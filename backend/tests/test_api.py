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
async def test_generate_mcqs():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/tests/generate-mcqs", json={
            "subject_name": "इतिहास",
            "count": 3,
            "difficulty": "medium"
        })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert "option_a" in data[0]
    assert "correct_option" in data[0]

@pytest.mark.asyncio
async def test_revision_summary():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/revision/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_items" in data
    assert "due_today_count" in data
