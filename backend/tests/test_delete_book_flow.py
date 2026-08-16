import pytest
import hashlib
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, delete
from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models.schema import Book, DocumentChunk, Bookmark, RevisionItem, Question, User, ProcessingStatus
from app.services.rag.vector_store import vector_store
from app.services.storage.cloud_storage import cloud_storage

@pytest.mark.asyncio
async def test_complete_delete_book_workflow():
    await init_db()

    async with AsyncSessionLocal() as session:
        # Create users
        u1 = await session.execute(select(User).where(User.id == 1))
        if not u1.scalar_one_or_none():
            session.add(User(id=1, username="user_1"))
        u2 = await session.execute(select(User).where(User.id == 2))
        if not u2.scalar_one_or_none():
            session.add(User(id=2, username="user_2"))
        await session.commit()

        # Step 1: Upload / Create Test Book for User 1
        test_content = b"%PDF-1.4 sample content for complete delete verification"
        storage_path = "books/test_delete_verify.pdf"
        await cloud_storage.upload_file(test_content, storage_path)
        assert await cloud_storage.file_exists(storage_path) is True

        checksum = hashlib.sha256(test_content).hexdigest()
        book = Book(
            user_id=1,
            title="महाराष्ट्राचा भूगोल संदर्भ",
            original_filename="geo_test.pdf",
            file_path="/tmp/geo_test.pdf",
            storage_path=storage_path,
            checksum=checksum,
            subject_name="भूगोल",
            status=ProcessingStatus.COMPLETED,
            progress_percent=100.0,
            total_chunks=2
        )
        session.add(book)
        await session.commit()
        await session.refresh(book)
        book_id = book.id

        # Add Document Chunks
        chunk1 = DocumentChunk(
            chunk_uuid=f"chunk_{book_id}_0",
            book_id=book_id,
            chunk_index=0,
            page_number=1,
            subject_name="भूगोल",
            book_title="महाराष्ट्राचा भूगोल संदर्भ",
            text_content="सह्याद्री पर्वतरांगेतील सर्वोच्च शिखर कळसुबाई आहे (१६४६ मीटर).",
            char_count=60
        )
        chunk2 = DocumentChunk(
            chunk_uuid=f"chunk_{book_id}_1",
            book_id=book_id,
            chunk_index=1,
            page_number=2,
            subject_name="भूगोल",
            book_title="महाराष्ट्राचा भूगोल संदर्भ",
            text_content="गोदावरी नदी महाराष्ट्रातील सर्वात लांब नदी आहे.",
            char_count=50
        )
        session.add_all([chunk1, chunk2])

        # Add Bookmarks & Revision Items & Questions
        bm = Bookmark(user_id=1, title="कळसुबाई", content="कळसुबाई शिखर १६४६ मी", source_book="महाराष्ट्राचा भूगोल संदर्भ")
        rev = RevisionItem(user_id=1, title="कळसुबाई", key_fact="१६४६ मी", source_book="महाराष्ट्राचा भूगोल संदर्भ")
        q = Question(
            source_book_name="महाराष्ट्राचा भूगोल संदर्भ",
            question_text="कळसुबाई शिखराची उंची किती आहे?",
            option_a="१६४६ मी",
            option_b="१००० मी",
            option_c="१२०० मी",
            option_d="१४०० मी",
            correct_option="A"
        )
        session.add_all([bm, rev, q])
        await session.commit()

        # Add chunks to in-memory RAG vector store
        vector_store.add_chunks([
            {"chunk_uuid": f"del_{book_id}_0", "book_id": book_id, "book_title": book.title, "text_content": chunk1.text_content, "page_number": 1},
            {"chunk_uuid": f"del_{book_id}_1", "book_id": book_id, "book_title": book.title, "text_content": chunk2.text_content, "page_number": 2},
        ])

        # Verify RAG can find the chunk
        rag_res = vector_store.search("कळसुबाई शिखराची उंची", top_k=2)
        assert len(rag_res) > 0
        assert any(r[0]["book_id"] == book_id for r in rag_res)

    # Step 2: Test Security / Unauthorized Delete (User 2 attempts delete)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        unauthorized_res = await client.delete(f"/api/books/{book_id}?user_id=2")
        assert unauthorized_res.status_code == 403

    # Step 3: Test Authorized Delete (User 1 deletes)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        delete_res = await client.delete(f"/api/books/{book_id}?user_id=1")
        assert delete_res.status_code == 200
        del_data = delete_res.json()
        assert del_data["success"] is True
        assert del_data["book_id"] == book_id

    # Step 4: Verify Database Deletion & Cascades
    async with AsyncSessionLocal() as session:
        # Book is gone
        b_check = await session.execute(select(Book).where(Book.id == book_id))
        assert b_check.scalar_one_or_none() is None

        # Document Chunks are gone
        c_check = await session.execute(select(DocumentChunk).where(DocumentChunk.book_id == book_id))
        assert len(c_check.scalars().all()) == 0

        # Bookmarks are gone
        bm_check = await session.execute(select(Bookmark).where(Bookmark.source_book == "महाराष्ट्राचा भूगोल संदर्भ"))
        assert len(bm_check.scalars().all()) == 0

        # Revision items are cleaned
        rev_check = await session.execute(select(RevisionItem).where(RevisionItem.source_book == "महाराष्ट्राचा भूगोल संदर्भ"))
        assert len(rev_check.scalars().all()) == 0

        # Questions are gone
        q_check = await session.execute(select(Question).where(Question.source_book_name == "महाराष्ट्राचा भूगोल संदर्भ"))
        assert len(q_check.scalars().all()) == 0

    # Step 5: Verify Storage Deletion
    assert await cloud_storage.file_exists(storage_path) is False

    # Step 6: Verify In-Memory Vector Store RAG exclusion
    rag_after = vector_store.search("कळसुबाई शिखराची उंची", top_k=5)
    assert not any(r[0]["book_id"] == book_id for r in rag_after)

    # Step 7: Verify Idempotent Second Delete (Returns 404 cleanly, no 500)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        repeat_res = await client.delete(f"/api/books/{book_id}?user_id=1")
        assert repeat_res.status_code == 404
