import io
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.notes.user_controlled_notes_service import user_controlled_notes_service

SAMPLE_HISTORY_DOC = """
प्रकरण १: १८५७ चा राष्ट्रीय उठाव
२९ मार्च १८५७ रोजी मंगल पांडे यांनी बराकपूर छावणीत काडतुसांविरोधात बंड पुकारले.
लॉर्ड डलहौसीचे दत्तक वारसा नामंजूर धोरण या उठावाचे प्रमुख राजकीय कारण होते.
१० मे १८५७ रोजी मीरत छावणीतील सैनिकांनी दिल्लीकडे कूच केले.

प्रकरण २: १८५८ चा राणीचा जाहीरनामा
१ नोव्हेंबर १८५८ रोजी लॉर्ड कॅनिंगने अलाहाबाद दरबारात राणीचा जाहीरनामा वाचून दाखवला.
याने ईस्ट इंडिया कंपनीची सत्ता संपुष्टात आली व ब्रिटिश क्राऊनचे थेट शासन सुरू झाले.
"""

SAMPLE_POLITY_DOC = """
प्रकरण १: भारतीय राज्यघटनेची निर्मिती
९ डिसेंबर १९४६ रोजी घटना समितीची पहिली बैठक झाली आणि डॉ. सच्चिदानंद सिन्हा हंगामी अध्यक्ष बनले.
११ डिसेंबर १९४६ रोजी डॉ. राजेंद्र प्रसाद यांची कायमस्वरूपी अध्यक्ष म्हणून निवड झाली.
२९ ऑगस्ट १९४७ रोजी डॉ. बाबासाहेब आंबेडकर यांच्या अध्यक्षतेखाली मसुदा समिती (Drafting Committee) स्थापन झाली.
२६ नोव्हेंबर १९४९ रोजी राज्यघटना स्वीकृत करण्यात आली आणि २६ जानेवारी १९५० रोजी ती अमलात आली.
"""

SAMPLE_GEOGRAPHY_DOC = """
प्रकरण १: महाराष्ट्राची प्राकृतिक रचना
महाराष्ट्राचे तीन प्रमुख प्राकृतिक विभाग पडतात: १. कोकण किनारपट्टी, २. सह्याद्री पर्वतरांग (पश्चिम घाट), आणि ३. महाराष्ट्र पठार (दख्खनचे पठार).
कळसुबाई (१६४६ मी) हे महाराष्ट्रातील सर्वोच्च शिखर असून ते अहमदनगर जिल्ह्यात आहे.
सह्याद्री पर्वतामुळे महाराष्ट्रात पर्जन्यछायेचा प्रदेश निर्माण होतो.
"""

@pytest.mark.asyncio
async def test_subject_selection_history_and_custom_instruction():
    """Verifies History subject processing with explicit user custom instruction."""
    doc_res = await user_controlled_notes_service.process_upload(
        SAMPLE_HISTORY_DOC.encode("utf-8"),
        "modern_india.txt"
    )
    doc_id = doc_res["id"]

    mock_chatgpt_json = {
        "heading_mr": "१८५७ चा राष्ट्रीय उठाव",
        "subheading_mr": "इतिहास (History) • Handwritten Notes",
        "short_definition_mr": "१८५७ चा लढा हा ब्रिटिश सत्तेविरुद्धचा पहिला सशस्त्र उठाव होता.",
        "key_points": ["२९ मार्च १८५७: मंगल पांडे यांचे बंड.", "१० मे १८५७: मीरत सैनिकांचे बंड."],
        "important_dates": ["२९ मार्च १८५७ - बराकपूर", "१० मे १८५७ - मीरत"],
        "important_personalities": ["मंगल पांडे - आद्य क्रांतिकारक"],
        "memory_tricks": ["💡 ब-मी-दि (बराकपूर -> मीरत -> दिल्ली)"],
        "exam_points": ["🎯 MPSC Prelims: डलहौसीचे दत्तक वारसा धोरण"],
        "quick_revision_box": ["⚡ २९ मार्च आणि १० मे घटनांचा क्रम"]
    }

    with patch("app.services.ai.llm_provider.LLMProvider._execute_with_provider", return_value=(json.dumps(mock_chatgpt_json), "ChatGPT")):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/prototype/notes/generate",
                json={
                    "doc_id": doc_id,
                    "subject": "इतिहास (History)",
                    "scope": "chapter",
                    "chapter_id": 1,
                    "exam_target": "mpsc_prelims",
                    "output_type": "handwritten_notes",
                    "custom_instruction": "फक्त १८५७ च्या उठावाच्या महत्त्वाच्या तारखा आणि कारणे स्पष्ट कर."
                }
            )
            assert res.status_code == 200
            data = res.json()
            assert data["subject"] == "इतिहास (History)"
            assert data["total_processed_chapters"] == 1
            assert "१८५७" in data["structured_note"]["heading_mr"]

