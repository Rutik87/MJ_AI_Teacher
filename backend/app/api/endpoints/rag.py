"""
RAG Diagnostic and Health Endpoints.
"""

import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.schema import Book, DocumentChunk
from app.config import settings
from app.services.rag.vector_store import vector_store

router = APIRouter(prefix="/rag", tags=["RAG Diagnostics"])

@router.get("/health")
async def get_rag_health(db: AsyncSession = Depends(get_db)):
    """
    RAG Diagnostic health endpoint.
    Reports indexing readiness, total chunks, books, embedding provider, and vector store type.
    """
    books_res = await db.execute(select(Book))
    books = books_res.scalars().all()

    chunks_res = await db.execute(select(DocumentChunk))
    chunks = chunks_res.scalars().all()

    last_indexed = None
    if chunks:
        sorted_chunks = sorted(chunks, key=lambda c: c.created_at or datetime.datetime.min, reverse=True)
        if sorted_chunks and sorted_chunks[0].created_at:
            last_indexed = sorted_chunks[0].created_at.isoformat()

    return {
        "ready": len(chunks) > 0,
        "total_chunks": len(chunks),
        "total_books": len(books),
        "last_indexed_at": last_indexed or datetime.datetime.utcnow().isoformat(),
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "vector_store": "PostgreSQL pgvector / SQLite vector_store"
    }
