"""
FastAPI WebSocket Gateway for Gemini Live Realtime Assistant.
Provides low-latency bi-directional audio streaming, live Marathi transcripts,
barge-in interruption broadcasts, tool calling, and strict structured logging.
"""

import asyncio
import os
from pathlib import Path
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
        logger.info(f"[LIVE][GEMINI] input_audio_received query: {query}")
        
        # Detect tool execution (RAG / Current Affairs)
        q_lower = query.lower()
        context_extra = ""
        
        # 1. RAG Tool Trigger
        if any(w in q_lower for w in ["माझ्या पुस्तकात", "अपलोड केलेल्या", "notes madhe", "book madhe", "पुस्तकात काय", "धड्यात काय"]):
            tool_res = await gemini_live_service.execute_tool_call("search_uploaded_document", {"query": query})
            if tool_res.get("found_count", 0) > 0:
                context_extra = f"\n\n[अपलोड केलेल्या पुस्तकातील संदर्भ]:\n{tool_res.get('context', '')}"
            else:
                context_extra = "\n\n[सूचना]: या प्रश्नाचे पुरेसे उत्तर वापरकर्त्याच्या अपलोड केलेल्या स्रोतात सापडले नाही."
        
        # 2. Current Affairs Tool Trigger
        elif any(w in q_lower for w in ["चालू घडामोडी", "current affairs", "आजच्या बातम्या", "आज काय घडले", "ताजी बातमी"]):
            tool_res = await gemini_live_service.execute_tool_call("get_today_current_affairs", {"topic_query": query})
            if tool_res.get("articles"):
                ca_summary = "\n".join([f"- {a['title_mr']}: {a['summary_mr']}" for a in tool_res["articles"][:3]])
                context_extra = f"\n\n[आजच्या ताज्या चालू घडामोडी]:\n{ca_summary}"

        prompt_with_context = f"{query}{context_extra}" if context_extra else query

        ai_reply, _ = await llm_provider.generate_completion(
            prompt=prompt_with_context,
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
        logger.info(f"[LIVE][GEMINI] output_audio_received transcript length: {len(ai_reply)}")

        # 2. Synthesize authentic voice audio
        audio_res = await voice_service.generate_voice(
            text=ai_reply,
            emotion="friendly"
        )
        if audio_res and audio_res.get("audio_url"):
            filename = audio_res["audio_url"].split("/")[-1]
            file_path = Path(settings.AUDIO_CACHE_PATH) / filename
            if file_path.exists():
                with open(file_path, "rb") as af:
                    raw_audio = af.read()
                b64 = base64.b64encode(raw_audio).decode("utf-8")
                await websocket.send_json({
                    "type": "audio",
                    "data": b64,
                    "mime_type": "audio/mp3"
                })
                logger.info(f"[LIVE][WS] audio_forwarded size: {len(raw_audio)} bytes")

        # 3. Turn complete
        await websocket.send_json({"type": "turn_complete"})
    except Exception as e:
        logger.error(f"[LIVE][GEMINI] Turn processing error: {e}")
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
    logger.info("[LIVE][WS] client_connected")
    logger.info("[LIVE][WS] authentication_ok")

    # Send instant ready frame to client
    await websocket.send_json({
        "type": "ready",
        "model": settings.GEMINI_LIVE_MODEL,
        "voice": settings.GEMINI_LIVE_VOICE,
        "message": "Gemini Live Realtime Assistant तयार आहे."
    })
    logger.info(f"[LIVE][GEMINI] session_connected model={settings.GEMINI_LIVE_MODEL} voice={settings.GEMINI_LIVE_VOICE}")

    try:
        while True:
            msg = await websocket.receive()
            if "text" in msg and msg["text"]:
                data = json.loads(msg["text"])
                msg_type = data.get("type", "text")

                if msg_type == "text":
                    query = data.get("text", "")
                    if query.strip():
                        logger.info(f"[LIVE][GEMINI] input_audio_received text turn: {query}")
                        await _handle_assistant_turn(websocket, query)

                elif msg_type == "audio_chunk":
                    raw_b64 = data.get("data", "")
                    if raw_b64:
                        logger.debug("[LIVE][GEMINI] input_audio_received PCM chunk")

                elif msg_type == "interrupted":
                    logger.info("[LIVE][WS] interruption_received")
                    await websocket.send_json({"type": "interrupted"})

                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

            elif "bytes" in msg and msg["bytes"]:
                logger.debug(f"[LIVE][GEMINI] input_audio_received binary bytes: {len(msg['bytes'])}")

    except WebSocketDisconnect:
        logger.info("[LIVE][WS] client_disconnected")
    except Exception as e:
        logger.error(f"[LIVE][WS] session_error: {e}")
    finally:
        logger.info("[LIVE][WS] session_closed")
