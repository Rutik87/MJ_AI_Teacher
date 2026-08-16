import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.api import (
    books_router,
    chat_router,
    settings_router,
    schedule_router,
    rag_router
)
from app.utils.logger import logger
from app.services.rag.vector_store import vector_store
from app.services.storage.cloud_storage import cloud_storage

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing MPSC AI Study Assistant database...")
    await init_db()
    logger.info("Database schema initialized successfully.")
    
    # Initialize durable cloud storage bucket and restore vector index from DB
    await cloud_storage.ensure_bucket_exists()
    await vector_store.load_from_db()
    
    yield
    logger.info("MPSC AI Study Assistant shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="MPSC AI v1.0 Workspace: Files, ChatGPT Chat & Schedule Analyzer",
    lifespan=lifespan
)

# CORS middleware for mobile, web, and desktop clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Core Routers: 1. Files & Storage (books) | 2. ChatGPT (chat)
#               3. Schedule (schedule)     | 4. Settings (settings)
#               5. RAG Diagnostic (rag)
# ============================================================
app.include_router(books_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(schedule_router, prefix=settings.API_PREFIX)
app.include_router(settings_router, prefix=settings.API_PREFIX)
app.include_router(rag_router, prefix=settings.API_PREFIX)

@app.get("/")
async def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "message": "नमस्कार! MPSC AI v1.0 कार्यरत आहे. (1. 📚 Files | 2. 🤖 ChatGPT | 3. 🗓️ Schedule)"
    }

@app.get("/api/health")
async def health_check():
    db_status = "connected"
    overall_status = "healthy"
    try:
        from app.database import async_engine
        from sqlalchemy import text
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"disconnected ({e})"
        overall_status = "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "rag_ready": bool(vector_store is not None and db_status == "connected"),
        "total_chunks_indexed": len(vector_store.chunks) if vector_store else 0,
        "version": settings.VERSION
    }