@pytest.mark.asyncio
async def test_subject_selection_polity_prelims_target():
    """Verifies Polity subject processing with MPSC Prelims emphasis."""
    doc_res = await user_controlled_notes_service.process_upload(
        SAMPLE_POLITY_DOC.encode("utf-8"),
        "polity_constitution.txt"
    )
    doc_id = doc_res["id"]

    mock_chatgpt_json = {
        "heading_mr": "भारतीय राज्यघटनेची निर्मिती",
        "subheading_mr": "राज्यशास्त्र (Polity) • MPSC Prelims",
        "short_definition_mr": "भारतीय राज्यघटना तयार करण्यासाठी २ वर्षे, ११ महिने आणि १८ दिवस लागले.",
        "key_points": [
            "९ डिसेंबर १९४६: पहिली बैठक (हंगामी अध्यक्ष डॉ. सच्चिदानंद सिन्हा).",
            "११ डिसेंबर १९४६: डॉ. राजेंद्र प्रसाद कायमस्वरूपी अध्यक्ष.",
            "२९ ऑगस्ट १९४७: मसुदा समितीचे अध्यक्ष डॉ. बाबासाहेब आंबेडकर."
        ],
        "important_dates": [
            "९ डिसेंबर १९४६ - पहिली बैठक",
            "२६ नोव्हेंबर १९४९ - राज्यघटना स्वीकृत",
            "२६ जानेवारी १९५० - राज्यघटना लागू"
        ],
        "important_personalities": [
            "डॉ. बाबासाहेब आंबेडकर - मसुदा समिती अध्यक्ष / भारतीय राज्यघटनेचे शिल्पकार",
            "डॉ. राजेंद्र प्रसाद - घटना समिती अध्यक्ष"
        ],
        "memory_tricks": ["💡 ९-११-१३ डिसेंबर १९४६: पहिल्या तीन ऐतिहासिक बैठका"],
        "exam_points": ["🎯 मसुदा समिती स्थापना तारीख: २९ ऑगस्ट १९४७"]
    }

    with patch("app.services.ai.llm_provider.LLMProvider._execute_with_provider", return_value=(json.dumps(mock_chatgpt_json), "ChatGPT")):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/prototype/notes/generate",
                json={
                    "doc_id": doc_id,
                    "subject": "राज्यशास्त्र (Polity & Governance)",
                    "scope": "chapter",
                    "chapter_id": 1,
                    "exam_target": "mpsc_prelims",
                    "output_type": "handwritten_notes",
                    "custom_instruction": "घटना निर्मितीच्या तारखा आणि समित्यांवर भर दे."
                }
            )
            assert res.status_code == 200
            data = res.json()
            assert "राज्यशास्त्र" in data["subject"]
            assert len(data["structured_note"]["important_dates"]) >= 2

