import os
import shutil
import asyncio
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update

from app.database import get_db, SyncSessionLocal
from app.config import settings
from app.models.schema import Book, Subject, Chapter, Page, DocumentChunk, ProcessingStatus
from app.schemas.pydantic_models import (
    BookResponse, BookStatusResponse, BookRenameRequest,
    SubjectResponse, SubjectCreate
)
from app.utils.file_security import sanitize_filename, validate_pdf_file
from app.utils.logger import logger
from app.services.pdf.extractor import pdf_extractor
from app.services.rag.chunker import chunker
from app.services.rag.vector_store import vector_store

router = APIRouter(tags=["Books & Library"])

# Default MPSC Subjects
DEFAULT_SUBJECTS = [
    {"name_mr": "इतिहास", "name_en": "History", "icon": "history_edu", "color": "#E65100"},
    {"name_mr": "भूगोल", "name_en": "Geography", "icon": "public", "color": "#2E7D32"},
    {"name_mr": "राज्यशास्त्र", "name_en": "Polity", "icon": "account_balance", "color": "#1565C0"},
    {"name_mr": "अर्थशास्त्र", "name_en": "Economics", "icon": "trending_up", "color": "#C2185B"},
    {"name_mr": "महाराष्ट्राचा इतिहास", "name_en": "Maharashtra History", "icon": "fort", "color": "#D84315"},
    {"name_mr": "महाराष्ट्राचा भूगोल", "name_en": "Maharashtra Geography", "icon": "terrain", "color": "#388E3C"},
    {"name_mr": "महाराष्ट्र विशेष", "name_en": "Maharashtra Special", "icon": "star", "color": "#F57C00"},
    {"name_mr": "सामान्य विज्ञान", "name_en": "General Science", "icon": "science", "color": "#00838F"},
    {"name_mr": "पर्यावरण", "name_en": "Environment", "icon": "park", "color": "#558B2F"},
    {"name_mr": "चालू घडामोडी", "name_en": "Current Affairs", "icon": "newspaper", "color": "#6A1B9A"},
    {"name_mr": "सामान्य ज्ञान", "name_en": "General Knowledge", "icon": "lightbulb", "color": "#AD1457"},
    {"name_mr": "गणित", "name_en": "Mathematics", "icon": "calculate", "color": "#0277BD"},
    {"name_mr": "बुद्धिमत्ता", "name_en": "Reasoning", "icon": "psychology", "color": "#00695C"},
    {"name_mr": "PYQ", "name_en": "Previous Year Questions", "icon": "quiz", "color": "#4527A0"},
    {"name_mr": "Notes", "name_en": "Study Notes", "icon": "note_alt", "color": "#4E342E"},
    {"name_mr": "Other", "name_en": "Other Material", "icon": "folder", "color": "#37474F"}
]

@router.get("/subjects", response_model=List[SubjectResponse])
async def list_subjects(db: AsyncSession = Depends(get_db)):
    """
    Returns all standard and custom MPSC subjects.
    """
    result = await db.execute(select(Subject))
    subjects = result.scalars().all()
    
    # Initialize default subjects if DB is empty
    if not subjects:
        for s_data in DEFAULT_SUBJECTS:
            subj = Subject(
                name_mr=s_data["name_mr"],
                name_en=s_data["name_en"],
                icon=s_data["icon"],
                color=s_data["color"],
                is_custom=False
            )
            db.add(subj)
        await db.commit()
        result = await db.execute(select(Subject))
        subjects = result.scalars().all()

    return subjects

@router.post("/subjects", response_model=SubjectResponse)
async def create_custom_subject(data: SubjectCreate, db: AsyncSession = Depends(get_db)):
    """
    Creates a new custom study subject.
    """
    existing = await db.execute(select(Subject).where(Subject.name_mr == data.name_mr))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="हा विषय आधीच उपलब्ध आहे.")

    subj = Subject(
        name_mr=data.name_mr,
        name_en=data.name_en,
        icon=data.icon,
        color=data.color,
        is_custom=True
    )
    db.add(subj)
    await db.commit()
    await db.refresh(subj)
    return subj

