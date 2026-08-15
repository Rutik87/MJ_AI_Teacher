from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.database import get_db
from app.models.schema import User, Book, Test, Progress, StudySession, Bookmark, RevisionItem, Subject
from app.schemas.pydantic_models import ProgressSummaryResponse, SubjectMastery
from app.services.progress.analytics import progress_analytics

router = APIRouter(tags=["Progress & Analytics"])

def _calculate_streak(active_dates: set) -> int:
    if not active_dates:
        return 0
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    current_date = today if today in active_dates else (yesterday if yesterday in active_dates else None)
    if not current_date:
        return 0
    
    streak = 0
    while current_date in active_dates:
        streak += 1
        current_date -= timedelta(days=1)
    return streak

@router.get("/progress/summary", response_model=ProgressSummaryResponse)
async def get_progress_summary(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """
    Returns 100% real study statistics, subject-wise mastery, and dynamic metrics derived strictly from the database.
    Zero activity returns a clean 0% / 0 days / 0 min state.
    """
    # 1. Books count (real books in database)
    b_res = await db.execute(select(Book))
    books = b_res.scalars().all()
    total_books_read = len([b for b in books if b.progress_percent > 0 or b.current_page_processing > 0])

    # 2. Completed tests
    t_res = await db.execute(
        select(Test).where(Test.user_id == user_id, Test.is_completed == True).order_by(Test.completed_at.desc())
    )
    tests = t_res.scalars().all()
    total_tests_taken = len(tests)

    # 3. Questions & Accuracy
    total_questions_solved = sum(t.total_questions for t in tests)
    total_correct = sum(t.correct_count for t in tests)
    overall_accuracy = round((total_correct / max(total_questions_solved, 1)) * 100.0, 1) if total_questions_solved > 0 else 0.0

    # 4. Study Sessions & Minutes
    s_res = await db.execute(select(StudySession).where(StudySession.user_id == user_id))
    study_sessions = s_res.scalars().all()
    total_study_minutes = sum(s.duration_minutes for s in study_sessions)

    # 5. Weekly study hours (Mon-Sun of current week)
    now = datetime.utcnow()
    monday = now.date() - timedelta(days=now.weekday())
    weekly_hours = [0.0] * 7
    active_dates = set()

    for s in study_sessions:
        if s.created_at:
            s_date = s.created_at.date()
            active_dates.add(s_date)
            days_diff = (s_date - monday).days
            if 0 <= days_diff < 7:
                weekly_hours[days_diff] += round(s.duration_minutes / 60.0, 2)

    for t in tests:
        if t.completed_at:
            active_dates.add(t.completed_at.date())

    # 6. Bookmarks count
    bm_res = await db.execute(select(func.count(Bookmark.id)).where(Bookmark.user_id == user_id))
    total_bookmarks = bm_res.scalar() or 0

    # 7. Revision items (due and total)
    rev_res = await db.execute(select(RevisionItem).where(RevisionItem.user_id == user_id))
    revision_items = rev_res.scalars().all()
    due_revision_count = len([r for r in revision_items if r.next_review_due and r.next_review_due <= now])

    for r in revision_items:
        if r.last_reviewed:
            active_dates.add(r.last_reviewed.date())

    # 8. Streak calculation
    streak_days = _calculate_streak(active_dates)

    # 9. Subject Mastery from Progress table
    p_res = await db.execute(select(Progress).where(Progress.user_id == user_id))
    progress_records = p_res.scalars().all()
    progress_map = {p.subject_name: p for p in progress_records}

    # Load standard subjects
    subj_res = await db.execute(select(Subject).order_by(Subject.id))
    all_subjects = subj_res.scalars().all()

    subject_mastery_list: List[SubjectMastery] = []
    weak_areas = []

    if all_subjects:
        for subj in all_subjects:
            p = progress_map.get(subj.name_mr)
            if p and p.total_questions_attempted > 0:
                is_weak = p.mastery_percentage < 60.0 and p.total_questions_attempted >= 5
                if is_weak:
                    weak_areas.append(p.subject_name)
                subject_mastery_list.append(SubjectMastery(
                    subject_name=subj.name_mr,
                    attempted=p.total_questions_attempted,
                    correct=p.total_correct,
                    mastery_percentage=p.mastery_percentage,
                    is_weak_area=is_weak,
                    recommendation_mr=p.recommended_action_mr or f"{subj.name_mr} चा नियमित सराव करा."
                ))
            else:
                subject_mastery_list.append(SubjectMastery(
                    subject_name=subj.name_mr,
                    attempted=0,
                    correct=0,
                    mastery_percentage=0.0,
                    is_weak_area=False,
                    recommendation_mr="अजून अभ्यास सुरू केलेला नाही."
                ))
    elif progress_records:
        for p in progress_records:
            is_weak = p.mastery_percentage < 60.0 and p.total_questions_attempted >= 5
            if is_weak:
                weak_areas.append(p.subject_name)
            subject_mastery_list.append(SubjectMastery(
                subject_name=p.subject_name,
                attempted=p.total_questions_attempted,
                correct=p.total_correct,
                mastery_percentage=p.mastery_percentage,
                is_weak_area=is_weak,
                recommendation_mr=p.recommended_action_mr or f"{p.subject_name} चा नियमित सराव करा."
            ))

    # 10. Preparation percentage: deterministic formula based on active mastery across syllabus
    # Formula: average mastery of subjects divided by total standard subjects
    total_subjects_count = len(all_subjects) if all_subjects else 16
    active_mastery_sum = sum(p.mastery_percentage for p in progress_records if p.total_questions_attempted > 0)
    preparation_percentage = round(min(100.0, active_mastery_sum / max(total_subjects_count, 1)), 1) if progress_records else 0.0

    # 11. Recent Activities (Real DB records only)
    recent_acts: List[Dict[str, Any]] = []
    for t in tests[:3]:
        recent_acts.append({
            "title": f"{t.subject_name} सराव चाचणी ({t.correct_count}/{t.total_questions})",
            "type": "test",
            "time": t.completed_at.strftime("%d-%m-%Y %H:%M") if t.completed_at else "काही वेळापूर्वी"
        })
    for s in study_sessions[:2]:
        recent_acts.append({
            "title": f"{s.subject_name} अभ्यास सत्र ({s.duration_minutes} मिनिटे)",
            "type": "session",
            "time": s.created_at.strftime("%d-%m-%Y %H:%M") if s.created_at else "काही वेळापूर्वी"
        })

    return ProgressSummaryResponse(
        total_study_minutes=total_study_minutes,
        total_books_read=total_books_read,
        total_tests_taken=total_tests_taken,
        total_questions_solved=total_questions_solved,
        streak_days=streak_days,
        preparation_percentage=preparation_percentage,
        overall_accuracy=overall_accuracy,
        total_bookmarks=total_bookmarks,
        due_revision_count=due_revision_count,
        subjects_mastery=subject_mastery_list,
        weak_areas=weak_areas,
        recent_activities=recent_acts,
        weekly_study_hours=weekly_hours
    )
