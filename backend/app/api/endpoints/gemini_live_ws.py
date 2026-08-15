"""
FastAPI WebSocket Gateway for Gemini Live Realtime Assistant.
Provides low-latency bi-directional audio streaming, live Marathi transcripts,
barge-in interruption broadcasts, and tool calling for RAG & Current Affairs.
"""

import asyncio
import json
import base64
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
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
    logger.info("[GeminiLiveWS] Client connected to live WebSocket.")

    client = gemini_live_service.get_client()
    config = gemini_live_service.get_live_config()
    model = settings.GEMINI_LIVE_MODEL

    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            # Notify client that connection to Gemini Live is ready
            await websocket.send_json({
                "type": "ready",
                "model": model,
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
                                    await session.send_client_content(
                                        turns=types.Content(
                                            role="user",
                                            parts=[types.Part.from_text(text=query)]
                                        ),
                                        end_of_turn=True
                                    )
                            elif msg_type == "audio_chunk":
                                # Base64 PCM audio chunk from microphone
                                raw_b64 = data.get("data", "")
                                if raw_b64:
                                    pcm_bytes = base64.b64decode(raw_b64)
                                    await session.send_realtime_input(
                                        audio=types.Blob(
                                            mime_type="audio/pcm;rate=16000",
                                            data=pcm_bytes
                                        )
                                    )

                        elif "bytes" in msg and msg["bytes"]:
                            # Direct binary PCM bytes
                            await session.send_realtime_input(
                                audio=types.Blob(
                                    mime_type="audio/pcm;rate=16000",
                                    data=msg["bytes"]
                                )
                            )
                except WebSocketDisconnect:
                    logger.info("[GeminiLiveWS] Client disconnected normally.")
                except Exception as e:
                    logger.debug(f"[GeminiLiveWS] Error in receive_from_client: {e}")

            # Task 2: Stream responses from Gemini Live back to client
            async def send_to_client():
                try:
                    async for response in session.receive():
                        server_content = response.server_content
                        tool_call = response.tool_call

                        # Handle interruption
                        if server_content and getattr(server_content, "interrupted", False):
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
                                    audio_b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                                    await websocket.send_json({
                                        "type": "audio",
                                        "data": audio_b64,
                                        "mime_type": part.inline_data.mime_type or "audio/pcm;rate=24000"
                                    })
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

                                # Execute tool
                                tool_result = await gemini_live_service.execute_tool_call(func_name, func_args)

                                # Send tool response back to Gemini
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
                    logger.debug(f"[GeminiLiveWS] Error in send_to_client: {e}")

            # Run both loops concurrently until disconnect
            await asyncio.gather(receive_from_client(), send_to_client())

    except WebSocketDisconnect:
        logger.info("[GeminiLiveWS] WebSocket closed.")
    except Exception as e:
        logger.error(f"[GeminiLiveWS] Session error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Gemini Live त्रुटी: {e}"
            })
            await websocket.close()
        except Exception:
            pass