def _background_process_pdf(book_id: int, file_path: str):
    """
    Background worker that runs PDF text extraction, OCR, chunking, and embedding.
    """
    db = SyncSessionLocal()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return

        book.status = ProcessingStatus.EXTRACTING
        book.status_message = "PDF मधील मजकूर काढत आहे..."
        book.progress_percent = 10.0
        db.commit()

        # Extract PDF content
        def on_page_progress(current_page, total_pages):
            pct = 10.0 + (current_page / max(total_pages, 1)) * 50.0
            book.progress_percent = round(pct, 1)
            book.current_page_processing = current_page
            book.total_pages = total_pages
            book.status_message = f"पान {current_page} / {total_pages} तपासत आहे..."
            db.commit()

        extracted_data = pdf_extractor.process_pdf_file(
            file_path=file_path,
            progress_callback=on_page_progress
        )

        book.total_pages = extracted_data["total_pages"]
        book.is_scanned = extracted_data["is_scanned"]
        book.status = ProcessingStatus.CHUNKING
        book.status_message = "अभ्यास घटकांचे विभाजन (Chunking) करत आहे..."
        book.progress_percent = 70.0
        db.commit()

        # Save Chapters
        for ch in extracted_data["chapters"]:
            chapter_rec = Chapter(
                book_id=book.id,
                title=ch["title"],
                start_page=ch["start_page"],
                end_page=ch["end_page"]
            )
            db.add(chapter_rec)
        db.commit()

        # Save Pages
        for p in extracted_data["pages"]:
            page_rec = Page(
                book_id=book.id,
                page_number=p["page_number"],
                extracted_text=p["text"],
                has_images=p["has_images"],
                is_ocr=p["is_ocr"],
                char_count=p["char_count"]
            )
            db.add(page_rec)
        db.commit()

        # Generate Chunks
        chunks = chunker.chunk_book_pages(
            book_id=book.id,
            book_title=book.title,
            subject_name=book.subject_name,
            pages_data=extracted_data["pages"],
            chapters_data=extracted_data["chapters"]
        )

        book.status = ProcessingStatus.EMBEDDING
        book.status_message = "शोध निर्देशांक (Search Index) तयार करत आहे..."
        book.progress_percent = 85.0
        db.commit()

        # Save chunks to DB
        for c in chunks:
            chunk_rec = DocumentChunk(
                chunk_uuid=c["chunk_uuid"],
                book_id=book.id,
                book_title=book.title,
                subject_name=book.subject_name,
                chapter_title=c["chapter_title"],
                page_number=c["page_number"],
                chunk_index=c["chunk_index"],
                text_content=c["text_content"],
                char_count=c["char_count"]
            )
            db.add(chunk_rec)
        db.commit()

        # Index in Vector Store
        vector_store.add_chunks(chunks)

        book.total_chunks = len(chunks)
        book.status = ProcessingStatus.COMPLETED
        book.status_message = "तयार आहे (Ready ✓)"
        book.progress_percent = 100.0
        book.is_indexed = True
        db.commit()
        logger.info(f"Successfully processed and indexed book id={book.id}, title='{book.title}', chunks={len(chunks)}")

    except Exception as e:
        logger.error(f"Error processing book id={book_id}: {e}")
        try:
            book = db.query(Book).filter(Book.id == book_id).first()
            if book:
                book.status = ProcessingStatus.FAILED
                book.status_message = f"प्रक्रियेत त्रुटी आली: {str(e)[:150]}"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()

@router.post("/books/upload", response_model=BookResponse)
async def upload_book(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    subject_name: Optional[str] = Form("इतिहास"),
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads a new PDF book, saves it to local disk, and starts background extraction and indexing.
    """
    filename = sanitize_filename(file.filename or "book.pdf")
    
    # Read file content to check size
    contents = await file.read()
    file_size = len(contents)
    validate_pdf_file(filename, file.content_type or "application/pdf", file_size)

    # Save to disk
    save_dir = Path(settings.BOOKS_PATH)
    save_path = save_dir / f"{int(asyncio.get_event_loop().time())}_{filename}"
    with open(save_path, "wb") as f:
        f.write(contents)

    book_title = title.strip() if title and title.strip() else Path(filename).stem

    # Find or link subject
    subj_res = await db.execute(select(Subject).where(Subject.name_mr == subject_name))
    subject = subj_res.scalar_one_or_none()

    book = Book(
        title=book_title,
        original_filename=filename,
        file_path=str(save_path),
        subject_id=subject.id if subject else None,
        subject_name=subject_name or "इतिहास",
        file_size_bytes=file_size,
        status=ProcessingStatus.PENDING,
        status_message="अपलोड झाले, प्रक्रिया सुरू होत आहे...",
        progress_percent=0.0
    )
    db.add(book)
    await db.commit()
    await db.refresh(book)

    # Launch background indexing
    background_tasks.add_task(_background_process_pdf, book.id, str(save_path))

    return book

@router.get("/books", response_model=List[BookResponse])
async def list_books(
    subject_name: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all uploaded books with optional subject filtering and keyword search.
    """
    query = select(Book).order_by(Book.created_at.desc())
    if subject_name and subject_name != "All":
        query = query.where(Book.subject_name == subject_name)
    
    result = await db.execute(query)
    books = result.scalars().all()

    if search and search.strip():
        s_lower = search.strip().lower()
        books = [b for b in books if s_lower in b.title.lower() or s_lower in (b.subject_name or "").lower()]

    return books

@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book_detail(book_id: int, db: AsyncSession = Depends(get_db)):
    """
    Returns details for a specific book.
    """
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="पुस्तक सापडले नाही.")
    return book