@pytest.mark.asyncio
async def test_subject_selection_geography_compare_table():
    """Verifies Geography subject processing with table comparison instruction."""
    doc_res = await user_controlled_notes_service.process_upload(
        SAMPLE_GEOGRAPHY_DOC.encode("utf-8"),
        "mh_geography.txt"
    )
    doc_id = doc_res["id"]

    mock_chatgpt_json = {
        "heading_mr": "महाराष्ट्राची प्राकृतिक रचना",
        "subheading_mr": "भूगोल (Geography) • तुलनात्मक तक्ता",
        "short_definition_mr": "महाराष्ट्राचे प्राकृतिक दृष्ट्या कोकण, पश्चिम घाट आणि दख्खन पठार असे तीन भाग आहेत.",
        "table": {
            "title_mr": "प्राकृतिक विभागांची तुलना",
            "headers": ["विभाग", "वैशिष्ट्ये", "सर्वोच्च बिंदू"],
            "rows": [
                ["कोकण", "अरबी समुद्राला लागून", "उत्तर-दक्षिण किनारपट्टी"],
                ["सह्याद्री", "जलविभाजक", "कळसुबाई (१६४६ मी)"],
                ["दख्खन पठार", "बेसाल्ट खडक", "९०% भूभाग"]
            ]
        },
        "key_points": ["कळसुबाई शिखर अहमदनगर जिल्ह्यात आहे."],
        "important_dates": [],
        "important_personalities": [],
        "exam_points": ["🎯 कळसुबाई उंची: १६४६ मीटर"]
    }

    with patch("app.services.ai.llm_provider.LLMProvider._execute_with_provider", return_value=(json.dumps(mock_chatgpt_json), "ChatGPT")):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/prototype/notes/generate",
                json={
                    "doc_id": doc_id,
                    "subject": "महाराष्ट्राचा भूगोल (Maharashtra Geography)",
                    "scope": "chapter",
                    "chapter_id": 1,
                    "exam_target": "mpsc_mains",
                    "output_type": "detailed_notes",
                    "custom_instruction": "प्राकृतिक विभागांचा तुलनात्मक तक्ता बनव."
                }
            )
            assert res.status_code == 200
            data = res.json()
            assert "भूगोल" in data["subject"]
            assert data["structured_note"]["table"]["headers"] == ["विभाग", "वैशिष्ट्ये", "सर्वोच्च बिंदू"]

@pytest.mark.asyncio
async def test_full_book_multi_chapter_generation():
    """Verifies that selecting 'full_file' processes all chapters and creates combined PDF."""
    doc_res = await user_controlled_notes_service.process_upload(
        SAMPLE_HISTORY_DOC.encode("utf-8"),
        "multi_chapter_history.txt"
    )
    doc_id = doc_res["id"]
    assert doc_res["total_chapters"] == 2

    mock_ch1 = {
        "heading_mr": "प्रकरण १: १८५७ चा राष्ट्रीय उठाव",
        "subheading_mr": "इतिहास",
        "short_definition_mr": "१८५७ चा लढा",
        "key_points": ["मंगल पांडे यांचे बंड"],
        "important_dates": ["२९ मार्च १८५७"],
        "important_personalities": ["मंगल पांडे"],
        "exam_points": ["बराकपूर छावणी"]
    }
    mock_ch2 = {
        "heading_mr": "प्रकरण २: १८५८ चा राणीचा जाहीरनामा",
        "subheading_mr": "इतिहास",
        "short_definition_mr": "कंपनी सत्तेचा अंत",
        "key_points": ["अलाहाबाद दरबारात वाचन"],
        "important_dates": ["१ नोव्हेंबर १८५८"],
        "important_personalities": ["लॉर्ड कॅनिंग"],
        "exam_points": ["भारत राज्यसचिव पद"]
    }

    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return (json.dumps(mock_ch1 if call_count % 2 == 1 else mock_ch2), "ChatGPT")

    with patch("app.services.ai.llm_provider.LLMProvider._execute_with_provider", side_effect=side_effect):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                "/prototype/notes/generate",
                json={
                    "doc_id": doc_id,
                    "subject": "इतिहास (History)",
                    "scope": "full_file",
                    "chapter_id": 0,
                    "exam_target": "mpsc_prelims",
                    "output_type": "handwritten_notes"
                }
            )
            assert res.status_code == 200
            data = res.json()
            assert data["total_processed_chapters"] == 2
            assert len(data["all_chapters_notes"]) == 2
            assert data["page_count"] >= 2

            # Verify PDF download
            pdf_res = await client.get(f"/prototype/notes/{doc_id}/pdf")
            assert pdf_res.status_code == 200
            assert pdf_res.headers["content-type"] == "application/pdf"
            assert len(pdf_res.content) > 1000
