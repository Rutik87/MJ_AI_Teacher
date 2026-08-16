import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db

@pytest.mark.asyncio
async def test_get_schedule():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/schedule?user_id=1")
    assert response.status_code == 200
    data = response.json()
    assert "target_exam" in data
    assert "slots" in data
    assert len(data["slots"]) >= 1

@pytest.mark.asyncio
async def test_save_schedule():
    await init_db()
    payload = {
        "user_id": 1,
        "target_exam": "MPSC राज्यसेवा पूर्व परीक्षा",
        "daily_study_hours": 8.0,
        "primary_subjects": ["इतिहास", "भूगोल"],
        "slots": [
            {
                "time_slot": "06:00 AM - 08:00 AM",
                "subject": "इतिहास",
                "topic": "१८५७ चा स्वातंत्र्यलढा",
                "activity": "वाचन"
            }
        ]
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/schedule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["schedule"]["daily_study_hours"] == 8.0

@pytest.mark.asyncio
async def test_analyze_schedule():
    await init_db()
    payload = {
        "user_id": 1,
        "target_exam": "MPSC राज्यसेवा पूर्व परीक्षा",
        "daily_study_hours": 6.0,
        "weak_subjects": ["अर्थशास्त्र"],
        "current_schedule": "दररोज ४ तास वाचन"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/schedule/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "analysis_markdown" in data
    assert len(data["analysis_markdown"]) > 20