@router.get("/books/{book_id}/status", response_model=BookStatusResponse)
async def get_book_status(book_id: int, db: AsyncSession = Depends(get_db)):
    """
    Polls real-time PDF processing status and progress percentage.
    """
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="पुस्तक सापडले नाही.")

    return BookStatusResponse(
        id=book.id,
        title=book.title,
        status=book.status.value if hasattr(book.status, 'value') else str(book.status),
        status_message=book.status_message,
        progress_percent=book.progress_percent,
        current_page=book.current_page_processing,
        total_pages=book.total_pages,
        is_indexed=book.is_indexed
    )

@router.get("/books/{book_id}/pdf")
async def get_book_pdf(book_id: int, db: AsyncSession = Depends(get_db)):
    """
    Serves the raw PDF file for in-app reader viewing.
    """
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book or not os.path.exists(book.file_path):
        raise HTTPException(status_code=404, detail="PDF फाईल सापडली नाही.")

    return FileResponse(
        path=book.file_path,
        media_type="application/pdf",
        filename=book.original_filename
    )

@router.get("/books/{book_id}/pages/{page_num}")
async def get_page_text(book_id: int, page_num: int, db: AsyncSession = Depends(get_db)):
    """
    Gets extracted text for a specific page.
    """
    result = await db.execute(
        select(Page).where(Page.book_id == book_id, Page.page_number == page_num)
    )
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="पान सापडले नाही.")
    
    return {
        "book_id": book_id,
        "page_number": page_num,
        "text": page.extracted_text,
        "is_ocr": page.is_ocr,
        "char_count": page.char_count
    }

@router.patch("/books/{book_id}", response_model=BookResponse)
async def update_book(book_id: int, data: BookRenameRequest, db: AsyncSession = Depends(get_db)):
    """
    Renames book or changes its subject.
    """
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="पुस्तक सापडले नाही.")

    book.title = data.title.strip()
    if data.subject_name:
        book.subject_name = data.subject_name
    await db.commit()
    await db.refresh(book)
    return book

@router.delete("/books/{book_id}")
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """
    Deletes a book, its chunks, and vector index.
    """
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="पुस्तक सापडले नाही.")

    # Remove vector index
    vector_store.delete_book_chunks(book_id)

    # Remove file from disk
    if os.path.exists(book.file_path):
        try:
            os.remove(book.file_path)
        except Exception as e:
            logger.warning(f"Could not remove PDF file from disk: {e}")

    await db.delete(book)
    await db.commit()
    return {"message": "पुस्तक यशस्वीरित्या हटवले.", "book_id": book_id}

@router.post("/books/{book_id}/reindex")
async def reindex_book(book_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Re-runs extraction and vector indexing for a book.
    """
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if not book or not os.path.exists(book.file_path):
        raise HTTPException(status_code=404, detail="पुस्तक किंवा फाईल सापडली नाही.")

    # Clear old chunks from vector store
    vector_store.delete_book_chunks(book_id)

    # Delete existing pages, chapters, chunks in DB
    await db.execute(delete(DocumentChunk).where(DocumentChunk.book_id == book_id))
    await db.execute(delete(Page).where(Page.book_id == book_id))
    await db.execute(delete(Chapter).where(Chapter.book_id == book_id))
    
    book.status = ProcessingStatus.PENDING
    book.status_message = "पुन्हा इंडेक्सिंग सुरू करत आहे..."
    book.progress_percent = 0.0
    await db.commit()

    background_tasks.add_task(_background_process_pdf, book.id, book.file_path)
    return {"message": "इंडेक्सिंग प्रक्रिया सुरू झाली.", "book_id": book_id}
