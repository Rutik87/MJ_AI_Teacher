import pytest
import os
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db
from app.models.schema import Book, Chapter, Page, ChatSession, ChatMessage

SAMPLE_BOOK_TXT = """# आधुनिक भारताचा इतिहास: १८५७ चा उठाव

## प्रकरण १: १८५७ च्या उठावाची कारणे
१८५७ च्या उठावाची प्रमुख राजकीय, आर्थिक, सामाजिक आणि लष्करी कारणे होती.
डलहौसीचे खालसा धोरण आणि संस्थानिकांवर झालेला अन्याय यामुळे रोष निर्माण झाला.
ब्रिटिश सैन्यातील भारतीय सैनिकांना मिळणारी दुय्यम वागणूक आणि एनफिल्ड बंदुकीच्या काडतुसांची घटना ही तात्कालिक कारणे ठरली.

## प्रकरण २: उठावाचे प्रमुख नेते
झाशीची राणी लक्ष्मीबाई, तात्या टोपे, नानासाहेब पेशवे, आणि कुंवर सिंह हे उठावाचे प्रमुख नेते होते.
१० मे १८५७ रोजी मीरत छावणीत सैनिकांनी बंड पुकारले.
"""

SAMPLE_POLITY_TXT = """# भारताचे संविधान व राज्यशास्त्र

## प्रकरण १: मूलभूत हक्क व मार्गदर्शक तत्त्वे
भारतीय राज्यघटनेच्या भाग ३ मध्ये कलम १२ ते ३५ दरम्यान मूलभूत हक्कांची तरतूद आहे.
मार्गदर्शक तत्त्वे भाग ४ मध्ये कलम ३६ ते ५१ दरम्यान दिली आहेत.
"""

@pytest.mark.asyncio
async def test_direct_chatgpt_full_v1_pipeline():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload Document 1 (History)
        files1 = {"file": ("modern_india.txt", SAMPLE_BOOK_TXT.encode("utf-8"), "text/plain")}
        res1 = await client.post("/api/books/upload", files=files1, data={"title": "आधुनिक भारताचा इतिहास", "subject": "इतिहास"})
        assert res1.status_code == 200
        book1_id = res1.json()["id"]

        # 2. Upload Document 2 (Polity)
        files2 = {"file": ("polity_mpsc.txt", SAMPLE_POLITY_TXT.encode("utf-8"), "text/plain")}
        res2 = await client.post("/api/books/upload", files=files2, data={"title": "भारतीय राज्यशास्त्र", "subject": "राज्यशास्त्र"})
        assert res2.status_code == 200
        book2_id = res2.json()["id"]

        # 3. Create a new ChatGPT Session with Document 1 Attached
        create_res = await client.post("/api/chat/sessions", json={
            "title": "1857 चा उठाव अभ्यास",
            "attached_book_ids": [book1_id]
        })
        assert create_res.status_code == 200
        session_id = create_res.json()["id"]

        # 4. Ask Document Structure Question
        q1_res = await client.post("/api/chat/message", json={
            "session_id": session_id,
            "message": "या पुस्तकात एकूण किती chapters आहेत आणि त्यांची नावे काय आहेत?",
            "book_id": book1_id
        })
        assert q1_res.status_code == 200
        q1_data = q1_res.json()
        assert q1_data["sender"] == "ai"
        assert len(q1_data["message"]) > 10

        # 5. Ask Content Question
        q2_res = await client.post("/api/chat/message", json={
            "session_id": session_id,
            "message": "१८५७ च्या उठावाची मुख्य कारणे समजावून सांगा."
        })
        assert q2_res.status_code == 200

        # 6. Ask Follow-up with Pronoun Reference
        followup_res = await client.post("/api/chat/message", json={
            "session_id": session_id,
            "message": "त्यातील एनफिल्ड काडतुसांची घटना काय होती?"
        })
        assert followup_res.status_code == 200

        # 7. Multi-Document Comparison
        compare_res = await client.post("/api/chat/message", json={
            "session_id": session_id,
            "message": "इतिहास आणि राज्यशास्त्र या दोन्ही पुस्तकांमधील महत्त्वाचे घटक तुलना करून सांगा.",
            "book_ids": [book1_id, book2_id]
        })
        assert compare_res.status_code == 200

        # 8. Check Session Message History Continuity
        hist_res = await client.get(f"/api/chat/sessions/{session_id}/messages")
        assert hist_res.status_code == 200
        messages = hist_res.json()
        assert len(messages) >= 8

        # 9. Generate Downloadable Artifact (PDF) and Save to Supabase Library
        art_res = await client.post("/api/chat/generate-artifact", json={
            "session_id": session_id,
            "source_book_id": book1_id,
            "title": "1857 उठाव Revision Sheet",
            "content": "### १८५७ चा उठाव\n\n- प्रमुख कारणे: डलहौसीचे खालसा धोरण\n- तात्कालिक कारण: एनफिल्ड काडतुसे",
            "artifact_type": "pdf"
        })
        assert art_res.status_code == 200
        art_data = art_res.json()
        assert art_data["is_generated"] is True
        generated_id = art_data["id"]

        # 10. Verify generated artifact appears in File Library under 'books'
        books_res = await client.get("/api/books")
        assert books_res.status_code == 200
        all_books = books_res.json()
        gen_book = next((b for b in all_books if b["id"] == generated_id), None)
        assert gen_book is not None
        assert gen_book["is_generated"] is True

        # 11. Test Study Schedule Analyzer
        sched_save = await client.post("/api/schedule", json={
            "target_exam": "MPSC राज्यसेवा",
            "daily_study_hours": 6.0,
            "slots": [{"time_slot": "08:00 AM - 10:00 AM", "subject": "इतिहास", "topic": "१८५७ चा उठाव", "activity": "वाचन"}]
        })
        assert sched_save.status_code == 200

        sched_ana = await client.post("/api/schedule/analyze", json={
            "target_exam": "MPSC राज्यसेवा",
            "daily_study_hours": 6.0,
            "exam_date": "2026-11-15",
            "weak_subjects": ["अर्थशास्त्र"]
        })
        assert sched_ana.status_code == 200
        assert "analysis_markdown" in sched_ana.json()

        # 12. Cascade Delete Tests
        del_book1 = await client.delete(f"/api/books/{book1_id}")
        assert del_book1.status_code == 200

        del_book2 = await client.delete(f"/api/books/{book2_id}")
        assert del_book2.status_code == 200

        del_session = await client.delete(f"/api/chat/sessions/{session_id}")
        assert del_session.status_code == 200

@pytest.mark.asyncio
async def test_direct_book_workspace_chat():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Upload book
        files = {"file": ("revolt_1857.txt", SAMPLE_BOOK_TXT.encode("utf-8"), "text/plain")}
        res = await client.post("/api/books/upload", files=files, data={"title": "१८५७ उठाव नोट्स", "subject": "इतिहास"})
        assert res.status_code == 200
        b_id = res.json()["id"]

        # Book-specific direct ChatGPT chat
        chat_res = await client.post(f"/api/books/{b_id}/chat", json={
            "message": "या पुस्तकातील महत्त्वाच्या तारखांची यादी द्या.",
            "user_id": 1
        })
        assert chat_res.status_code == 200
        assert "answer" in chat_res.json()

        # History check
        hist_res = await client.get(f"/api/books/{b_id}/chat/history?user_id=1")
        assert hist_res.status_code == 200
        assert len(hist_res.json()) >= 2

        # Cleanup
        del_res = await client.delete(f"/api/books/{b_id}")
        assert del_res.status_code == 200
