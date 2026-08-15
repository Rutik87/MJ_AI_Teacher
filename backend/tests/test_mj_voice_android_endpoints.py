import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_mj_converse_and_audio_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Test /api/mj/converse
        res = await ac.post("/api/mj/converse", json={"query": "Are MJ, aaj kasa ahes?"})
        assert res.status_code == 200, f"MJ Converse failed: {res.text}"
        data = res.json()
        assert "reply_text" in data
        assert "audio_url" in data
        assert data["audio_url"] is not None
        assert "voice_profile_id" not in data or data.get("voice_profile_id") == "mj_primary"
        
        audio_url = data["audio_url"]
        print(f"Generated Audio URL: {audio_url}")
        
        # 2. Test Audio Endpoint download
        audio_res = await ac.get(audio_url)
        assert audio_res.status_code == 200, f"Audio fetch failed: {audio_res.status_code}"
        assert audio_res.headers.get("content-type") == "audio/mpeg"
        assert len(audio_res.content) > 1000, "Audio file content is too small"

@pytest.mark.asyncio
async def test_chat_message_generates_mj_audio():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/chat/message", json={"message": "1857 cha uthav mala samjhav", "mode": "teacher_mode"})
        assert res.status_code == 200, f"Chat message failed: {res.text}"
        data = res.json()
        assert "message" in data
        assert data.get("has_audio") is True
        assert data.get("audio_url") is not None
        assert data["audio_url"].startswith("/api/voice/audio/")

        # Test audio download
        audio_res = await ac.get(data["audio_url"])
        assert audio_res.status_code == 200
        assert audio_res.headers.get("content-type") == "audio/mpeg"
        assert len(audio_res.content) > 1000
