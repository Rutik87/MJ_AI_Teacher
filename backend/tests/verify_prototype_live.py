import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(timeout=180.0) as client:
        # 1. HTML Prototype
        r = await client.get("https://mj-ai-teacher.onrender.com/prototype/notes")
        print(f"[1] HTML Prototype Status: {r.status_code}, Length: {len(r.text)} bytes")

        # 2. Upload text file
        sample_txt = """प्रकरण १: १८५७ चा राष्ट्रीय उठाव
२९ मार्च १८५७ रोजी मंगल पांडे यांनी बराकपूर छावणीत गायी व डुकराची चरबी लावलेल्या नव्या एनफिल्ड रायफलींच्या काडतुसांविरोधात सशस्त्र बंड पुकारले.
लॉर्ड डलहौसीचे दत्तक वारसा नामंजूर धोरण आणि संस्थाने खालसा करण्याचे धोरण या उठावाचे प्रमुख राजकीय कारण होते.
१० मे १८५७ रोजी मीरत छावणीतील सैनिकांनी उठाव करून दिल्लीकडे कूच केले आणि बहादूरशाह जफर यांना भारताचा सम्राट घोषित केले.
झाशीमध्ये राणी लक्ष्मीबाई, कानपूरमध्ये नानासाहेब पेशवे व तात्या टोपे, तर बिहारमध्ये कुंवरसिंह यांनी उठावाचे समर्थ नेतृत्व केले.

प्रकरण २: १८५८ चा राणीचा जाहीरनामा व कायदे
१ नोव्हेंबर १८५८ रोजी लॉर्ड कॅनिंगने अलाहाबाद दरबारात राणी व्हिक्टोरियाचा जाहीरनामा वाचून दाखवला.
या जाहीरनाम्याने ईस्ट इंडिया कंपनीची भारतातील राजवट संपुष्टात आली आणि ब्रिटिश संसदेकडे भारताची सत्ता हस्तांतरित झाली.
भारतासाठी राज्यसचिव (Secretary of State) हे नवे पद निर्माण करण्यात आले."""

        files = {"file": ("modern_india_test.txt", sample_txt.encode("utf-8"), "text/plain")}
        up_res = await client.post("https://mj-ai-teacher.onrender.com/prototype/notes/upload", files=files)
        print(f"[2] Upload Status: {up_res.status_code}")
        up_data = up_res.json()
        print(f"    Detected Chapters: {up_data['total_chapters']}")
        doc_id = up_data["id"]

        # 3. Generate Chapter Notes via ChatGPT
        gen_payload = {
            "doc_id": doc_id,
            "chapter_id": 1,
            "custom_instruction": "या अध्यायाचे MPSC साठी पूर्ण handwritten notes, timeline आणि points बनव."
        }
        gen_res = await client.post("https://mj-ai-teacher.onrender.com/prototype/notes/generate", json=gen_payload)
        print(f"[3] Generate Status: {gen_res.status_code}")
        if gen_res.status_code != 200:
            print(f"    Error text: {gen_res.text}")
        else:
            gen_data = gen_res.json()
            heading = gen_data.get('structured_note', {}).get('heading_mr', '')
            print(f"    Heading: {heading}")
            print(f"    Pages: {gen_data.get('page_count')}")
            print(f"    PDF URL: {gen_data.get('pdf_url')}")

        # 4. Download Generated PDF
        pdf_res = await client.get(f"https://mj-ai-teacher.onrender.com/prototype/notes/{doc_id}/pdf")
        print(f"[4] PDF Download Status: {pdf_res.status_code}")
        print(f"    PDF Size: {len(pdf_res.content)} bytes")
        print(f"    Content-Type: {pdf_res.headers.get('content-type')}")

if __name__ == "__main__":
    asyncio.run(main())
