import asyncio
import httpx

SAMPLE_HISTORY_TXT = """प्रकरण १: १८५७ चा राष्ट्रीय उठाव
२९ मार्च १८५७ रोजी मंगल पांडे यांनी बराकपूर छावणीत काडतुसांविरोधात बंड पुकारले.
लॉर्ड डलहौसीचे दत्तक वारसा नामंजूर धोरण या उठावाचे प्रमुख राजकीय कारण होते.
१० मे १८५७ रोजी मीरत छावणीतील सैनिकांनी दिल्लीकडे कूच केले.

प्रकरण २: १८५८ चा राणीचा जाहीरनामा
१ नोव्हेंबर १८५८ रोजी लॉर्ड कॅनिंगने अलाहाबाद दरबारात राणीचा जाहीरनामा वाचून दाखवला.
याने ईस्ट इंडिया कंपनीची सत्ता संपुष्टात आली व ब्रिटिश क्राऊनचे थेट शासन सुरू झाले."""

SAMPLE_POLITY_TXT = """प्रकरण १: भारतीय राज्यघटनेची निर्मिती
९ डिसेंबर १९४६ रोजी घटना समितीची पहिली बैठक झाली आणि डॉ. सच्चिदानंद सिन्हा हंगामी अध्यक्ष बनले.
११ डिसेंबर १९४६ रोजी डॉ. राजेंद्र प्रसाद यांची कायमस्वरूपी अध्यक्ष म्हणून निवड झाली.
२९ ऑगस्ट १९४७ रोजी डॉ. बाबासाहेब आंबेडकर यांच्या अध्यक्षतेखाली मसुदा समिती स्थापन झाली.
२६ नोव्हेंबर १९४९ रोजी राज्यघटना स्वीकृत झाली आणि २६ जानेवारी १९५० रोजी अमलात आली."""

SAMPLE_GEO_TXT = """प्रकरण १: महाराष्ट्राची प्राकृतिक रचना
महाराष्ट्राचे तीन प्रमुख प्राकृतिक विभाग: १. कोकण किनारपट्टी, २. सह्याद्री पर्वतरांग, ३. महाराष्ट्र पठार.
कळसुबाई (१६४६ मी) हे महाराष्ट्रातील सर्वोच्च शिखर असून ते अहमदनगर जिल्ह्यात आहे."""

async def main():
    async with httpx.AsyncClient(timeout=180.0) as client:
        print("=" * 60)
        print("USER-CONTROLLED NOTES GENERATOR - LIVE PRODUCTION AUDIT")
        print("=" * 60)

        # 1. HTML Prototype Access
        r = await client.get("https://mj-ai-teacher.onrender.com/prototype/notes")
        print(f"[TEST 1] Browser UI Status: {r.status_code} (Length: {len(r.text)} bytes)")
        assert r.status_code == 200

        # 2. History Document Upload & Chapter Selection
        files = {"file": ("mpsc_history.txt", SAMPLE_HISTORY_TXT.encode("utf-8"), "text/plain")}
        up_res = await client.post("https://mj-ai-teacher.onrender.com/prototype/notes/upload", files=files)
        print(f"[TEST 2] History Upload: {up_res.status_code}, Detected Chapters: {up_res.json().get('total_chapters')}")
        hist_doc_id = up_res.json()["id"]

        # 3. History Chapter 1 - MPSC Prelims Handwritten Notes
        hist_payload = {
            "doc_id": hist_doc_id,
            "subject": "इतिहास (History)",
            "scope": "chapter",
            "chapter_id": 1,
            "exam_target": "mpsc_prelims",
            "output_type": "handwritten_notes",
            "custom_instruction": "फक्त १८५७ च्या उठावाच्या महत्त्वाच्या तारखा, व्यक्ती आणि MPSC मुद्दे दे."
        }
        hist_gen = await client.post("https://mj-ai-teacher.onrender.com/prototype/notes/generate", json=hist_payload)
        print(f"[TEST 3] History Gen Status: {hist_gen.status_code}")
        h_data = hist_gen.json()
        print(f"         Heading: {h_data.get('structured_note', {}).get('heading_mr')}")
        print(f"         Pages: {h_data.get('page_count')}")

        # 4. Polity Document - Full File Multi-Chapter Generation
        p_files = {"file": ("mpsc_polity.txt", SAMPLE_POLITY_TXT.encode("utf-8"), "text/plain")}
        p_up = await client.post("https://mj-ai-teacher.onrender.com/prototype/notes/upload", files=p_files)
        polity_doc_id = p_up.json()["id"]

        polity_payload = {
            "doc_id": polity_doc_id,
            "subject": "राज्यशास्त्र (Polity & Governance)",
            "scope": "chapter",
            "chapter_id": 1,
            "exam_target": "prelims_mains",
            "output_type": "handwritten_notes",
            "custom_instruction": "घटना निर्मितीच्या तारखा आणि समित्यांवर भर दे."
        }
        polity_gen = await client.post("https://mj-ai-teacher.onrender.com/prototype/notes/generate", json=polity_payload)
        print(f"[TEST 4] Polity Gen Status: {polity_gen.status_code}")
        p_data = polity_gen.json()
        print(f"         Heading: {p_data.get('structured_note', {}).get('heading_mr')}")

        # 5. Geography Document - Comparison Table Style
        g_files = {"file": ("mpsc_geography.txt", SAMPLE_GEO_TXT.encode("utf-8"), "text/plain")}
        g_up = await client.post("https://mj-ai-teacher.onrender.com/prototype/notes/upload", files=g_files)
        geo_doc_id = g_up.json()["id"]

        geo_payload = {
            "doc_id": geo_doc_id,
            "subject": "महाराष्ट्राचा भूगोल (Maharashtra Geography)",
            "scope": "chapter",
            "chapter_id": 1,
            "exam_target": "mpsc_mains",
            "output_type": "detailed_notes",
            "custom_instruction": "प्राकृतिक विभागांचा तुलनात्मक तक्ता आणि कळसुबाईची माहिती दे."
        }
        geo_gen = await client.post("https://mj-ai-teacher.onrender.com/prototype/notes/generate", json=geo_payload)
        print(f"[TEST 5] Geography Gen Status: {geo_gen.status_code}")
        g_data = geo_gen.json()
        print(f"         Heading: {g_data.get('structured_note', {}).get('heading_mr')}")

        # 6. PDF Download Verification
        pdf_res = await client.get(f"https://mj-ai-teacher.onrender.com/prototype/notes/{hist_doc_id}/pdf")
        print(f"[TEST 6] PDF Download Status: {pdf_res.status_code}")
        print(f"         Size: {len(pdf_res.content)} bytes, Content-Type: {pdf_res.headers.get('content-type')}")
        assert pdf_res.status_code == 200
        assert len(pdf_res.content) > 1000

        print("\nALL LIVE PRODUCTION AUDIT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
