import pytest
import io
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.notes.user_controlled_notes_service import user_controlled_notes_service

@pytest.mark.asyncio
async def test_browser_prototype_html_route():
    """Verifies that the interactive browser prototype UI is served at /prototype/notes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/prototype/notes")
        assert res.status_code == 200
        assert "MPSC AI • User-Controlled" in res.text
        assert "Live Notebook Preview" in res.text

@pytest.mark.asyncio
async def test_prototype_txt_upload_and_chapter_detection():
    """Verifies TXT upload and chapter parsing."""
    sample_text = """
प्रकरण १: १८५७ चा उठाव
२९ मार्च १८५७ रोजी मंगल पांडे यांनी बराकपूर छावणीत काडतुसांविरोधात बंड पुकारले.
लॉर्ड डलहौसीचे दत्तक वारसा नामंजूर धोरण या उठावाचे प्रमुख कारण होते.

प्रकरण २: १८५८ चा राणीचा जाहीरनामा
१ नोव्हेंबर १८५८ रोजी लॉर्ड कॅनिंगने अलाहाबाद दरबारात राणीचा जाहीरनामा वाचून दाखवला.
याने ईस्ट इंडिया कंपनीची सत्ता समाप्त होऊन ब्रिटिश पार्लमेंटची सत्ता सुरू झाली.
"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {
            "file": ("modern_india_history.txt", io.BytesIO(sample_text.encode("utf-8")), "text/plain")
        }
        res = await client.post("/prototype/notes/upload", files=files)
        assert res.status_code == 200
        data = res.json()
        assert "id" in data
        assert data["total_chapters"] >= 2
        assert len(data["chapters"]) >= 2
        assert "१८५७ चा उठाव" in data["chapters"][0]["title"]

@pytest.mark.asyncio
async def test_prototype_chatgpt_generation_and_pdf_download():
    """Verifies ChatGPT notes generation and multi-page notebook PDF creation."""
    sample_text = "१८५७ च्या उठावाची कारणे, २९ मार्च १८५७ रोजी मंगल पांडे यांचे बंड आणि लॉर्ड कॅनिंग यांची भूमिका."
    doc_result = await user_controlled_notes_service.process_upload(
        sample_text.encode("utf-8"),
        "test_history_doc.txt"
    )
    doc_id = doc_result["id"]

    mock_chatgpt_json = {
        "heading_mr": "१८५७ चा राष्ट्रीय उठाव",
        "subheading_mr": "MPSC विशेष हस्तलिखित अभ्यास नोट्स",
        "short_definition_mr": "१८५७ चा उठाव हा ब्रिटिश ईस्ट इंडिया कंपनीच्या अन्यायी धोरणांविरुद्धचा पहिला मोठा सशस्त्र स्वातंत्र्यलढा होता.",
        "important_concepts": [
            {"title_mr": "दत्तक वारसा नामंजूर धोरण", "explanation_mr": "लॉर्ड डलहौसीने भारतीय संस्थाने खालसा करण्यासाठी आणलेले धोरण."}
        ],
        "key_points": [
            "२९ मार्च १८५७: मंगल पांडे यांचे बराकपूर छावणीत बंड.",
            "१० मे १८५७: मीरत छावणीतून सैनिकांची दिल्लीकडे कूच."
        ],
        "important_dates": [
            "२९ मार्च १८५७ - बराकपूर छावणीतील उठाव",
            "१० मे १८५७ - मीरत सैनिकांचे बंड"
        ],
        "important_personalities": [
            "मंगल पांडे - आद्य क्रांतिकारक",
            "झाशीची राणी लक्ष्मीबाई - झाशीचे नेतृत्व"
        ],
        "memory_tricks": [
            "💡 ट्रिक: 'ब-मी-दि' (बराकपूर -> मीरत -> दिल्ली)"
        ],
        "table": {
            "title_mr": "उठावाचे प्रमुख केंद्र व नेते",
            "headers": ["केंद्र", "नेतृत्व", "दडपणारा अधिकारी"],
            "rows": [
                ["झाशी", "राणी लक्ष्मीबाई", "ह्यू रोज"],
                ["कानपूर", "नानासाहेब पेशवे", "कॉलिन कॅम्पबेल"]
            ]
        },
        "exam_points": [
            "🎯 MPSC: उठावाची सुरुवात बराकपूरमध्ये २९ मार्च रोजी झाली."
        ],
        "quick_revision_box": [
            "⚡ कारणे: राजकीय, लष्करी (एनफिल्ड काडतुसे), सामाजिक व धार्मिक."
        ],
        "common_mistakes": [
            "⚠️ १० मे आणि २९ मार्चच्या घटनांची गल्लत करू नका."
        ]
    }

    with patch("app.services.ai.llm_provider.LLMProvider._execute_with_provider", return_value=(json.dumps(mock_chatgpt_json), "ChatGPT OpenAI (gpt-4o-mini)")):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            gen_res = await client.post(
                "/prototype/notes/generate",
                json={
                    "doc_id": doc_id,
                    "chapter_id": 1,
                    "custom_instruction": "या अध्यायाचे MPSC साठी पूर्ण handwritten notes बनव."
                }
            )
            assert gen_res.status_code == 200
            gen_data = gen_res.json()
            assert gen_data["doc_id"] == doc_id
            assert "१८५७" in gen_data["structured_note"]["heading_mr"]
            assert gen_data["page_count"] >= 1

            # Test PDF download endpoint
            pdf_res = await client.get(f"/prototype/notes/{doc_id}/pdf")
            assert pdf_res.status_code == 200
            assert pdf_res.headers["content-type"] == "application/pdf"
            assert len(pdf_res.content) > 1000
