import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db

@pytest.mark.asyncio
async def test_current_affairs_categories_endpoint():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/current-affairs/categories")
        assert res.status_code == 200
        data = res.json()
        assert len(data["categories"]) == 12
        assert "महाराष्ट्र" in data["categories"]
        assert "अर्थव्यवस्था" in data["categories"]
        assert "विज्ञान व तंत्रज्ञान" in data["categories"]

@pytest.mark.asyncio
async def test_current_affairs_trust_status():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/current-affairs/trust-status")
        assert res.status_code == 200
        data = res.json()
        assert "last_updated_at" in data
        assert "last_successful_sync" in data
        assert "verified" in data["verification_status"]
        assert data["total_verified_records"] > 0

@pytest.mark.asyncio
async def test_current_affairs_date_filtering():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Today
        res_today = await client.get("/api/current-affairs/?date_filter=today")
        assert res_today.status_code == 200
        items_today = res_today.json()
        assert len(items_today) > 0

        # Last 7 days
        res_7 = await client.get("/api/current-affairs/?date_filter=last_7_days")
        assert res_7.status_code == 200
        items_7 = res_7.json()
        assert len(items_7) >= len(items_today)

@pytest.mark.asyncio
async def test_current_affairs_natural_search():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/current-affairs/search?q=महाराष्ट्रातील योजना")
        assert res.status_code == 200
        data = res.json()
        assert data["meta"]["total_results"] > 0
        assert any("लाडकी बहीण" in r["title_mr"] for r in data["results"])

@pytest.mark.asyncio
async def test_current_affairs_daily_quiz():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/current-affairs/quiz?limit=5")
        assert res.status_code == 200
        mcqs = res.json()
        assert len(mcqs) > 0
        assert "question_mr" in mcqs[0]
        assert "option_a" in mcqs[0]
        assert "correct_option" in mcqs[0]
        assert "explanation_mr" in mcqs[0]
