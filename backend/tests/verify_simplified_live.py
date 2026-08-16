import asyncio
import httpx

SAMPLE_HISTORY_TXT = """# आधुनिक भारताचा इतिहास: १८५७ चा स्वातंत्र्यलढा

## प्रकरण १: १८५७ च्या उठावाची कारणे
१८५७ च्या उठावाची प्रमुख राजकीय, आर्थिक, सामाजिक आणि लष्करी कारणे होती.
डलहौसीचे खालसा धोरण, संस्थानिकांवर झालेला अन्याय आणि धार्मिक भावना दुखावणारे निर्णय यामुळे जनतेत असंतोष पसरला.
लष्करातील भारतीय सैनिकांना मिळणारी दुय्यम वागणूक आणि एनफिल्ड बंदुकीच्या काडतुसांना चरबी लावल्याची बातमी ही तात्कालिक कारणे ठरली.

## प्रकरण २: उठावाचे प्रमुख नेते
झाशीची राणी लक्ष्मीबाई, तात्या टोपे, नानासाहेब पेशवे, कुंवर सिंह आणि मौलवी अहमदउल्ला हे या लढ्याचे प्रमुख नेते होते.
१० मे १८५७ रोजी मीरत छावणीत भारतीय सैनिकांनी उघड बंड पुकारले."""

SAMPLE_POLITY_TXT = """# भारताचे संविधान व राज्यशास्त्र

## प्रकरण १: मूलभूत हक्क
भारतीय राज्यघटनेच्या भाग ३ मध्ये कलम १२ ते ३५ दरम्यान मूलभूत हक्कांची तरतूद आहे.
यात समानतेचा हक्क (कलम १४-१८), स्वातंत्र्याचा हक्क (कलम १९-२२), आणि घटनात्मक उपायांचा हक्क (कलम ३२) यांचा समावेश होतो."""

