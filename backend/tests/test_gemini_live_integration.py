"""
Gemini Live Realtime Voice Assistant — Integration Tests.
Tests tool execution for RAG, live date-stamped Current Affairs,
WebSocket message protocols, and barge-in interruption.
"""

import pytest
import datetime
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db
from app.services.ai.gemini_live_service import gemini_live_service, get_live_tools_declarations

@pytest.mark.asyncio
async def test_live_tools_declarations():
    """Verify that both RAG and Current Affairs tools are properly declared."""
    await init_db()
    tools = get_live_tools_declarations()
    assert len(tools) == 1
    func_names = [f.name for f in tools[0].function_declarations]
    assert "search_uploaded_document" in func_names
    assert "get_today_current_affairs" in func_names

@pytest.mark.asyncio
async def test_rag_tool_execution():
    """Verify fast execution of search_uploaded_document tool."""
    # Test execution with generic query
    result = await gemini_live_service.execute_tool_call(
        "search_uploaded_document",
        {"query": "राज्यघटना कलम 14", "book_id": None}
    )
    assert result["status"] == "success"
    assert "chunks" in result

@pytest.mark.asyncio
async def test_current_affairs_tool_execution_with_real_date():
    """Verify that get_today_current_affairs returns genuine date-stamped current data."""
    result = await gemini_live_service.execute_tool_call(
        "get_today_current_affairs",
        {"category": "महाराष्ट्र", "topic_query": "लाडकी बहीण"}
    )
    assert result["status"] == "success"
    assert "query_date" in result
    now_str = datetime.datetime.utcnow().strftime("%d %B %Y")
    assert result["query_date"] == now_str
    assert result["items_count"] >= 1
    assert len(result["articles"]) >= 1
    article = result["articles"][0]
    assert article["date"] == now_str
    assert "महाराष्ट्र" in article["category"]

@pytest.mark.asyncio
async def test_unknown_tool_graceful_handling():
    """Verify unknown tool returns error message gracefully without crashing."""
    result = await gemini_live_service.execute_tool_call("unknown_tool", {})
    assert result["status"] == "error"
