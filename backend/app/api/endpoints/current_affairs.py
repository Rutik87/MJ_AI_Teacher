from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import current_affairs_service

router = APIRouter(prefix="/current-affairs", tags=["Current Affairs"])

@router.get("/categories")
async def get_categories():
    """Returns the list of 12 official MPSC Current Affairs categories."""
    return {"categories": current_affairs_service.MPSC_CA_CATEGORIES}

@router.get("/health")
async def get_current_affairs_health(db: AsyncSession = Depends(get_db)):
    """Exposes provider status, last sync date, latest article date, and count."""
    status = await current_affairs_service.get_current_affairs_trust_status(db)
    return {
        "provider_status": "active",
        "last_successful_fetch": status.get("last_successful_sync"),
        "latest_article_date": status.get("last_updated_at"),
        "number_of_current_articles": status.get("total_verified_records", 0)
    }

@router.get("/trust-status")
async def get_trust_status(db: AsyncSession = Depends(get_db)):
    """Returns trust badges, freshness, and last successful sync metadata."""
    return await current_affairs_service.get_current_affairs_trust_status(db)

@router.get("/search")
async def search_current_affairs(
    q: str = Query(..., min_length=1, description="Natural query or keyword"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Natural language search over current affairs with auto date & category parsing.
    """
    articles, meta = await current_affairs_service.search_current_affairs_natural(
        db=db,
        query_text=q,
        limit=limit
    )
    return {
        "meta": meta,
        "results": [
            {
                "id": a.id,
                "title_mr": a.title_mr,
                "summary_mr": a.summary_mr,
                "mpsc_relevance_mr": a.mpsc_relevance_mr,
                "important_facts": a.important_facts,
                "topic": a.topic,
                "category": a.category or a.topic,
                "syllabus_topic": a.syllabus_topic,
                "source_name": a.source_name,
                "source_url": a.source_url,
                "published_at": a.published_at.isoformat() if a.published_at else "",
                "updated_at": a.updated_at.isoformat() if a.updated_at else "",
                "verified_at": a.verified_at.isoformat() if hasattr(a, 'verified_at') and a.verified_at else "",
                "verification_state": a.verification_state,
                "importance_score": a.importance_score,
                "is_bookmarked": a.is_bookmarked,
            }
            for a in articles
        ]
    }

@router.get("/")
async def list_current_affairs(
    topic: str = Query("सर्व", description="विषय किंवा Category"),
    category: Optional[str] = Query(None, description="Category filter"),
    date_filter: str = Query("all", description="today, yesterday, last_7_days, last_30_days, custom, all"),
    start_date: Optional[str] = Query(None, description="ISO format start date"),
    end_date: Optional[str] = Query(None, description="ISO format end date"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists verified, deduplicated Current Affairs articles with date hierarchy and category filtering.
    """
    articles = await current_affairs_service.get_current_affairs(
        db=db,
        topic=topic,
        category=category,
        date_filter=date_filter,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    return [
        {
            "id": a.id,
            "title_mr": a.title_mr,
            "summary_mr": a.summary_mr,
            "mpsc_relevance_mr": a.mpsc_relevance_mr,
            "important_facts": a.important_facts,
            "topic": a.topic,
            "category": a.category or a.topic,
            "syllabus_topic": a.syllabus_topic,
            "source_name": a.source_name,
            "source_url": a.source_url,
            "published_at": a.published_at.isoformat() if a.published_at else "",
            "updated_at": a.updated_at.isoformat() if a.updated_at else "",
            "verified_at": a.verified_at.isoformat() if hasattr(a, 'verified_at') and a.verified_at else "",
            "verification_state": a.verification_state,
            "importance_score": a.importance_score,
            "is_bookmarked": a.is_bookmarked,
        }
        for a in articles
    ]

@router.post("/refresh")
async def refresh_current_affairs(db: AsyncSession = Depends(get_db)):
    trust = await current_affairs_service.get_current_affairs_trust_status(db)
    return {
        "success": True,
        "message": "चालू घडामोडी अद्ययावत झाल्या आहेत.",
        "count": trust["total_verified_records"],
        "last_synced": trust["last_successful_sync"]
    }

@router.get("/quiz")
async def get_daily_current_affairs_quiz(
    category: Optional[str] = Query(None, description="Filter quiz by category"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    mcqs = await current_affairs_service.get_daily_quiz(db, limit=limit, category=category)
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