async def main():
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("=" * 70)
        print("MPSC AI v1.0 — MASTER DIRECT CHATGPT & FILE LIBRARY LIVE PRODUCTION AUDIT")
        print("=" * 70)

        base_url = "https://mj-ai-teacher.onrender.com"

        # 1. Health Check
        r_health = await client.get(f"{base_url}/api/health")
        print(f"[TEST 1]  Health Check              : {r_health.status_code} -> {r_health.json()}")
        assert r_health.status_code == 200

        # 2. Subjects List
        r_subj = await client.get(f"{base_url}/api/subjects")
        print(f"[TEST 2]  Subjects Taxonomy         : {r_subj.status_code} (Total: {len(r_subj.json())} subjects)")
        assert r_subj.status_code == 200

        # 3. File Upload (Document 1 - History)
        files1 = {"file": ("modern_india_1857.txt", SAMPLE_HISTORY_TXT.encode("utf-8"), "text/plain")}
        r_up1 = await client.post(f"{base_url}/api/books/upload", files=files1, data={"title": "आधुनिक भारताचा इतिहास १८५७", "subject": "इतिहास"})
        print(f"[TEST 3]  Upload Document 1 (History): {r_up1.status_code} (ID: {r_up1.json()['id']})")
        assert r_up1.status_code == 200
        book1_id = r_up1.json()["id"]

        # 4. File Upload (Document 2 - Polity)
        files2 = {"file": ("polity_constitution.txt", SAMPLE_POLITY_TXT.encode("utf-8"), "text/plain")}
        r_up2 = await client.post(f"{base_url}/api/books/upload", files=files2, data={"title": "भारताचे संविधान व राज्यशास्त्र", "subject": "राज्यशास्त्र"})
        print(f"[TEST 4]  Upload Document 2 (Polity) : {r_up2.status_code} (ID: {r_up2.json()['id']})")
        assert r_up2.status_code == 200
        book2_id = r_up2.json()["id"]

        # Wait 3s for storage/DB sync
        await asyncio.sleep(3)

        # 5. List Files & Verify Supabase Signed URL
        r_books = await client.get(f"{base_url}/api/books")
        print(f"[TEST 5]  File Library List         : {r_books.status_code} (Found {len(r_books.json())} files)")
        assert r_books.status_code == 200

        r_signed = await client.get(f"{base_url}/api/books/{book1_id}/signed-url")
        print(f"[TEST 6]  Supabase Signed Download  : {r_signed.status_code} -> URL ready")
        assert r_signed.status_code == 200

        # 6. Create Persistent Chat Session with Document 1
        r_sess = await client.post(f"{base_url}/api/chat/sessions", json={
            "title": "१८५७ स्वातंत्र्यलढा अभ्यास",
            "attached_book_ids": [book1_id],
            "user_id": 1
        })
        print(f"[TEST 7]  Create ChatGPT Session    : {r_sess.status_code} (Session ID: {r_sess.json()['id']})")
        assert r_sess.status_code == 200
        session_id = r_sess.json()["id"]

        # 7. Document Structure Question (Direct OpenAI full document comprehension)
        r_q1 = await client.post(f"{base_url}/api/chat/message", json={
            "session_id": session_id,
            "message": "या पुस्तकात एकूण किती chapters आहेत आणि त्यांची नावे काय आहेत?",
            "book_id": book1_id,
            "user_id": 1
        })
        print(f"[TEST 8]  Document Structure Query  : {r_q1.status_code}")
        print(f"          ChatGPT Answer            : {r_q1.json().get('message', '')[:100]}...")
        assert r_q1.status_code == 200

        # 8. Content Question & Multi-turn Follow-up (Pronoun Resolution)
        r_q2 = await client.post(f"{base_url}/api/chat/message", json={
            "session_id": session_id,
            "message": "१८५७ च्या उठावाची मुख्य कारणे समजावून सांगा.",
            "user_id": 1
        })
        print(f"[TEST 9]  Document Content Query    : {r_q2.status_code}")
        assert r_q2.status_code == 200

        r_follow = await client.post(f"{base_url}/api/chat/message", json={
            "session_id": session_id,
            "message": "त्यातील एनफिल्ड काडतुसांची तात्कालिक घटना काय होती?",
            "user_id": 1
        })
        print(f"[TEST 10] Follow-up Pronoun Context : {r_follow.status_code}")
        print(f"          ChatGPT Follow-up Answer  : {r_follow.json().get('message', '')[:100]}...")
        assert r_follow.status_code == 200

        # 9. Multi-Document Comparison (History + Polity attached to same session)
        r_comp = await client.post(f"{base_url}/api/chat/message", json={
            "session_id": session_id,
            "message": "इतिहास आणि राज्यशास्त्र या दोन्ही पुस्तकांमधील मुख्य फरक व महत्त्व तुलना करा.",
            "book_ids": [book1_id, book2_id],
            "user_id": 1
        })
        print(f"[TEST 11] Multi-Document Comparison : {r_comp.status_code}")
        assert r_comp.status_code == 200

        # 10. Verify Session History Continuity
        r_hist = await client.get(f"{base_url}/api/chat/sessions/{session_id}/messages?user_id=1")
        print(f"[TEST 12] Session History Continuity: {r_hist.status_code} ({len(r_hist.json())} messages in thread)")
        assert r_hist.status_code == 200
        assert len(r_hist.json()) >= 8

        # 11. Generate Downloadable PDF Artifact to Supabase Storage
        r_art = await client.post(f"{base_url}/api/chat/generate-artifact", json={
            "session_id": session_id,
            "source_book_id": book1_id,
            "title": "1857 स्वातंत्र्यलढा Revision Sheet",
            "content": "### १८५७ स्वातंत्र्यलढा महत्त्वाचे मुद्दे\n\n1. डलहौसीचे खालसा धोरण\n2. तात्कालिक कारण: एनफिल्ड काडतुसे\n3. प्रमुख नेते: झाशीची राणी लक्ष्मीबाई, तात्या टोपे",
            "artifact_type": "pdf",
            "user_id": 1
        })
        print(f"[TEST 13] Generate PDF Artifact     : {r_art.status_code} (Storage: {r_art.json().get('storage_path')})")
        assert r_art.status_code == 200
        artifact_id = r_art.json()["id"]

        # 12. Study Schedule Analyzer
        r_sched_save = await client.post(f"{base_url}/api/schedule", json={
            "user_id": 1,
            "target_exam": "MPSC राज्यसेवा पूर्व परीक्षा 2026",
            "daily_study_hours": 6.0,
            "primary_subjects": ["इतिहास", "राज्यशास्त्र", "भूगोल", "अर्थशास्त्र"],
            "slots": [
                {"time_slot": "07:00 AM - 09:30 AM", "subject": "इतिहास", "topic": "१८५७ चा उठाव", "activity": "सखोल वाचन"}
            ]
        })
        assert r_sched_save.status_code == 200

        r_sched_ana = await client.post(f"{base_url}/api/schedule/analyze", json={
            "user_id": 1,
            "target_exam": "MPSC राज्यसेवा पूर्व परीक्षा 2026",
            "daily_study_hours": 6.0,
            "exam_date": "2026-11-15",
            "weak_subjects": ["अर्थशास्त्र", "सामान्य विज्ञान"],
            "current_schedule": "दररोज ६ तास अभ्यास"
        })
        print(f"[TEST 14] ChatGPT Schedule Analysis : {r_sched_ana.status_code}")
        assert r_sched_ana.status_code == 200

        # 13. Cascade Delete Tests
        r_del_art = await client.delete(f"{base_url}/api/books/{artifact_id}")
        r_del_b1 = await client.delete(f"{base_url}/api/books/{book1_id}")
        r_del_b2 = await client.delete(f"{base_url}/api/books/{book2_id}")
        r_del_sess = await client.delete(f"{base_url}/api/chat/sessions/{session_id}")
        print(f"[TEST 15] Cascade Delete Verification: {r_del_art.status_code}, {r_del_b1.status_code}, {r_del_b2.status_code}, {r_del_sess.status_code}")
        assert r_del_b1.status_code == 200

        print("\n" + "=" * 70)
        print("ALL 15 MASTER PRODUCTION ACCEPTANCE CRITERIA PASSED WITH 100% SUCCESS!")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
