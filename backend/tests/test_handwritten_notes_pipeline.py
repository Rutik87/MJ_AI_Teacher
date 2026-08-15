import pytest
import os
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db
from app.services.notes.note_generator_service import note_generator_service
from app.services.notes.pdf_note_renderer import pdf_note_renderer

@pytest.mark.asyncio
async def test_handwritten_note_generation_service():
    """Verify that NoteGeneratorService analyzes chapters and creates complete structured Marathi notes."""
    await init_db()
    # Create sample structured chapter data
    chapters = [
        {
            "heading_mr": "१८५७ चा राष्ट्रीय उठाव",
            "subheading_mr": "पार्श्वभूमी, प्रमुख कारणे व स्वरूप",
            "short_definition_mr": "१८५७ चा उठाव हा ब्रिटिश ईस्ट इंडिया कंपनीच्या अन्यायाविरुद्धचा पहिला व्यापक सशस्त्र लढा होता.",
            "important_concepts": [
                {"title_mr": "कार्तुस प्रकरण", "explanation_mr": "एनफिल्ड बंदुकीच्या काडतुसांना चरबी लावल्याच्या संशयामुळे सैन्यात असंतोष पसरला."},
                {"title_mr": "दत्तक विधान नामंजूर", "explanation_mr": "लॉर्ड डलहौसीने झाशी, सातारा, नागपूर संस्थाने खालसा केली."}
            ],
            "key_points": [
                "१. २९ मार्च १८५७ रोजी मंगल पांडे यांनी बराकपूर येथे बंड पुकारले.",
                "२. १० मे १८५७ रोजी मीरत छावणीत प्रत्यक्ष उठावाला सुरुवात झाली.",
                "३. बहादूर शाह जफर यांना क्रांतीचे नेते घोषित करण्यात आले."
            ],
            "examples": ["उदा. झाशीची राणी लक्ष्मीबाई व तात्या टोपे यांचे शौर्य"],
            "formulas_or_laws": ["१८५८ चा भारत सरकार कायदा: कंपनीची सत्ता समाप्त"],
            "table": {
                "title_mr": "उठावातील प्रमुख नेते व ठिकाणे",
                "headers": ["ठिकाण", "नेते", "दडपशाही करणारा ब्रिटिश अधिकारी"],
                "rows": [
                    ["दिल्ली", "बहादूर शाह जफर / जनरल बख्त खान", "जॉन निकोल्सन"],
                    ["कानपूर", "नानासाहेब पेशवे / तात्या टोपे", "कॉलिन कॅम्पबेल"],
                    ["झाशी", "राणी लक्ष्मीबाई", "ह्यू रोज"]
                ]
            },
            "flowchart_steps": [
                "पायरी १: सैनिकांमधील असंतोष व मंगल पांडे यांचे बंड",
                "पायरी २: मीरत ते दिल्ली क्रांतीचा प्रसार",
                "पायरी ३: १८५८ ची राणीची सनद व सत्तांतर"
            ],
            "exam_points": [
                "🎯 MPSC वारंवार १८५८ च्या कायद्यातील तरतुदी आणि उठावाच्या नेत्यांवर प्रश्न विचारते."
            ],
            "quick_revision_box": [
                "⚡ मंगल पांडे - बराकपूर, तात्या टोपे - कानपूर/ग्वाल्हेर, राणी लक्ष्मीबाई - झाशी."
            ],
            "common_mistakes": [
                "⚠️ बहादुर शाह जफर आणि नानासाहेब पेशवे यांच्या भूमिकेत गल्लत करू नका."
            ]
        }
    ]

    # Test PDF rendering
    pdf_path, pdf_url, page_count = await pdf_note_renderer.render_notebook_pdf(
        book_id=999,
        book_title="महाराष्ट्राचा व भारताचा इतिहास",
        chapters=chapters
    )

    assert os.path.exists(pdf_path), "PDF file was not created on disk"
    assert os.path.getsize(pdf_path) > 1000, "PDF file is too small"
    assert page_count >= 1
    assert pdf_url == "/api/notes/999/download"

@pytest.mark.asyncio
async def test_handwritten_notes_api_full_workflow():
    """Test full REST API lifecycle: Generate -> Status -> Download PDF -> Markdown -> Delete."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a dummy book in the database first via books API
        # Or test with an existing sample book ID
        upload_resp = await client.post(
            "/api/books/upload",
            files={"file": ("mpsc_polity_notes.txt", b"Bhartiya Rajyaghatna Kalam 14 Samanta. Kalam 19 Swatantrya. Kalam 21 Jivitache Swatantrya.", "text/plain")},
            data={"title": "भारतीय राज्यघटना नोट्स", "subject_name": "राज्यशास्त्र"}
        )
        assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
        book_id = upload_resp.json()["id"]

        # 2. Trigger Handwritten Notes Generation
        gen_resp = await client.post(f"/api/notes/generate/{book_id}")
        assert gen_resp.status_code == 200, f"Notes generation failed: {gen_resp.text}"
        gen_data = gen_resp.json()
        assert gen_data["status"] == "success"
        assert gen_data["book_id"] == book_id
        assert "chapters" in gen_data
        assert len(gen_data["chapters"]) >= 1

        # 3. Check Note Status
        status_resp = await client.get(f"/api/notes/{book_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["has_notes"] is True
        assert status_data["status"] == "completed"
        assert status_data["progress_percent"] == 100.0
        assert status_data["pdf_url"] is not None

        # 4. Test PDF Download endpoint
        download_resp = await client.get(f"/api/notes/{book_id}/download")
        assert download_resp.status_code == 200
        assert download_resp.headers.get("content-type") == "application/pdf"
        assert len(download_resp.content) > 1000, "Downloaded PDF content is too small"

        # 5. Test Markdown Download endpoint
        md_resp = await client.get(f"/api/notes/{book_id}/markdown")
        assert md_resp.status_code == 200
        assert "text/markdown" in md_resp.headers.get("content-type", "")
        assert len(md_resp.text) > 50

        # 6. Test Delete Notes endpoint
        del_resp = await client.delete(f"/api/notes/{book_id}")
        assert del_resp.status_code == 200
        del_data = del_resp.json()
        assert del_data["status"] == "success"

        # 7. Verify status is not_generated after deletion
        after_del = await client.get(f"/api/notes/{book_id}")
        assert after_del.status_code == 200
        assert after_del.json()["has_notes"] is False

@pytest.mark.asyncio
async def test_handwritten_notes_security_and_404():
    """Verify proper 404 responses for non-existent books and notes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid book generation
        res = await client.post("/api/notes/generate/999999")
        assert res.status_code == 404

        # Invalid book download
        dl_res = await client.get("/api/notes/999999/download")
        assert dl_res.status_code == 404

        # Invalid book delete
        del_res = await client.delete("/api/notes/999999")
        assert del_res.status_code == 404
