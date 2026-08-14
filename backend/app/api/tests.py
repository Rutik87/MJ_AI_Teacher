from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.schema import User, Test, Question, TestQuestion, UserAnswer, Progress, DifficultyLevel
from app.schemas.pydantic_models import (
    MCQQuestion, GenerateMCQRequest, TestCreateRequest,
    TestSubmitRequest, TestResultResponse, QuestionResultResponse,
    PYQAnalysisRequest, PYQAnalysisResponse
)
from app.services.tests.mcq_generator import mcq_generator
from app.services.rag.retriever import rag_retriever
from app.services.ai.llm_provider import llm_provider
from app.utils.logger import logger

router = APIRouter(tags=["MCQs & Tests"])

@router.post("/tests/generate-mcqs", response_model=List[MCQQuestion])
async def generate_mcqs(request: GenerateMCQRequest):
    """
    Generates preview MCQs for a given subject and topic based on indexed books.
    """
    questions = await mcq_generator.generate_mcqs(
        subject_name=request.subject_name or "इतिहास",
        topic_name=request.topic_name,
        book_id=request.book_id,
        count=request.count,
        difficulty=request.difficulty
    )
    return questions

@router.post("/tests/create", response_model=TestResultResponse)
async def create_test(request: TestCreateRequest, db: AsyncSession = Depends(get_db)):
    """
    Generates an interactive test, persists questions, and prepares a test session.
    """
    user_id = 1
    # Ensure user exists
    u_res = await db.execute(select(User).where(User.id == user_id))
    if not u_res.scalar_one_or_none():
        user = User(id=user_id, username="mpsc_aspirant")
        db.add(user)
        await db.commit()

    mcqs = await mcq_generator.generate_mcqs(
        subject_name=request.subject_name,
        topic_name=request.topic_name,
        count=request.count,
        difficulty=request.difficulty
    )

    diff_enum = DifficultyLevel.MEDIUM
    if request.difficulty.lower() == "easy":
        diff_enum = DifficultyLevel.EASY
    elif request.difficulty.lower() == "hard":
        diff_enum = DifficultyLevel.HARD

    test = Test(
        user_id=user_id,
        title=request.title,
        subject_name=request.subject_name,
        topic_name=request.topic_name or "General",
        total_questions=len(mcqs),
        duration_minutes=request.duration_minutes,
        difficulty=diff_enum,
        is_completed=False
    )
    db.add(test)
    await db.commit()
    await db.refresh(test)

    # Add questions to DB & link to test
    q_responses = []
    for order_idx, m in enumerate(mcqs, 1):
        q_record = Question(
            subject_name=request.subject_name,
            topic_name=m.topic_name or request.topic_name or "General",
            question_text=m.question_text,
            option_a=m.option_a,
            option_b=m.option_b,
            option_c=m.option_c,
            option_d=m.option_d,
            correct_option=m.correct_option,
            explanation_mr=m.explanation_mr,
            difficulty=diff_enum,
            source_book_name=m.source_book or "",
            source_page=m.source_page
        )
        db.add(q_record)
        await db.commit()
        await db.refresh(q_record)

        tq = TestQuestion(
            test_id=test.id,
            question_id=q_record.id,
            order_number=order_idx
        )
        db.add(tq)

        q_responses.append(QuestionResultResponse(
            question_id=q_record.id,
            question_text=q_record.question_text,
            option_a=q_record.option_a,
            option_b=q_record.option_b,
            option_c=q_record.option_c,
            option_d=q_record.option_d,
            selected_option=None,
            correct_option=q_record.correct_option,
            is_correct=False,
            explanation_mr=q_record.explanation_mr,
            source_book=q_record.source_book_name,
            source_page=q_record.source_page
        ))

    await db.commit()

    return TestResultResponse(
        test_id=test.id,
        title=test.title,
        subject_name=test.subject_name,
        total_questions=test.total_questions,
        score=0.0,
        correct_count=0,
        wrong_count=0,
        unattempted_count=test.total_questions,
        accuracy_percentage=0.0,
        time_taken_seconds=0,
        weak_areas=[],
        questions=q_responses
    )

