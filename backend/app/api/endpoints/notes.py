"""
REST API Endpoints for AI Handwritten Notes Generator.
Supports generation, preview, PDF download, Markdown download, and deletion.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.schema import Book, HandwrittenNote, User
from app.services.notes.note_generator_service import note_generator_service
from app.utils.logger import logger

router = APIRouter(prefix="/notes", tags=["AI Handwritten Notes Generator"])

@router.get("/health")
async def get_notes_health(db: AsyncSession = Depends(get_db)):
    """Diagnostic health check for Handwritten Notes engine."""
    q = select(HandwrittenNote)
    res = await db.execute(q)
    notes = res.scalars().all()
    ready_count = sum(1 for n in notes if n.status == "ready")
    return {
        "status": "active",
        "total_notes": len(notes),
        "ready_notes": ready_count,
        "pdf_engine": "ReportLab 4.0 (Devanagari Authentic Ruled Sheet)"
    }

@router.get("/all")
async def list_all_user_notes(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """Lists all generated handwritten notes for the user."""
    q = select(HandwrittenNote).where(HandwrittenNote.user_id == user_id).order_by(HandwrittenNote.created_at.desc())
    res = await db.execute(q)
    notes = res.scalars().all()
    return [
        {
            "id": n.id,
            "book_id": n.book_id,
            "status": n.status,
            "title": n.title,
            "page_count": n.page_count,
            "chapter_count": n.chapter_count or len(n.content_json or []),
            "has_pdf": bool(n.pdf_path),
            "created_at": n.created_at.isoformat() if n.created_at else None
        }
        for n in notes
    ]

@router.post("/generate/{book_id}")
async def generate_handwritten_notes(
    book_id: int,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyzes the complete uploaded PDF/TXT content and generates
    structured, exam-oriented Marathi handwritten-style notes.
    """
    # 1. Ownership & Book verification
    book_res = await db.execute(
        select(Book).where(Book.id == book_id, Book.user_id == user_id)
    )
    book = book_res.scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="पुस्तक सापडले नाही किंवा आपल्याला परवानगी नाही."
        )

    # 2. Get or create note record
    note_res = await db.execute(
        select(HandwrittenNote).where(HandwrittenNote.book_id == book_id, HandwrittenNote.user_id == user_id)
    )
    note = note_res.scalar_one_or_none()

    if not note:
        note = HandwrittenNote(
            user_id=user_id,
            book_id=book_id,
            title=f"{book.title} - Handwritten Notes",
            status="reading",
            progress_percent=10.0,
            progress_message="Content वाचत आहे..."
        )
        db.add(note)
        await db.commit()
        await db.refresh(note)

    # Callback to update note progress in DB
    async def on_progress(state_code: str, pct: float, msg: str):
        note.status = state_code
        note.progress_percent = pct
        note.progress_message = msg
        await db.commit()

    try:
        result = await note_generator_service.generate_notes_for_book(
            book_id=book_id,
            user_id=user_id,
            db=db,
            progress_callback=on_progress
        )

        note.status = "completed"
        note.progress_percent = 100.0
        note.progress_message = "Notes तयार आहेत 🎉"
        note.page_count = result["page_count"]
        note.chapter_count = result["chapter_count"]
        note.content_json = result["chapters"]
        note.markdown_content = result["markdown_content"]
        note.pdf_path = result["pdf_path"]
        note.pdf_url = result["pdf_url"]
        note.error_message = None

        await db.commit()
        await db.refresh(note)

        return {
            "status": "success",
            "message": "Handwritten Notes यशस्वीरित्या तयार झाल्या आहेत.",
            "note_id": note.id,
            "book_id": book.id,
            "title": note.title,
            "chapter_count": note.chapter_count,
            "page_count": note.page_count,
            "pdf_url": note.pdf_url,
            "chapters": note.content_json,
            "markdown_content": note.markdown_content
        }

    except Exception as e:
        logger.error(f"[NotesAPI] Generation failed for book {book_id}: {e}", exc_info=True)
        note.status = "failed"
        note.progress_message = "Notes तयार करताना त्रुटी आली."
        note.error_message = str(e)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Notes तयार करताना त्रुटी आली: {e}"
        )

