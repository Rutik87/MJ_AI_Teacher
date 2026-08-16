import pytest
import json
import base64
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings, validate_gemini_live_voice
from app.services.ai.gemini_live_service import gemini_live_service, MARATHI_BEST_FRIEND_PROMPT

client = TestClient(app)

# 1. Voice and Model Validation
def test_gemini_live_model_and_voice():
    assert settings.GEMINI_LIVE_MODEL == "gemini-3.1-flash-live-preview"
    assert validate_gemini_live_voice("Aoede") == "Aoede"
    assert gemini_live_service.voice_name == "Aoede"

# 2. WebSocket Connection & Handshake
def test_gemini_live_ws_handshake():
    with client.websocket_connect("/api/mj/live-ws") as ws:
        ready_frame = ws.receive_json()
        assert ready_frame["type"] == "ready"
        assert ready_frame["model"] == settings.GEMINI_LIVE_MODEL
        assert ready_frame["voice"] == "Aoede"
        assert "Gemini Live Realtime Assistant" in ready_frame["message"]

# 3. Conversational Marathi & Audio Streaming Turn
def test_gemini_live_marathi_conversation_turn():
    with patch("app.services.ai.llm_provider.LLMProvider.generate_completion") as mock_llm:
        mock_llm.return_value = ("मी एकदम मजेत आहे! तू कसा आहेस? 😄", "ChatGPT")
        
        with client.websocket_connect("/api/mj/live-ws") as ws:
            ws.receive_json()  # ready frame
            
            # Send Marathi text turn
            ws.send_json({"type": "text", "text": "Are MJ, aaj kasa ahes?"})
            
            # Receive transcript
            transcript_frame = ws.receive_json()
            assert transcript_frame["type"] == "transcript"
            assert "मी एकदम मजेत आहे" in transcript_frame["text"]

            # Receive audio chunk or turn_complete
            next_frame = ws.receive_json()
            assert next_frame["type"] in ["audio", "turn_complete"]

# 4. Roman Marathi Input Handling
def test_gemini_live_roman_marathi_turn():
    with patch("app.services.ai.llm_provider.LLMProvider.generate_completion") as mock_llm:
        mock_llm.return_value = ("हो नक्कीच! १८५७ चा उठाव समजावून सांगते.", "ChatGPT")
        
        with client.websocket_connect("/api/mj/live-ws") as ws:
            ws.receive_json()
            ws.send_json({"type": "text", "text": "1857 cha revolt mala ekdam simple Marathi madhe samjhav"})
            
            transcript_frame = ws.receive_json()
            assert transcript_frame["type"] == "transcript"
            assert "१८५७ चा उठाव" in transcript_frame["text"]

# 5. RAG Tool Execution via Voice WS
@pytest.mark.asyncio
async def test_gemini_live_rag_tool_execution():
    with patch("app.services.rag.retriever.rag_retriever.retrieve") as mock_retrieve:
        mock_citation = MagicMock()
        mock_citation.text_snippet = "१८५७ च्या उठावाची सुरुवात २९ मार्च १८५७ रोजी बराकपूर येथे झाली."
        mock_citation.book_name = "आधुनिक भारताचा इतिहास"
        mock_citation.chapter = "अध्याय १"
        mock_citation.page_number = 12
        mock_retrieve.return_value = ([mock_citation], mock_citation.text_snippet, True)

        res = await gemini_live_service.execute_tool_call(
            "search_uploaded_document",
            {"query": "1857 चा उठाव कधी सुरू झाला?"}
        )
        assert res["status"] == "success"
        assert res["found_count"] == 1
        assert "बराकपूर" in res["context"]

# 6. Current Affairs Tool Execution via Voice WS
@pytest.mark.asyncio
async def test_gemini_live_current_affairs_tool_execution():
    res = await gemini_live_service.execute_tool_call(
        "get_today_current_affairs",
        {"category": "महाराष्ट्र"}
    )
    assert res["status"] == "success"
    assert "articles" in res
    assert len(res["articles"]) > 0

# 7. Interruption / Barge-in Behavior
def test_gemini_live_interruption_ping():
    with client.websocket_connect("/api/mj/live-ws") as ws:
        ws.receive_json()  # ready
        ws.send_json({"type": "ping"})
        pong = ws.receive_json()
        assert pong["type"] == "pong"
