import pytest
import hashlib
import io
from app.services.storage.cloud_storage import CloudStorageService
from app.services.rag.vector_store import ModularVectorStore

@pytest.mark.asyncio
async def test_cloud_storage_local_fallback():
    service = CloudStorageService(bucket_name="test-mpsc-books")
    test_content = b"%PDF-1.4 test pdf content for MPSC AI Study Assistant"
    storage_path = "books/test_book.pdf"

    # 1. Calculate Checksum
    checksum = service.calculate_checksum(test_content)
    assert checksum == hashlib.sha256(test_content).hexdigest()

    # 2. Upload
    path = await service.upload_file(test_content, storage_path)
    assert path == storage_path

    # 3. File exists
    exists = await service.file_exists(storage_path)
    assert exists is True

    # 4. Download
    downloaded = await service.download_file(storage_path)
    assert downloaded == test_content

    # 5. Signed URL
    url = await service.get_signed_url(storage_path)
    assert len(url) > 0

    # 6. Delete
    deleted = await service.delete_file(storage_path)
    assert deleted is True
    assert await service.file_exists(storage_path) is False

def test_vector_store_persistence():
    vs = ModularVectorStore()
    sample_chunks = [
        {
            "chunk_uuid": "chunk_001",
            "book_id": 999,
            "book_title": "महाराष्ट्राचा इतिहास",
            "subject_name": "इतिहास",
            "chapter_title": "छत्रपती शिवाजी महाराज",
            "page_number": 12,
            "chunk_index": 0,
            "text_content": "छत्रपती शिवाजी महाराजांनी रयतेचे स्वराज्य स्थापन केले आणि अष्टप्रधान मंडळ स्थापन केले.",
            "char_count": 85
        },
        {
            "chunk_uuid": "chunk_002",
            "book_id": 999,
            "book_title": "महाराष्ट्राचा भूगोल",
            "subject_name": "भूगोल",
            "chapter_title": "सह्याद्री पर्वत",
            "page_number": 45,
            "chunk_index": 1,
            "text_content": "महाराष्ट्रातील सर्वोच्च शिखर कळसूबाई हे सह्याद्री पर्वतात अहमदनगर जिल्ह्यात आहे.",
            "char_count": 78
        }
    ]

    # Add chunks
    vs.add_chunks(sample_chunks)
    assert len(vs.chunks) >= 2

    # Search Marathi RAG query
    results = vs.search("कळसूबाई शिखर", top_k=2)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert "कळसूबाई" in top_chunk["text_content"]
    assert top_chunk["page_number"] == 45

    # Test delete
    vs.delete_book_chunks(999)
    remaining = [c for c in vs.chunks if c.get("book_id") == 999]
    assert len(remaining) == 0
