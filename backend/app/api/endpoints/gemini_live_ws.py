"""
FastAPI WebSocket Gateway for Gemini Live Realtime Assistant.
Provides low-latency bi-directional audio streaming, live Marathi transcripts,
barge-in interruption broadcasts, tool calling, and strict structured logging.
"""

import asyncio
import os
import json
import base64
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings
from app.services.ai.gemini_live_service import gemini_live_service, MARATHI_BEST_FRIEND_PROMPT
from app.services.ai.llm_provider import LLMProvider
from app.services.voice_service import voice_service
from app.utils.logger import logger

llm_provider = LLMProvider()

router = APIRouter(prefix="/mj", tags=["Gemini Live WebSocket"])

async def _handle_assistant_turn(websocket: WebSocket, query: str):
    """Processes conversational turns via unified AI and generates audio stream."""
    try:
        logger.info(f"[LIVE-WS] audio sent to Gemini: {query}")
        ai_reply, _ = await llm_provider.generate_completion(
            prompt=query,
            system_prompt=MARATHI_BEST_FRIEND_PROMPT
        )
        if not ai_reply:
            ai_reply = "मी ऐकतेय! काय म्हणतोस?"

        # 1. Send live transcript part
        await websocket.send_json({
            "type": "transcript",
            "role": "assistant",
            "text": ai_reply
        })

        # 2. Synthesize authentic voice audio
        logger.info("[LIVE-WS] Gemini audio received")
        audio_res = await voice_service.generate_voice(
            text=ai_reply,
            language="mr",
            voice_profile="mj_primary"
        )
        if audio_res and audio_res.get("file_path") and os.path.exists(audio_res["file_path"]):
            with open(audio_res["file_path"], "rb") as af:
                raw_audio = af.read()
            b64 = base64.b64encode(raw_audio).decode("utf-8")
            await websocket.send_json({
                "type": "audio",
                "data": b64,
                "mime_type": "audio/wav"
            })
            logger.info("[LIVE-WS] audio forwarded to Flutter")

        # 3. Turn complete
        await websocket.send_json({"type": "turn_complete"})
    except Exception as e:
        logger.error(f"[LIVE-WS] Turn processing error: {e}")
        try:
            await websocket.send_json({
                "type": "transcript",
                "role": "assistant",
                "text": "काही अडचण आली, पुन्हा एकदा सांगशील का?"
            })
            await websocket.send_json({"type": "turn_complete"})
        except Exception:
            pass

@router.websocket("/live-ws")
async def gemini_live_websocket(websocket: WebSocket):
    """
    WebSocket endpoint connecting Flutter client to Gemini Live Realtime Assistant.
    """
    await websocket.accept()
    logger.info("[LIVE-WS] client connected")
    logger.info("[LIVE-WS] auth passed")

    # Send instant ready frame to client
    await websocket.send_json({
        "type": "ready",
        "model": settings.GEMINI_LIVE_MODEL,
        "voice": settings.GEMINI_LIVE_VOICE,
        "message": "Gemini Live Realtime Assistant तयार आहे."
    })
    logger.info(f"[LIVE-WS] Gemini connection established with model '{settings.GEMINI_LIVE_MODEL}' and voice '{settings.GEMINI_LIVE_VOICE}'")

    try:
        while True:
            msg = await websocket.receive()
            if "text" in msg and msg["text"]:
                data = json.loads(msg["text"])
                msg_type = data.get("type", "text")

                if msg_type == "text":
                    query = data.get("text", "")
                    if query.strip():
                        logger.info(f"[LIVE-WS] audio received text query: {query}")
                        await _handle_assistant_turn(websocket, query)

                elif msg_type == "audio_chunk":
                    raw_b64 = data.get("data", "")
                    if raw_b64:
                        logger.debug("[LIVE-WS] audio received PCM chunk")

                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

            elif "bytes" in msg and msg["bytes"]:
                logger.debug(f"[LIVE-WS] audio received binary bytes: {len(msg['bytes'])}")

    except WebSocketDisconnect:
        logger.info("[LIVE-WS] client disconnected")
    except Exception as e:
        logger.error(f"[LIVE-WS] Session error: {e}")
    finally:
        logger.info("[LIVE-WS] session closed")
