from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.schema import User, RevisionItem
from app.schemas.pydantic_models import (
    RevisionItemCreate, RevisionReviewSubmit,
    RevisionItemResponse, RevisionSummaryResponse
)
from app.services.progress.spaced_repetition import spaced_repetition_service

router = APIRouter(tags=["Spaced Repetition & Revision"])

@router.get("/revision/summary", response_model=RevisionSummaryResponse)
async def get_revision_summary(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """
    Returns counts of total, due today, and mastered revision cards strictly from real user database records.
    Fresh user returns 0 items.
    """
    all_res = await db.execute(select(RevisionItem).where(RevisionItem.user_id == user_id))
    items = all_res.scalars().all()

    now = datetime.utcnow()
    due_items = [i for i in items if i.next_review_due <= now]
    mastered_items = [i for i in items if i.confidence_level >= 4]

    due_response = [
        RevisionItemResponse(
            id=i.id,
            title=i.title,
            key_fact=i.key_fact,
            subject_name=i.subject_name,
            topic_name=i.topic_name,
            source_book=i.source_book,
            source_page=i.source_page,
            repetition_count=i.repetition_count,
            interval_days=i.interval_days,
            confidence_level=i.confidence_level,
            last_reviewed=i.last_reviewed,
            next_review_due=i.next_review_due,
            is_due=True
        )
        for i in due_items
    ]

    return RevisionSummaryResponse(
        total_items=len(items),
        due_today_count=len(due_items),
        mastered_count=len(mastered_items),
        due_items=due_response
    )

@router.post("/revision/add", response_model=RevisionItemResponse)
async def add_revision_item(data: RevisionItemCreate, user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """
    Creates a new key fact card for spaced repetition.
    """
    item = RevisionItem(
        user_id=user_id,
        title=data.title,
        key_fact=data.key_fact,
        subject_name=data.subject_name,
        topic_name=data.topic_name,
        source_book=data.source_book,
        source_page=data.source_page,
        next_review_due=datetime.utcnow()
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return RevisionItemResponse(
        id=item.id,
        title=item.title,
        key_fact=item.key_fact,
        subject_name=item.subject_name,
        topic_name=item.topic_name,
        source_book=item.source_book,
        source_page=item.source_page,
        repetition_count=item.repetition_count,
        interval_days=item.interval_days,
        confidence_level=item.confidence_level,
        last_reviewed=item.last_reviewed,
        next_review_due=item.next_review_due,
        is_due=True
    )

@router.post("/revision/review", response_model=RevisionItemResponse)
async def review_revision_item(data: RevisionReviewSubmit, db: AsyncSession = Depends(get_db)):
    """
    Submits SM-2 review rating (1-5) and updates next repetition schedule.
    """
    res = await db.execute(select(RevisionItem).where(RevisionItem.id == data.item_id))
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="घटक सापडला नाही.")

    rep_count, interval, ease, next_due = spaced_repetition_service.calculate_next_review(
        rating=data.rating,
        repetition_count=item.repetition_count,
        interval_days=item.interval_days,
        ease_factor=item.ease_factor
    )

    item.repetition_count = rep_count
    item.interval_days = interval
    item.ease_factor = ease
    item.confidence_level = data.rating
    item.last_reviewed = datetime.utcnow()
    item.next_review_due = next_due

    if data.rating >= 3:
        item.correct_count += 1
    else:
        item.incorrect_count += 1

    await db.commit()
    await db.refresh(item)

    return RevisionItemResponse(
        id=item.id,
        title=item.title,
        key_fact=item.key_fact,
        subject_name=item.subject_name,
        topic_name=item.topic_name,
        source_book=item.source_book,
        source_page=item.source_page,
        repetition_count=item.repetition_count,
        interval_days=item.interval_days,
        confidence_level=item.confidence_level,
        last_reviewed=item.last_reviewed,
        next_review_due=item.next_review_due,
        is_due=item.next_review_due <= datetime.utcnow()
    )