@router.get("/{book_id}")
async def get_handwritten_notes_status(
    book_id: int,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns current generation status, chapters, and download links for the book's notes.
    """
    # 1. Ownership & Book verification
    book_res = await db.execute(
        select(Book).where(Book.id == book_id, Book.user_id == user_id)
    )
    book = book_res.scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="पुस्तक सापडले नाही."
        )

    note_res = await db.execute(
        select(HandwrittenNote).where(HandwrittenNote.book_id == book_id, HandwrittenNote.user_id == user_id)
    )
    note = note_res.scalar_one_or_none()

    if not note:
        return {
            "status": "not_generated",
            "book_id": book_id,
            "has_notes": False,
            "progress_percent": 0.0,
            "progress_message": "Notes अजून तयार केलेल्या नाहीत."
        }

    return {
        "status": note.status,
        "book_id": note.book_id,
        "note_id": note.id,
        "has_notes": note.status == "completed",
        "title": note.title,
        "progress_percent": note.progress_percent,
        "progress_message": note.progress_message,
        "chapter_count": note.chapter_count,
        "page_count": note.page_count,
        "pdf_url": note.pdf_url,
        "chapters": note.content_json or [],
        "markdown_content": note.markdown_content or "",
        "error_message": note.error_message,
        "generated_at": note.generated_at
    }

@router.get("/{book_id}/download")
async def download_handwritten_notes_pdf(
    book_id: int,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """
    Serves the generated high-resolution notebook PDF file.
    """
    note_res = await db.execute(
        select(HandwrittenNote).where(HandwrittenNote.book_id == book_id, HandwrittenNote.user_id == user_id)
    )
    note = note_res.scalar_one_or_none()

    if not note or not note.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="या पुस्तकासाठी PDF नोट्स उपलब्ध नाहीत."
        )

    file_path = Path(note.pdf_path)
    if not file_path.exists():
        # Check standard data path
        file_path = Path("data/notes") / f"notes_book_{book_id}.pdf"
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF फाईल सर्व्हरवर सापडली नाही."
        )

    ascii_filename = f"notes_book_{book_id}.pdf"
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=ascii_filename,
        headers={"Content-Disposition": f"inline; filename={ascii_filename}"}
    )

@router.get("/{book_id}/markdown")
async def download_handwritten_notes_markdown(
    book_id: int,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """
    Serves the raw Markdown / plain-text notes.
    """
    note_res = await db.execute(
        select(HandwrittenNote).where(HandwrittenNote.book_id == book_id, HandwrittenNote.user_id == user_id)
    )
    note = note_res.scalar_one_or_none()

    if not note or not note.markdown_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="मजकूर नोट्स उपलब्ध नाहीत."
        )

    return PlainTextResponse(
        content=note.markdown_content,
        media_type="text/markdown; charset=utf-8"
    )

@router.delete("/{book_id}")
async def delete_handwritten_notes(
    book_id: int,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes the generated handwritten notes and removes PDF artifacts from disk.
    """
    note_res = await db.execute(
        select(HandwrittenNote).where(HandwrittenNote.book_id == book_id, HandwrittenNote.user_id == user_id)
    )
    note = note_res.scalar_one_or_none()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="हटवण्यासाठी नोट्स सापडल्या नाहीत."
        )

    # Delete physical PDF file if present
    if note.pdf_path:
        try:
            p = Path(note.pdf_path)
            if p.exists():
                p.unlink()
        except Exception as e:
            logger.warning(f"[NotesAPI] Could not remove PDF file {note.pdf_path}: {e}")

    await db.delete(note)
    await db.commit()

    return {
        "status": "success",
        "message": "Handwritten Notes यशस्वीरित्या हटवण्यात आल्या आहेत.",
        "book_id": book_id
    }
