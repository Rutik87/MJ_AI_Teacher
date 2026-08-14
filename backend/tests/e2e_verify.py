import asyncio
import os
import sys
from pathlib import Path

# Configure UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from httpx import AsyncClient, ASGITransport
import fitz
from app.main import app
from app.database import init_db
from app.models.schema import Book, ProcessingStatus
from app.database import SyncSessionLocal
from app.api.books import _background_process_pdf

async def run_e2e_test():
    print("=== [1/6] Initializing Database ===")
    await init_db()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/api/health")
        print(f"Health Status: {res.status_code}, data: {res.json()}")
        assert res.status_code == 200

        # 2. Create sample MPSC PDF
        print("\n=== [2/6] Generating Sample MPSC Marathi History PDF ===")
        sample_pdf_path = Path(backend_dir) / "tests" / "mpsc_sample_history.pdf"
        font_path = "C:/Windows/Fonts/Nirmala.ttf"
        if not Path(font_path).exists():
            font_path = "C:/Windows/Fonts/mangal.ttf"
        if not Path(font_path).exists():
            font_path = "C:/Windows/Fonts/arial.ttf"

        doc = fitz.open()
        p1 = doc.new_page()
        text_p1 = (
            "Chapter 1: Maharashtra Social Reformers - Satyashodhak Samaj\n\n"
            "सत्यशोधक समाजाची स्थापना (Satyashodhak Samaj was founded) on 24 September 1873 by Mahatma Jyotirao Phule in Pune.\n"
            "The motto of Satyashodhak Samaj was: Sarvasakshi Jagatpati, Tyala Nakocha Madhyasthi.\n"
            "Krushnarao Bhalekar started the Deenbandhu newspaper on 1 January 1877 as the official organ of Satyashodhak Samaj."
        )
        p1.insert_text((50, 72), text_p1)

        p2 = doc.new_page()
        text_p2 = (
            "Chapter 2: 1857 Revolt in Maharashtra (१८५७ चा उठाव)\n\n"
            "In the 1857 revolt, Rango Bapuji Gupte was the chief strategist in Satara.\n"
            "In Kolhapur, the 27th Native Infantry soldiers revolted under Ramji Shirsat.\n"
            "In Khandesh, Bhil leaders Kajising and Bhagoji Naik fought against the British."
        )
        p2.insert_text((50, 72), text_p2)

        doc.save(str(sample_pdf_path))
        doc.close()
        print(f"Sample PDF created at {sample_pdf_path}")

        # 3. Process & Index PDF directly
        print("\n=== [3/6] Indexing Book & Building Vector Embeddings ===")
        db = SyncSessionLocal()
        book = Book(
            title="महाराष्ट्राचा आधुनिक इतिहास (MPSC संदर्भ)",
            original_filename="mpsc_sample_history.pdf",
            file_path=str(sample_pdf_path),
            subject_name="महाराष्ट्राचा इतिहास",
            total_pages=2,
            status=ProcessingStatus.PENDING
        )
        db.add(book)
        db.commit()
        db.refresh(book)
        book_id = book.id
        db.close()

        # Run extraction & indexing
        _background_process_pdf(book_id, str(sample_pdf_path))

        # Check status via API
        stat_res = await client.get(f"/api/books/{book_id}/status")
        print(f"Book Status API: {stat_res.json()}")
        assert stat_res.json()["is_indexed"] == True

        # 4. Ask AI a Question in Marathi (RAG Verification)
        print("\n=== [4/6] Querying MPSC AI Teacher in Marathi with RAG ===")
        chat_res = await client.post("/api/chat/message", json={
            "message": "Satyashodhak Samaj ची स्थापना कोणी केली व त्यांचे मुखपत्र कोणते होते?",
            "mode": "general_chat"
        })
        chat_data = chat_res.json()
        print(f"\nAI Response:\n{chat_data['message']}")
        print(f"\nCitations Found: {len(chat_data['sources'])}")
        for c in chat_data['sources']:
            print(f" - Book: {c['book_name']}, Page: {c['page_number']}, Snippet: {c['text_snippet'][:80]}...")
        assert len(chat_data['sources']) > 0

        # 5. Teacher Mode Progressive Lesson
        print("\n=== [5/6] Testing Teacher Mode Progressive Lesson ===")
        teacher_res = await client.post("/api/teacher/teach", json={
            "topic": "1857 Revolt in Maharashtra",
            "subject": "महाराष्ट्राचा इतिहास",
            "difficulty": "medium"
        })
        t_data = teacher_res.json()
        print(f"\nTeacher Mode Output (Snippet):\n{t_data['lesson_markdown'][:300]}...\n")
        assert len(t_data['sources']) > 0

        # 6. MCQ Generator & Test Creation
        print("\n=== [6/6] Generating MCQs & Submitting Test ===")
        mcq_res = await client.post("/api/tests/generate-mcqs", json={
            "subject_name": "महाराष्ट्राचा इतिहास",
            "count": 3,
            "difficulty": "medium"
        })
        mcqs = mcq_res.json()
        print(f"Generated {len(mcqs)} MCQs:")
        for idx, m in enumerate(mcqs, 1):
            print(f" Q{idx}: {m['question_text']}")
            print(f"   (A) {m['option_a']} | Correct: {m['correct_option']}")
            print(f"   Exp: {m['explanation_mr'][:80]}...")

        # Create interactive test
        test_create = await client.post("/api/tests/create", json={
            "title": "महाराष्ट्राचा इतिहास सराव",
            "subject_name": "महाराष्ट्राचा इतिहास",
            "count": 3
        })
        test_data = test_create.json()
        test_id = test_data["test_id"]
        print(f"\nCreated Test ID: {test_id}, Total Questions: {test_data['total_questions']}")

        # Submit answers
        submit_res = await client.post("/api/tests/submit", json={
            "test_id": test_id,
            "answers": [
                {"question_id": test_data["questions"][0]["question_id"], "selected_option": test_data["questions"][0]["correct_option"]},
                {"question_id": test_data["questions"][1]["question_id"], "selected_option": test_data["questions"][1]["correct_option"]},
                {"question_id": test_data["questions"][2]["question_id"], "selected_option": "D"},
            ],
            "time_taken_seconds": 120
        })
        result_data = submit_res.json()
        print(f"Test Score: {result_data['score']}/{result_data['total_questions']} (Accuracy: {result_data['accuracy_percentage']}%)")

        print("\n🎉 ALL E2E WORKFLOW TESTS PASSED SUCCESSFULLY! 🎉")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
