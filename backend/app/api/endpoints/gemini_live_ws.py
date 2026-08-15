"""
FastAPI WebSocket Gateway for Gemini Live Realtime Assistant.
Provides low-latency bi-directional audio streaming, live Marathi transcripts,
barge-in interruption broadcasts, tool calling, and strict structured logging.
"""

import asyncio
import json
import base64
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types

from app.config import settings
from app.services.ai.gemini_live_service import gemini_live_service
from app.utils.logger import logger

router = APIRouter(prefix="/mj", tags=["Gemini Live WebSocket"])

@router.websocket("/live-ws")
async def gemini_live_websocket(websocket: WebSocket):
    """
    WebSocket endpoint connecting Flutter client to Google Gemini Live API.
    """
    await websocket.accept()
    logger.info("[LIVE-WS] client connected")

    # Verify API Key availability
    client = gemini_live_service.get_client()
    api_key = settings.GEMINI_API_KEY or ""
    if not api_key:
        logger.warning("[LIVE-WS] GEMINI_API_KEY is not configured on server.")
    logger.info("[LIVE-WS] auth passed")

    config = gemini_live_service.get_live_config()
    
    # Try preferred live model, fallback to gemini-2.0-flash if preview model is unavailable
    models_to_try = [settings.GEMINI_LIVE_MODEL, "gemini-2.0-flash", "gemini-2.0-flash-exp"]
    # De-duplicate while preserving order
    models_to_try = list(dict.fromkeys(models_to_try))

    session = None
    active_model = None

    for model_candidate in models_to_try:
        try:
            logger.info(f"[LIVE-WS] Attempting live connection to model: {model_candidate}")
            # Try connecting with 8-second timeout
            connect_coro = client.aio.live.connect(model=model_candidate, config=config)
            session_ctx = await asyncio.wait_for(connect_coro.__aenter__(), timeout=8.0)
            session = session_ctx
            active_model = model_candidate
            logger.info(f"[LIVE-WS] Gemini connection established with model '{active_model}' and voice '{settings.GEMINI_LIVE_VOICE}'")
            break
        except Exception as conn_err:
            logger.warning(f"[LIVE-WS] Model '{model_candidate}' connection failed: {conn_err}")

    if not session:
        logger.error("[LIVE-WS] All Gemini Live model candidates failed to connect.")
        await websocket.send_json({
            "type": "error",
            "message": "Gemini Live सर्व्हरशी जोडता आले नाही. कृपया इंटरनेट किंवा API Key तपासा."
        })
        await websocket.close()
        logger.info("[LIVE-WS] session closed")
        return

    try:
        # Notify client that connection to Gemini Live is ready
        await websocket.send_json({
            "type": "ready",
            "model": active_model,
            "voice": settings.GEMINI_LIVE_VOICE,
            "message": "Gemini Live Realtime Assistant तयार आहे."
        })

        # Task 1: Forward client messages (audio chunks / text) to Gemini Live
        async def receive_from_client():
            try:
                while True:
                    msg = await websocket.receive()
                    if "text" in msg and msg["text"]:
                        data = json.loads(msg["text"])
                        msg_type = data.get("type", "text")

                        if msg_type == "text":
                            query = data.get("text", "")
                            if query.strip():
                                logger.info(f"[LIVE-WS] audio received text query length={len(query)}")
                                await session.send_client_content(
                                    turns=types.Content(
                                        role="user",
                                        parts=[types.Part.from_text(text=query)]
                                    ),
                                    end_of_turn=True
                                )
                                logger.info("[LIVE-WS] audio sent to Gemini")
                        elif msg_type == "audio_chunk":
                            # Base64 PCM audio chunk from microphone
                            raw_b64 = data.get("data", "")
                            if raw_b64:
                                pcm_bytes = base64.b64decode(raw_b64)
                                logger.debug(f"[LIVE-WS] audio received PCM bytes={len(pcm_bytes)}")
                                await session.send_realtime_input(
                                    audio=types.Blob(
                                        mime_type="audio/pcm;rate=16000",
                                        data=pcm_bytes
                                    )
                                )
                                logger.debug("[LIVE-WS] audio sent to Gemini")

                    elif "bytes" in msg and msg["bytes"]:
                        # Direct binary PCM bytes
                        logger.debug(f"[LIVE-WS] audio received binary PCM bytes={len(msg['bytes'])}")
                        await session.send_realtime_input(
                            audio=types.Blob(
                                mime_type="audio/pcm;rate=16000",
                                data=msg["bytes"]
                            )
                        )
                        logger.debug("[LIVE-WS] audio sent to Gemini")
            except WebSocketDisconnect:
                logger.info("[LIVE-WS] client disconnected")
            except Exception as e:
                logger.debug(f"[LIVE-WS] Error in receive_from_client: {e}")

        # Task 2: Stream responses from Gemini Live back to client
        async def send_to_client():
            try:
                async for response in session.receive():
                    server_content = response.server_content
                    tool_call = response.tool_call

                    # Handle interruption
                    if server_content and getattr(server_content, "interrupted", False):
                        logger.info("[LIVE-WS] interrupted")
                        await websocket.send_json({
                            "type": "interrupted",
                            "message": "Assistant interrupted by user speech."
                        })
                        continue

                    # Handle model turn output (audio & text parts)
                    if server_content and getattr(server_content, "model_turn", None):
                        for part in server_content.model_turn.parts:
                            # 1. Audio Part
                            if getattr(part, "inline_data", None) and part.inline_data.data:
                                logger.debug(f"[LIVE-WS] Gemini audio received bytes={len(part.inline_data.data)}")
                                audio_b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                                await websocket.send_json({
                                    "type": "audio",
                                    "data": audio_b64,
                                    "mime_type": part.inline_data.mime_type or "audio/pcm;rate=24000"
                                })
                                logger.debug("[LIVE-WS] audio forwarded to Flutter")

                            # 2. Text Part
                            if getattr(part, "text", None):
                                await websocket.send_json({
                                    "type": "transcript",
                                    "role": "assistant",
                                    "text": part.text
                                })

                    if server_content and getattr(server_content, "turn_complete", False):
                        await websocket.send_json({
                            "type": "turn_complete"
                        })

                    # Handle Tool Calls (RAG / Current Affairs)
                    if tool_call and getattr(tool_call, "function_calls", None):
                        for call in tool_call.function_calls:
                            call_id = call.id
                            func_name = call.name
                            func_args = call.args or {}

                            tool_result = await gemini_live_service.execute_tool_call(func_name, func_args)

                            await session.send_tool_response(
                                function_responses=[
                                    types.FunctionResponse(
                                        id=call_id,
                                        name=func_name,
                                        response={"result": tool_result}
                                    )
                                ]
                            )

            except Exception as e:
                logger.debug(f"[LIVE-WS] Error in send_to_client: {e}")

        # Run both loops concurrently
        await asyncio.gather(receive_from_client(), send_to_client())

    except WebSocketDisconnect:
        logger.info("[LIVE-WS] WebSocket disconnected.")
    except Exception as e:
        logger.error(f"[LIVE-WS] Session error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Gemini Live त्रुटी: {e}"
            })
        except Exception:
            pass
    finally:
        logger.info("[LIVE-WS] session closed")
        try:
            await session.__aexit__(None, None, None)
        except Exception:
            pass
