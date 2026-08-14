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

DEFAULT_REVISION_SEEDS = [
    {
        "title": "सत्यशोधक समाज",
        "key_fact": "स्थापना: २४ सप्टेंबर १८७३, पुणे | संस्थापक: महात्मा ज्योतिराव फुले | वृत्तपत्र: 'दीनबंधू' (कृष्णराव भालेकर)",
        "subject_name": "महाराष्ट्राचा इतिहास",
        "topic_name": "समाजसुधारक",
        "source_book": "महाराष्ट्राचा इतिहास",
        "source_page": 124
    },
    {
        "title": "कलम ३२ - घटनात्मक उपायांचा अधिकार",
        "key_fact": "डॉ. आंबेडकरांनी या कलमाला 'घटनेचा आत्मा आणि हृदय' म्हटले आहे. ५ प्रकारचे प्राधिकृत लेख (Writs) काढण्याचा अधिकार सर्वोच्च न्यायालयाला मिळतो.",
        "subject_name": "राज्यशास्त्र",
        "topic_name": "मूलभूत हक्क",
        "source_book": "भारतीय राज्यघटना",
        "source_page": 64
    },
    {
        "title": "महाराष्ट्रातील प्रमुख नद्यांची लांबी",
        "key_fact": "गोदावरी: ६६८ किमी (महाराष्ट्र) | भीमा: ४५१ किमी | कृष्णा: २८२ किमी | तापी: २०८ किमी",
        "subject_name": "महाराष्ट्राचा भूगोल",
        "topic_name": "नदीप्रणाली",
        "source_book": "महाराष्ट्राचा भूगोल",
        "source_page": 42
    },
    {
        "title": "नीती आयोग (NITI Aayog)",
        "key_fact": "स्थापना: १ जानेवारी २०१५ (नियोजन आयोगाच्या जागी) | अध्यक्ष: पंतप्रधान | थिंक टँक म्हणून कार्य करते.",
        "subject_name": "अर्थशास्त्र",
        "topic_name": "नियोजन",
        "source_book": "भारतीय अर्थव्यवस्था",
        "source_page": 95
    }
]

@router.get("/revision/summary", response_model=RevisionSummaryResponse)
async def get_revision_summary(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """
    Returns counts of total, due today, and mastered revision cards.
    """
    # Ensure user exists and populate default seed cards if empty
    u_res = await db.execute(select(User).where(User.id == user_id))
    if not u_res.scalar_one_or_none():
        user = User(id=user_id, username="mpsc_aspirant")
        db.add(user)
        await db.commit()

    all_res = await db.execute(select(RevisionItem).where(RevisionItem.user_id == user_id))
    items = all_res.scalars().all()

    if not items:
        for seed in DEFAULT_REVISION_SEEDS:
            item = RevisionItem(
                user_id=user_id,
                title=seed["title"],
                key_fact=seed["key_fact"],
                subject_name=seed["subject_name"],
                topic_name=seed["topic_name"],
                source_book=seed["source_book"],
                source_page=seed["source_page"],
                next_review_due=datetime.utcnow()
            )
            db.add(item)
        await db.commit()
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
