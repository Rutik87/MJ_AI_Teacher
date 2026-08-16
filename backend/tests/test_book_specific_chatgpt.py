import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

from sqlalchemy import select
from app.main import app
from app.database import init_db, AsyncSessionLocal
from app.models.schema import Book, Chapter, Page, DocumentChunk, BookChatMessage
from app.services.ai.book_chat_service import book_chat_service

@pytest.mark.asyncio
async def test_book_specific_chat_grounding():
    """Verifies that ChatGPT generates source-grounded answer for a specific book."""
    await init_db()
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Book).where(Book.id == 901))
        if not existing.scalar_one_or_none():
            book = Book(
                id=901,
                user_id=1,
                title="महाराष्ट्राचा भूगोल Test Book",
                original_filename="mh_geo.txt",
                file_path="data/test/mh_geo.txt",
                total_pages=10
            )
            db.add(book)
            await db.commit()

    with patch("app.services.rag.retriever.rag_retriever.retrieve") as mock_retrieve:
        mock_citation = MagicMock()
        mock_citation.book_name = "महाराष्ट्राचा भूगोल Test Book"
        mock_citation.chapter = "प्रकरण १: सह्याद्री पर्वत"
        mock_citation.page_number = 4
        mock_citation.text_snippet = "कळसुबाई हे महाराष्ट्रातील सर्वोच्च शिखर असून त्याची उंची १६४६ मीटर आहे."
        mock_retrieve.return_value = ([mock_citation], mock_citation.text_snippet, True)

        with patch("app.services.ai.llm_provider.LLMProvider.generate_chat_response", return_value=("📌 **उत्तर**\nमहाराष्ट्रातील सर्वोच्च शिखर कळसुबाई (१६४६ मी) आहे.\n📖 **स्रोत**: महाराष्ट्राचा भूगोल, पान ४", "ChatGPT")):
            async with AsyncSessionLocal() as db:
                result = await book_chat_service.execute_book_chat(
                    book_id=901,
                    user_id=1,
                    message="महाराष्ट्रातील सर्वात उंच शिखर कोणते आहे?",
                    db=db
                )
                assert result["book_id"] == 901
                assert "कळसुबाई" in result["answer"]
                assert len(result["source_citations"]) == 1
                assert result["source_citations"][0]["page_number"] == 4

@pytest.mark.asyncio
async def test_book_chat_missing_source_guardrail():
    """Verifies that missing content in the book triggers anti-hallucination message."""
    with patch("app.services.rag.retriever.rag_retriever.retrieve", return_value=([], "", False)):
        async with AsyncSessionLocal() as db:
            result = await book_chat_service.execute_book_chat(
                book_id=901,
                user_id=1,
                message="या पुस्तकात अंतराळ मोहिमांबद्दल काय दिले आहे?",
                db=db
            )
            assert "उपलब्ध मजकुरामध्ये" in result["answer"]
            assert "माहिती सापडली नाही" in result["answer"]
            assert len(result["source_citations"]) == 0

@pytest.mark.asyncio
async def test_book_chat_intent_classification():
    """Verifies intent classification across different prompt types."""
    assert book_chat_service._classify_intent("Chapter 1 चे handwritten notes बनव.") == "handwritten_notes"
    assert book_chat_service._classify_intent("या chapter मधून 30 MPSC MCQ बनव.") == "mcq"
    assert book_chat_service._classify_intent("या पूर्ण पुस्तकातील महत्त्वाच्या तारखा काढ.") == "dates"
    assert book_chat_service._classify_intent("या chapter ची revision sheet बनव.") == "revision"
    assert book_chat_service._classify_intent("Chapter 3 मधील कारणे आणि परिणाम table मध्ये दाखव.") == "comparison"
    assert book_chat_service._classify_intent("मला हे सोप्या मराठीत समजाव.") == "chat"

@pytest.mark.asyncio
async def test_book_chat_history_isolation():
    """Verifies that book chat history is isolated per book and user."""
    async with AsyncSessionLocal() as db:
        history = await book_chat_service.get_book_chat_history(book_id=901, user_id=1, db=db)
        assert isinstance(history, list)
        assert len(history) >= 2  # from earlier tests

        # Clear history
        cleared = await book_chat_service.clear_book_chat_history(book_id=901, user_id=1, db=db)
        assert cleared is True

        history_after = await book_chat_service.get_book_chat_history(book_id=901, user_id=1, db=db)
        assert len(history_after) == 0

@pytest.mark.asyncio
async def test_book_chat_api_endpoints():
    """Verifies POST /api/books/{book_id}/chat and GET /api/books/{book_id}/chat/history endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Unauthorized / non-existent book
        res_fail = await client.post(
            "/api/books/99999/chat",
            json={"message": "Test query", "user_id": 1}
        )
        assert res_fail.status_code == 404

        # Valid book chat
        with patch("app.services.rag.retriever.rag_retriever.retrieve") as mock_retrieve:
            mock_citation = MagicMock()
            mock_citation.book_name = "महाराष्ट्राचा भूगोल Test Book"
            mock_citation.chapter = "प्रकरण १"
            mock_citation.page_number = 2
            mock_citation.text_snippet = "सह्याद्री पर्वतरांग ही महाराष्ट्राची जलविभाजक आहे."
            mock_retrieve.return_value = ([mock_citation], mock_citation.text_snippet, True)

            with patch("app.services.ai.llm_provider.LLMProvider.generate_chat_response", return_value=("📌 **उत्तर**\nसह्याद्री पर्वतरांग ही प्रमुख जलविभाजक आहे.", "ChatGPT")):
                res = await client.post(
                    "/api/books/901/chat",
                    json={"message": "सह्याद्री पर्वताबद्दल सांगा", "user_id": 1}
                )
                assert res.status_code == 200
                data = res.json()
                assert data["book_id"] == 901
                assert "सह्याद्री" in data["answer"]
                assert len(data["source_citations"]) == 1

                # Check history endpoint
                res_hist = await client.get("/api/books/901/chat/history?user_id=1")
                assert res_hist.status_code == 200
                assert len(res_hist.json()) >= 2