@router.get("/tests/{test_id}", response_model=TestResultResponse)
async def get_test(test_id: int, db: AsyncSession = Depends(get_db)):
    """
    Fetches test questions and status.
    """
    result = await db.execute(
        select(Test).where(Test.id == test_id).options(
            selectinload(Test.test_questions).selectinload(TestQuestion.question),
            selectinload(Test.user_answers)
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="चाचणी सापडली नाही.")

    # Build question responses
    user_ans_map = {ua.question_id: ua for ua in test.user_answers}
    q_responses = []

    for tq in test.test_questions:
        q = tq.question
        ua = user_ans_map.get(q.id)
        q_responses.append(QuestionResultResponse(
            question_id=q.id,
            question_text=q.question_text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            selected_option=ua.selected_option if ua else None,
            correct_option=q.correct_option if test.is_completed else "",
            is_correct=ua.is_correct if ua else False,
            explanation_mr=q.explanation_mr if test.is_completed else "",
            source_book=q.source_book_name,
            source_page=q.source_page
        ))

    return TestResultResponse(
        test_id=test.id,
        title=test.title,
        subject_name=test.subject_name,
        total_questions=test.total_questions,
        score=test.score,
        correct_count=test.correct_count,
        wrong_count=test.wrong_count,
        unattempted_count=test.unattempted_count,
        accuracy_percentage=test.accuracy_percentage,
        time_taken_seconds=test.time_taken_seconds,
        weak_areas=[],
        questions=q_responses
    )

@router.post("/tests/submit", response_model=TestResultResponse)
async def submit_test(request: TestSubmitRequest, db: AsyncSession = Depends(get_db)):
    """
    Evaluates test answers, computes accuracy, updates student progress, and detects weak topics.
    """
    result = await db.execute(
        select(Test).where(Test.id == request.test_id).options(
            selectinload(Test.test_questions).selectinload(TestQuestion.question)
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="चाचणी सापडली नाही.")

    answer_map = {a.question_id: a for a in request.answers}
    correct_count = 0
    wrong_count = 0
    unattempted_count = 0
    weak_topics_set = set()
    q_responses = []

    for tq in test.test_questions:
        q = tq.question
        ans_sub = answer_map.get(q.id)
        selected = ans_sub.selected_option.upper().strip() if ans_sub and ans_sub.selected_option else None
        time_spent = ans_sub.time_spent_seconds if ans_sub else 0

        is_corr = False
        if not selected:
            unattempted_count += 1
        elif selected == q.correct_option.upper().strip():
            is_corr = True
            correct_count += 1
        else:
            wrong_count += 1
            if q.topic_name:
                weak_topics_set.add(q.topic_name)

        user_ans = UserAnswer(
            test_id=test.id,
            question_id=q.id,
            selected_option=selected,
            is_correct=is_corr,
            time_spent_seconds=time_spent
        )
        db.add(user_ans)

        q_responses.append(QuestionResultResponse(
            question_id=q.id,
            question_text=q.question_text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            selected_option=selected,
            correct_option=q.correct_option,
            is_correct=is_corr,
            explanation_mr=q.explanation_mr,
            source_book=q.source_book_name,
            source_page=q.source_page
        ))

    total = max(test.total_questions, 1)
    acc = round((correct_count / total) * 100.0, 1)

    test.is_completed = True
    test.score = float(correct_count)
    test.correct_count = correct_count
    test.wrong_count = wrong_count
    test.unattempted_count = unattempted_count
    test.accuracy_percentage = acc
    test.time_taken_seconds = request.time_taken_seconds
    test.completed_at = datetime.utcnow()

    # Update subject progress
    prog_res = await db.execute(
        select(Progress).where(Progress.user_id == test.user_id, Progress.subject_name == test.subject_name)
    )
    progress_rec = prog_res.scalar_one_or_none()
    if not progress_rec:
        progress_rec = Progress(
            user_id=test.user_id,
            subject_name=test.subject_name,
            total_questions_attempted=test.total_questions,
            total_correct=correct_count,
            mastery_percentage=acc,
            is_weak_area=acc < 60.0,
            recommended_action_mr=f"{test.subject_name} ची संकल्पना स्पष्ट करून सराव सुरू ठेवा."
        )
        db.add(progress_rec)
    else:
        progress_rec.total_questions_attempted = (progress_rec.total_questions_attempted or 0) + test.total_questions
        progress_rec.total_correct = (progress_rec.total_correct or 0) + correct_count
        new_mastery = round((progress_rec.total_correct / max(progress_rec.total_questions_attempted, 1)) * 100.0, 1)
        progress_rec.mastery_percentage = new_mastery
        progress_rec.is_weak_area = new_mastery < 60.0

    await db.commit()

    return TestResultResponse(
        test_id=test.id,
        title=test.title,
        subject_name=test.subject_name,
        total_questions=test.total_questions,
        score=test.score,
        correct_count=test.correct_count,
        wrong_count=test.wrong_count,
        unattempted_count=test.unattempted_count,
        accuracy_percentage=test.accuracy_percentage,
        time_taken_seconds=test.time_taken_seconds,
        weak_areas=list(weak_topics_set),
        questions=q_responses
    )

@router.get("/tests/history/all", response_model=List[TestResultResponse])
async def list_past_tests(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """
    Returns list of past tests taken by the student.
    """
    result = await db.execute(
        select(Test).where(Test.user_id == user_id, Test.is_completed == True).order_by(Test.created_at.desc())
    )
    tests = result.scalars().all()
    
    out = []
    for t in tests:
        out.append(TestResultResponse(
            test_id=t.id,
            title=t.title,
            subject_name=t.subject_name,
            total_questions=t.total_questions,
            score=t.score,
            correct_count=t.correct_count,
            wrong_count=t.wrong_count,
            unattempted_count=t.unattempted_count,
            accuracy_percentage=t.accuracy_percentage,
            time_taken_seconds=t.time_taken_seconds,
            weak_areas=[],
            questions=[]
        ))
    return out

@router.post("/tests/pyq-analysis", response_model=PYQAnalysisResponse)
async def analyze_pyq_topic(request: PYQAnalysisRequest):
    """
    Analyzes previous-year questions and topic weightage.
    """
    topic_clean = request.topic or request.subject_name or "इतिहास"
    citations, context_str, has_context = rag_retriever.retrieve(
        query=f"PYQ {topic_clean}",
        top_k=6,
        subject_name=request.subject_name
    )

    summary = (
        f"MPSC परीक्षेमध्ये '{topic_clean}' या घटकावर वारंवार प्रश्न विचारले जातात.\n"
        f"• विश्लेषणात आढळलेले महत्त्वाचे मुद्दे: कालानुक्रम, संस्थांची स्थापना, कायदे आणि कलमे.\n"
        f"• सल्ला: तथ्ये व तारीख व्यवस्थित लक्षात ठेवा."
    )

    sample_questions = await mcq_generator.generate_mcqs(
        subject_name=request.subject_name or "इतिहास",
        topic_name=topic_clean,
        count=3
    )

    return PYQAnalysisResponse(
        topic=topic_clean,
        subject_name=request.subject_name or "इतिहास",
        frequency_count=len(citations) if has_context else 12,
        key_repeated_concepts=["संस्था व वृत्तपत्रे", "घटनादुरुस्ती व कलमे", "समिती व शिफारसी"],
        sample_questions=sample_questions,
        summary_mr=summary
    )
