from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import current_affairs_service

router = APIRouter(prefix="/current-affairs", tags=["Current Affairs"])

@router.get("/")
async def list_current_affairs(
    topic: str = Query("सर्व", description="विषय फिल्टर"),
    db: AsyncSession = Depends(get_db)
):
    articles = await current_affairs_service.get_current_affairs(db, topic=topic)
    return [
        {
            "id": a.id,
            "title_mr": a.title_mr,
            "summary_mr": a.summary_mr,
            "mpsc_relevance_mr": a.mpsc_relevance_mr,
            "important_facts": a.important_facts,
            "topic": a.topic,
            "source_name": a.source_name,
            "source_url": a.source_url,
            "published_at": a.published_at.isoformat() if a.published_at else "",
            "updated_at": a.updated_at.isoformat() if a.updated_at else "",
            "verification_state": a.verification_state,
            "importance_score": a.importance_score,
            "is_bookmarked": a.is_bookmarked,
        }
        for a in articles
    ]

@router.post("/refresh")
async def refresh_current_affairs(db: AsyncSession = Depends(get_db)):
    articles = await current_affairs_service.refresh_current_affairs_data(db)
    return {
        "success": True,
        "message": "चालू घडामोडी अद्ययावत झाल्या आहेत.",
        "count": len(articles),
        "last_synced": "आताच अद्ययावत झाले"
    }

@router.get("/quiz")
async def get_daily_current_affairs_quiz(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    mcqs = await current_affairs_service.get_daily_quiz(db, limit=limit)
    return [
        {
            "id": q.id,
            "article_id": q.article_id,
            "question_mr": q.question_mr,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "correct_option": q.correct_option,
            "explanation_mr": q.explanation_mr,
        }
        for q in mcqs
    ]

@router.post("/{article_id}/bookmark")
async def toggle_bookmark(article_id: int, db: AsyncSession = Depends(get_db)):
    status = await current_affairs_service.toggle_article_bookmark(db, article_id)
    return {"id": article_id, "is_bookmarked": status}
