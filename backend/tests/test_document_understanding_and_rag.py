import pytest
from app.services.text.txt_extractor import txt_extractor
from app.services.rag.chunker import chunker
from app.services.rag.vector_store import vector_store
from app.services.rag.retriever import rag_retriever
from app.models.schema import Book, DocumentChunk

@pytest.mark.asyncio
async def test_rich_chunk_metadata_and_citations():
    txt_content = """# प्रकरण १: महाराष्ट्रातील नद्या व धरणे

गोदावरी नदी ही महाराष्ट्रातील सर्वात लांब नदी आहे. तिचा उगम नाशिक जिल्ह्यातील त्र्यंबकेश्वर येथे होतो.
गोदावरी नदीवर औरंगाबाद जिल्ह्यात जायकवाडी धरण (नाथसागर जलाशय) बांधण्यात आले आहे.

--- Page 2 ---
# प्रकरण २: कोयना जलविद्युत प्रकल्प

कोयना नदीवर सातारा जिल्ह्यातील कोयनानगर येथे कोयना धरण बांधण्यात आले आहे.
या धरणाच्या जलाशयाला 'शिवसागर जलाशय' म्हणतात. कोयना प्रकल्पाला महाराष्ट्राची 'भाग्यरेषा' मानले जाते.
"""
    # 1. Text extraction & page structuring
    pages_data, chapters_data = txt_extractor.extract_from_text(txt_content, title="महाराष्ट्र भूगोल व नद्या")
    assert len(pages_data) == 2
    assert len(chapters_data) == 2

    # 2. Chunker with rich metadata
    chunks = chunker.chunk_book_pages(
        book_id=999,
        book_title="महाराष्ट्र भूगोल व नद्या",
        subject_name="भूगोल",
        pages_data=pages_data,
        chapters_data=chapters_data
    )
    assert len(chunks) >= 2
    
    first_chunk = chunks[0]
    assert first_chunk["book_id"] == 999
    assert first_chunk["book_title"] == "महाराष्ट्र भूगोल व नद्या"
    assert first_chunk["subject_name"] == "भूगोल"
    assert first_chunk["page_number"] in [1, 2]
    assert "गोदावरी" in first_chunk["text_content"]

    # 3. Vector indexing & retrieval
    vector_store.add_chunks(chunks)
    
    citations, context_str, has_context = rag_retriever.retrieve(
        query="महाराष्ट्राची भाग्यरेषा कोणत्या प्रकल्पाला म्हणतात?",
        top_k=2,
        book_id=999
    )
    
    assert has_context is True
    assert len(citations) > 0
    assert citations[0].book_name == "महाराष्ट्र भूगोल व नद्या"
    assert "कोयना" in citations[0].chapter or "कोयना" in citations[0].text_snippet

    # 4. Cleanup
    vector_store.delete_book_chunks(999)
