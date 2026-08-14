import pytest
import fitz
from pathlib import Path
from app.services.pdf.extractor import pdf_extractor
from app.services.rag.chunker import chunker

@pytest.fixture
def sample_pdf_path(tmp_path):
    pdf_file = tmp_path / "test_mpsc_history.pdf"
    doc = fitz.open()
    
    # Page 1
    p1 = doc.new_page()
    # Check if Nirmala/Mangal/Arial Unicode font exists on Windows
    font_path = "C:/Windows/Fonts/Nirmala.ttf"
    if not Path(font_path).exists():
        font_path = "C:/Windows/Fonts/mangal.ttf"
    if not Path(font_path).exists():
        font_path = "C:/Windows/Fonts/arial.ttf"

    try:
        p1.insert_text((50, 72), "प्रकरण 1: महाराष्ट्रातील समाजसुधारक - सत्यशोधक समाज स्थापना १८७३", fontfile=font_path if Path(font_path).exists() else None)
    except Exception:
        p1.insert_text((50, 72), "Chapter 1: Maharashtra History - Satyashodhak Samaj 1873")
    
    # Page 2
    p2 = doc.new_page()
    try:
        p2.insert_text((50, 72), "प्रकरण 2: १८५७ चा उठाव व संघर्ष", fontfile=font_path if Path(font_path).exists() else None)
    except Exception:
        p2.insert_text((50, 72), "Chapter 2: 1857 Revolt in Maharashtra")
    
    doc.save(str(pdf_file))
    doc.close()
    return str(pdf_file)

def test_pdf_extraction(sample_pdf_path):
    result = pdf_extractor.process_pdf_file(sample_pdf_path)
    assert result["total_pages"] == 2
    assert len(result["pages"]) == 2
    assert len(result["pages"][0]["text"]) > 5

def test_chunker(sample_pdf_path):
    result = pdf_extractor.process_pdf_file(sample_pdf_path)
    chunks = chunker.chunk_book_pages(
        book_id=1,
        book_title="महाराष्ट्र इतिहास",
        subject_name="इतिहास",
        pages_data=result["pages"],
        chapters_data=result["chapters"]
    )
    assert len(chunks) >= 2
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["book_title"] == "महाराष्ट्र इतिहास"
