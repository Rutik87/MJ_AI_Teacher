import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db

@pytest.mark.asyncio
async def test_voice_lab_benchmark_sentences():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/voice-lab/benchmark-sentences")
        assert res.status_code == 200
        data = res.json()
        assert len(data["sentences"]) == 4
        assert "अरे, काळजी करू नकोस" in data["sentences"][0]["text"]
        assert "1857" in data["sentences"][1]["text"]

@pytest.mark.asyncio
async def test_voice_lab_synthesize_all_models():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "text": "अरे, काळजी करू नकोस. चला एकेक मुद्दा समजून घेऊया.",
            "models": ["indicf5", "snortts", "chatterbox"],
            "emotion": "friendly",
            "speed": 1.0
        }
        res = await client.post("/api/voice-lab/synthesize", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "indicf5" in data["results"]
        assert "snortts" in data["results"]
        assert "chatterbox" in data["results"]
        assert data["results"]["indicf5"]["similarity_score"] >= 0.90
        assert data["results"]["indicf5"]["audio_url"].endswith(".wav")

@pytest.mark.asyncio
async def test_voice_lab_benchmark_all_endpoint():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/voice-lab/benchmark-all")
        assert res.status_code == 200
        data = res.json()
        assert len(data["benchmark_matrix"]) == 4
        assert data["recommendation"]["selected_model"] == "IndicF5"

@pytest.mark.asyncio
async def test_voice_lab_html_page_serving():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/voice-lab")
        assert res.status_code == 200
        assert "Marathi Primary Voice Cloning Lab" in res.text
