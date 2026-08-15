import pytest
import os
import io
from pathlib import Path
from app.services.text.txt_extractor import txt_extractor
from app.services.rag.chunker import chunker
from app.services.rag.vector_store import ModularVectorStore
from app.utils.file_security import validate_pdf_file, validate_document_file
from fastapi import HTTPException

def test_txt_extractor_marathi_content():
    marathi_txt = """# प्रकरण १: महाराष्ट्राचा भूगोल

महाराष्ट्र हे भारतातील एक प्रमुख राज्य आहे. महाराष्ट्राची राजधानी मुंबई असून उपराजधानी नागपूर आहे.

--- Page 2 ---
# प्रकरण २: सह्याद्री पर्वत रांगा

सह्याद्री पर्वतातील सर्वोच्च शिखर कळसूबाई (१६४६ मीटर) आहे. हे अहमदनगर जिल्ह्यात आहे.
"""
    raw_bytes = marathi_txt.encode("utf-8")
    extracted_text = txt_extractor.decode_and_validate(raw_bytes)
    assert "महाराष्ट्राची राजधानी मुंबई" in extracted_text
    assert "कळसूबाई" in extracted_text

def test_txt_extractor_invalid_encoding_rejection():
    # Null bytes / binary data
    binary_data = b"Some text \x00 with null bytes binary"
    with pytest.raises(ValueError, match="binary data or null bytes detected"):
        txt_extractor.decode_and_validate(binary_data)

    # Empty content
    with pytest.raises(ValueError, match="empty or contains only whitespace"):
        txt_extractor.decode_and_validate(b"   \n\n  \t  ")

def test_txt_file_processing_and_chunking(tmp_path):
    test_file = tmp_path / "mpsc_notes.txt"
    test_content = """# प्रकरण १: १८५७ चा उठाव

१८५७ च्या उठावात महाराष्ट्रातून नानासाहेब पेशवे आणि तात्या टोपे यांनी नेतृत्व केले.
सातारा येथे रंगो बापूजी गुप्ते यांनी उठावाची योजना आखली.

--- Page 2 ---
# प्रकरण २: समाजसुधारक

महात्मा जोतीराव फुले यांनी १८७३ मध्ये सत्यशोधक समाजाची स्थापना केली.
त्यांनी १८४८ मध्ये पुण्यातील भिडे वाड्यात मुलींची पहिली शाळा सुरू केली.
"""
    test_file.write_text(test_content, encoding="utf-8")

    result = txt_extractor.process_txt_file(str(test_file))
    assert result["total_pages"] >= 2
    assert len(result["chapters"]) >= 2
    assert "१८५७ चा उठाव" in result["chapters"][0]["title"]

    # Chunking
    chunks = chunker.chunk_book_pages(
        book_id=101,
        book_title="MPSC History Notes",
        subject_name="इतिहास",
        pages_data=result["pages"],
        chapters_data=result["chapters"]
    )
    assert len(chunks) >= 2

    # Vector store indexing and search
    vstore = ModularVectorStore()
    vstore.add_chunks(chunks)

    search_results = vstore.search("सत्यशोधक समाज", top_k=2)
    assert len(search_results) > 0
    top_chunk, score = search_results[0]
    assert "सत्यशोधक समाज" in top_chunk["text_content"]
    assert top_chunk["book_id"] == 101

    # Delete chunks from vector store
    vstore.delete_book_chunks(101)
    assert len(vstore.search("सत्यशोधक समाज", top_k=2)) == 0

def test_validate_document_file_accepts_pdf_and_txt():
    # Valid PDF
    validate_document_file("history.pdf", "application/pdf", 1024)
    # Valid TXT
    validate_document_file("notes.txt", "text/plain", 1024)
    # Invalid extension
    with pytest.raises(HTTPException):
        validate_document_file("script.exe", "application/x-msdownload", 1024)
