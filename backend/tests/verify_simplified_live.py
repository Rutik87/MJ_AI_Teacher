import asyncio
import httpx

SAMPLE_TXT_CONTENT = """प्रकरण १: महाराष्ट्रातील समाजसुधारक
महात्मा जोतीराव फुले यांनी २४ सप्टेंबर १८७३ रोजी सत्यशोधक समाजाची स्थापना केली.
त्यांनी शूद्र व अतिशूद्रांच्या शिक्षणासाठी मुलींची पहिली शाळा १ जानेवारी १८४८ रोजी पुण्यात भिडे वाड्यात सुरू केली.
सावित्रीबाई फुले यांनी या शाळेत पहिल्या शिक्षिका म्हणून अध्यापनाचे कार्य केले.
'गुलामगिरी', 'शेतकऱ्याचा असूड' हे महात्मा फुलेंचे प्रसिद्ध ग्रंथ आहेत."""

async def main():
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("=" * 65)
        print("MPSC AI SIMPLIFIED ARCHITECTURE — LIVE PRODUCTION AUDIT")
        print("=" * 65)

        base_url = "https://mj-ai-teacher.onrender.com"

        # 1. Health check
        r_health = await client.get(f"{base_url}/api/health")
        print(f"[TEST 1] Health Check: {r_health.status_code} -> {r_health.json()}")
        assert r_health.status_code == 200

        # 2. Subjects list
        r_subj = await client.get(f"{base_url}/api/subjects")
        print(f"[TEST 2] Subjects List: {r_subj.status_code} (Total: {len(r_subj.json())})")
        assert r_subj.status_code == 200
        assert len(r_subj.json()) >= 10

        # 3. File Upload (TXT/PDF)
        files = {"file": ("maharashtra_reformers.txt", SAMPLE_TXT_CONTENT.encode("utf-8"), "text/plain")}
        r_up = await client.post(f"{base_url}/api/books/upload", files=files, data={"title": "महाराष्ट्रातील समाजसुधारक", "subject": "महाराष्ट्राचा इतिहास"})
        print(f"[TEST 3] File Upload: {r_up.status_code} -> {r_up.json()}")
        assert r_up.status_code == 200
        book_id = r_up.json()["id"]

        # Wait 3 seconds for async RAG ingestion
        await asyncio.sleep(3)

        # 4. List Files
        r_books = await client.get(f"{base_url}/api/books")
        print(f"[TEST 4] Books List: {r_books.status_code} (Found {len(r_books.json())} books)")
        assert r_books.status_code == 200

        # 5. File Signed URL
        r_url = await client.get(f"{base_url}/api/books/{book_id}/signed-url")
        print(f"[TEST 5] File Signed URL: {r_url.status_code} -> {r_url.json().get('url', '')[:60]}...")
        assert r_url.status_code == 200

        # 6. File-Aware ChatGPT Q&A
        chat_payload = {
            "message": "सत्यशोधक समाजाची स्थापना कोणी व कधी केली?",
            "user_id": 1
        }
        r_chat = await client.post(f"{base_url}/api/books/{book_id}/chat", json=chat_payload)
        print(f"[TEST 6] File ChatGPT Response: {r_chat.status_code}")
        ans_data = r_chat.json()
        print(f"         Answer: {ans_data.get('answer', '')[:120]}...")
        print(f"         Citations: {len(ans_data.get('source_citations', []))} sources")
        assert r_chat.status_code == 200

        # 7. Follow-up Question
        followup_payload = {
            "message": "मुलींची पहिली शाळा कधी सुरू झाली?",
            "user_id": 1
        }
        r_follow = await client.post(f"{base_url}/api/books/{book_id}/chat", json=followup_payload)
        print(f"[TEST 7] Follow-up Response: {r_follow.status_code}")
        print(f"         Answer: {r_follow.json().get('answer', '')[:120]}...")
        assert r_follow.status_code == 200

        # 8. File Chat History
        r_hist = await client.get(f"{base_url}/api/books/{book_id}/chat/history?user_id=1")
        print(f"[TEST 8] Book Chat History: {r_hist.status_code} (Messages: {len(r_hist.json())})")
        assert r_hist.status_code == 200
        assert len(r_hist.json()) >= 4  # 2 user msgs + 2 ai answers

        # 9. General Chat Message Endpoint
        r_gen_chat = await client.post(f"{base_url}/api/chat/message", json={
            "message": "MPSC राज्यसेवा पूर्व परीक्षेसाठी सामान्य अध्ययनाचे मुख्य घटक कोणते आहेत?",
            "mode": "general_chat"
        })
        print(f"[TEST 9] General Chat Response: {r_gen_chat.status_code}")
        print(f"         Message: {r_gen_chat.json().get('message', '')[:100]}...")
        assert r_gen_chat.status_code == 200

        # 10. Delete File
        r_del = await client.delete(f"{base_url}/api/books/{book_id}")
        print(f"[TEST 10] Delete Book: {r_del.status_code}")
        assert r_del.status_code == 200

        print("\nALL PRODUCTION ACCEPTANCE CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
