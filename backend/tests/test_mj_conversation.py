import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.mj_assistant_service import resolve_context_topic

@pytest.mark.asyncio
async def test_wake_word_and_greeting():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test standalone wake word
        res = await client.post("/api/mj/converse", json={"query": "Are MJ"})
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == "activation"
        assert data["action"] == "keep_listening"
        assert data["mode"] == "FRIEND"
        assert data["audio_url"] is not None

@pytest.mark.asyncio
async def test_interruption_stop():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/mj/converse", json={"query": "थांब"})
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == "interruption"
        assert data["action"] == "stop"
        assert "थांबले" in data["reply_text"]

@pytest.mark.asyncio
async def test_casual_friend_empathy():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/mj/converse", json={"query": "आज अभ्यासाचा मूड नाही"})
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == "casual_empathy"
        assert data["mode"] == "FRIEND"
        assert data["emotion"] == "empathetic"
        assert data["audio_url"] is not None

@pytest.mark.asyncio
async def test_study_planner_intent():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/mj/converse", json={"query": "आज काय अभ्यास करू?"})
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == "study_planner"
        assert data["mode"] == "STUDY"
        assert data["action"] == "navigate_plan"

@pytest.mark.asyncio
async def test_pronoun_context_resolution():
    history = [
        {"sender": "user", "text": "1857 चा उठाव समजावून सांग."},
        {"sender": "mj", "text": "1857 चा उठाव हा भारताचा पहिला स्वातंत्र्यलढा मानला जातो."}
    ]
    resolved, topic = resolve_context_topic("त्याची मुख्य कारणे कोणती?", history)
    assert topic is not None
    assert "संदर्भ" in resolved

@pytest.mark.asyncio
async def test_voice_profile_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/voice/profile")
        assert res.status_code == 200
        data = res.json()
        assert data["voice_profile_id"] == "mj_primary"
        assert data["name"] == "MJ"
        assert data["is_authorized"] is True
