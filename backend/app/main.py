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
    teacher_router,
    tests_router,
    revision_router,
    progress_router,
    voice_router,
    settings_router,
    current_affairs_router,
    mj_router,
    sync_router
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
    description="Personal MPSC AI Teacher, PDF Library, and Exam Preparation Platform",
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

# Mount Routers
app.include_router(books_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(teacher_router, prefix=settings.API_PREFIX)
app.include_router(tests_router, prefix=settings.API_PREFIX)
app.include_router(revision_router, prefix=settings.API_PREFIX)
app.include_router(progress_router, prefix=settings.API_PREFIX)
app.include_router(voice_router, prefix=settings.API_PREFIX)
app.include_router(settings_router, prefix=settings.API_PREFIX)
app.include_router(current_affairs_router, prefix=settings.API_PREFIX)
app.include_router(mj_router, prefix=settings.API_PREFIX)
app.include_router(sync_router, prefix=settings.API_PREFIX)

# Mount Voice Cloning Evaluation Lab
from voice_lab.lab_server import router as voice_lab_router
from fastapi.responses import FileResponse
from pathlib import Path

app.include_router(voice_lab_router)

@app.get("/voice-lab")
async def serve_voice_lab():
    lab_html = Path("voice_lab/static/index.html")
    if lab_html.exists():
        return FileResponse(lab_html, media_type="text/html")
    return {"error": "Voice Lab interface not found"}

@app.get("/")
async def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "message": "नमस्कार! MPSC AI Study Assistant API कार्यरत आहे."
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
