import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db

@pytest.mark.asyncio
async def test_api_health():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_list_subjects():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/subjects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 10
    names = [s["name_mr"] for s in data]
    assert "इतिहास" in names
    assert "राज्यशास्त्र" in names

@pytest.mark.asyncio
async def test_chat_message():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/chat/message", json={
            "message": "सत्यशोधक समाजाची स्थापना कोणी केली?",
            "mode": "general_chat"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["sender"] == "ai"
    assert len(data["message"]) > 10

@pytest.mark.asyncio
async def test_list_books():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/books")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_chat_sessions():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/chat/sessions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
