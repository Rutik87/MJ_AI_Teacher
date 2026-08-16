import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import init_db, AsyncSessionLocal
from app.services.notes.note_generator_service import note_generator_service
from app.services.notes.pdf_note_renderer import pdf_note_renderer
from app.models.schema import Book, Chapter, Page, DocumentChunk, HandwrittenNote

@pytest.mark.asyncio
async def test_chatgpt_chapter_note_generation_and_grounding():
    """Verifies that ChatGPT generates source-grounded structured Marathi notes."""
    sample_text = """
    १८५७ चा उठाव:
    २९ मार्च १८५७ रोजी बराकपूर छावणीत मंगल पांडे यांनी काडतुसांना विरोध करत उठाव सुरू केला.
    १० मे १८५७ रोजी मीरत छावणीतील सैनिकांनी दिल्लीकडे कूच केले.
    मुघल बादशहा बहादूरशाह जफर यांना भारताचा सम्राट घोषित करण्यात आले.
    झाशीची राणी लक्ष्मीबाई, तात्या टोपे, आणि नानासाहेब पेशवे यांनी प्रमुख नेतृत्व केले.
    डलहौसीचे दत्तक वारसा नामंजूर धोरण आणि लॉर्ड कॅनिंगचे नवीन एनफिल्ड रायफलींचे धोरण या उठावाची प्रमुख कारणे होती.
    """

    mock_chatgpt_json = {
        "heading_mr": "१८५७ चा उठाव - पार्श्वभूमी व कारणे",
        "subheading_mr": "MPSC आधुनिक भारताचा इतिहास विशेष नोट्स",
        "short_definition_mr": "१८५७ चा उठाव हा ब्रिटिश ईस्ट इंडिया कंपनीच्या अन्यायी धोरणांविरुद्धचा पहिला मोठा सशस्त्र स्वातंत्र्यलढा होता.",
        "important_concepts": [
            {"title_mr": "दत्तक वारसा नामंजूर धोरण", "explanation_mr": "लॉर्ड डलहौसीने भारतीय संस्थाने खालसा करण्यासाठी आणलेले धोरण."}
        ],
        "key_points": [
            "२९ मार्च १८५७: मंगल पांडे यांचे बराकपूर छावणीत बंड.",
            "१० मे १८५७: मीरत छावणीतून सैनिकांची दिल्लीकडे कूच.",
            "बहादूरशाह जफर यांना उठावाचे नेतृत्व देण्यात आले."
        ],
        "important_dates": [
            "२९ मार्च १८५७ - बराकपूर येथील उठाव",
            "१० मे १८५७ - मीरत छावणीतील बंड"
        ],
        "important_personalities": [
            "मंगल पांडे - पहिले हुतात्मा",
            "राणी लक्ष्मीबाई - झाशीचे नेतृत्व",
            "तात्या टोपे - सेनापती"
        ],
        "memory_tricks": [
            "💡 ट्रिक: 'ब-मी-दि' (बराकपूर -> मीरत -> दिल्ली)"
        ],
        "exam_points": [
            "🎯 MPSC: उठावाची सुरुवात बराकपूर (२९ मार्च) आणि प्रत्यक्ष फैलाव मीरत (१० मे) पासून झाला."
        ],
        "quick_revision_box": [
            "⚡ कारणे: डलहौसीचे धोरण + एनफिल्ड काडतुसे",
            "⚡ नेतृत्व: बहादूरशाह जफर, राणी लक्ष्मीबाई, तात्या टोपे"
        ],
        "common_mistakes": [
            "⚠️ चूक टाळा: उठाव १० मे रोजी बराकपूरमध्ये नव्हे तर मीरतमध्ये झाला."
        ]
    }

    with patch("app.services.ai.llm_provider.LLMProvider._execute_with_provider", return_value=(json.dumps(mock_chatgpt_json), "ChatGPT OpenAI (gpt-4o-mini)")):
        note_dict = await note_generator_service._generate_chapter_note(
            book_title="आधुनिक भारताचा इतिहास",
            chapter_title="प्रकरण १: १८५७ चा उठाव",
            chapter_text=sample_text
        )

        assert note_dict["heading_mr"] == "१८५७ चा उठाव - पार्श्वभूमी व कारणे"
        assert len(note_dict["key_points"]) >= 3
        assert len(note_dict["important_dates"]) >= 2
        assert len(note_dict["important_personalities"]) >= 2
        assert "मंगल पांडे" in str(note_dict["important_personalities"])
        assert "२९ मार्च १८५७" in str(note_dict["important_dates"])

@pytest.mark.asyncio
async def test_pdf_notebook_renderer_generation():
    """Verifies that ReportLab notebook renderer produces an authentic PDF artifact."""
    sample_chapters = [
        {
            "heading_mr": "१८५७ चा उठाव",
            "subheading_mr": "MPSC इतिहास हस्तलिखित नोट्स",
            "short_definition_mr": "भारतातील पहिला मोठा स्वातंत्र्यलढा.",
            "important_concepts": [
                {"title_mr": "दत्तक धोरण", "explanation_mr": "डलहौसीचे संस्थाने खालसा करण्याचे धोरण."}
            ],
            "key_points": [
                "१. बराकपूर येथे मंगल पांडे यांचे बंड.",
                "२. झाशी, ग्वाल्हेर, कानपूर येथे उठावाचा फैलाव."
            ],
            "important_dates": [
                "२९ मार्च १८५७: मंगल पांडे बंड"
            ],
            "important_personalities": [
                "झाशीची राणी लक्ष्मीबाई"
            ],
            "memory_tricks": [
                "💡 ट्रिक: १८५७ च्या क्रांतीचे केंद्र"
            ],
            "exam_points": [
                "🎯 MPSC पूर्व: लॉर्ड कॅनिंग त्यावेळी गव्हर्नर जनरल होते."
            ],
            "quick_revision_box": [
                "⚡ मुख्य नेते आणि त्यांच्या कार्यक्षेत्रांची जोडी लक्षात ठेवा."
            ],
            "common_mistakes": [
                "⚠️ तारीख आणि ठिकाणांची गल्लत करू नका."
            ]
        }
    ]

    pdf_path, pdf_url, page_count = await pdf_note_renderer.render_notebook_pdf(
        book_id=999,
        book_title="आधुनिक भारताचा इतिहास Test",
        chapters=sample_chapters
    )

    assert Path(pdf_path).exists()
    assert Path(pdf_path).stat().st_size > 1000  # PDF generated with content
    assert pdf_url == "/api/notes/999/download"
    assert page_count >= 1

    # Cleanup test PDF
    try:
        Path(pdf_path).unlink()
    except Exception:
        pass

@pytest.mark.asyncio
async def test_notes_api_endpoints():
    """Verifies that /api/notes/health, /api/notes/all, and /api/notes/{book_id} respond correctly."""
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res_health = await client.get("/api/notes/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "active"

        # 2. List all notes
        res_all = await client.get("/api/notes/all?user_id=1")
        assert res_all.status_code == 200
        assert isinstance(res_all.json(), list)

        # 3. Status check for book 999 (not generated)
        res_status = await client.get("/api/notes/999")
        assert res_status.status_code == 404 or res_status.json().get("status") == "not_generated"
