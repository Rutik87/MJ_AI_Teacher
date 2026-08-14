import pytest
from app.services.rag.vector_store import ModularVectorStore
from app.services.rag.retriever import RAGRetriever

def test_marathi_vector_search(tmp_path):
    store = ModularVectorStore(storage_path=str(tmp_path / "test_vec.json"))
    sample_chunks = [
        {
            "chunk_uuid": "c-1",
            "book_id": 1,
            "book_title": "महाराष्ट्राचा इतिहास",
            "subject_name": "इतिहास",
            "chapter_title": "समाजसुधारक",
            "page_number": 124,
            "chunk_index": 0,
            "text_content": "सत्यशोधक समाजाची स्थापना महात्मा ज्योतिराव फुले यांनी २४ सप्टेंबर १८७३ रोजी केली. 'दीनबंधू' हे त्यांचे मुखपत्र होते."
        },
        {
            "chunk_uuid": "c-2",
            "book_id": 2,
            "book_title": "भारतीय राज्यघटना",
            "subject_name": "राज्यशास्त्र",
            "chapter_title": "मूलभूत हक्क",
            "page_number": 64,
            "chunk_index": 0,
            "text_content": "कलम ३२ अन्वये घटनात्मक उपायांचा अधिकार दिला आहे. यात ५ प्रकारचे प्राधिकृत लेख (Writs) आहेत."
        }
    ]
    store.add_chunks(sample_chunks)

    # Search for Satyashodhak Samaj in Marathi
    results = store.search("सत्यशोधक समाजाची स्थापना कोणी केली", top_k=2)
    assert len(results) > 0
    top_chunk, score = results[0]
    assert top_chunk["book_id"] == 1
    assert top_chunk["page_number"] == 124
    assert score > 0.1

    # Search for Article 32 in Marathi
    results_polity = store.search("कलम ३२ मूलभूत हक्क", top_k=2)
    assert len(results_polity) > 0
    top_polity, score_p = results_polity[0]
    assert top_polity["book_id"] == 2
    assert top_polity["page_number"] == 64
