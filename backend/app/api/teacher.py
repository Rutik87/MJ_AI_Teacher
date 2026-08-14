from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.pydantic_models import TeacherTopicRequest, ChatMessageResponse, SourceCitation
from app.services.rag.retriever import rag_retriever
from app.services.ai.llm_provider import llm_provider
from app.services.ai.prompts import MPSC_TEACHER_SYSTEM_PROMPT, EXAM_MODE_SYSTEM_PROMPT

router = APIRouter(tags=["MPSC Teacher Mode"])

@router.post("/teacher/teach")
async def teach_topic_progressively(request: TeacherTopicRequest, db: AsyncSession = Depends(get_db)):
    """
    Dedicated Teacher Mode: Explains an MPSC topic progressively with examples, common mistakes, and mini quiz.
    """
    citations, context_str, has_context = rag_retriever.retrieve(
        query=f"{request.subject or ''} {request.topic}".strip(),
        top_k=5
    )

    teaching_prompt = (
        f"{MPSC_TEACHER_SYSTEM_PROMPT}\n\n"
        f"विद्यार्थ्याची विनंती: 'मला हा घटक शिकव: {request.topic}'\n"
        f"विषय: {request.subject or 'सामान्य'}\n"
        f"काठिण्य पातळी: {request.difficulty or 'medium'}\n\n"
        f"खालील ८ टप्प्यांमध्ये अतिशय सोप्या आणि आकर्षक मराठीत शिकवा:\n"
        f"१. प्राथमिक ओळख व संकल्पना (Basic Explanation)\n"
        f"२. MPSC साठी महत्त्वाचे तथ्य व आकडेवारी (Important Facts & Dates)\n"
        f"३. हा घटक MPSC साठी का महत्त्वाचा आहे? (Exam Relevance)\n"
        f"४. सोपे उदाहरण / साम्य (Real-life Example)\n"
        f"५. परीक्षेत होणाऱ्या सामान्य चुका (Common Traps & Mistakes)\n"
        f"६. मागील वर्षांचा संदर्भ (Previous Year Insights)\n"
        f"७. द्रुत उजळणी (Quick 3-Point Revision)\n"
        f"८. लघु प्रश्नमंजुषा (Mini 2-Question Quiz)\n"
    )

    answer = await llm_provider.generate_chat_response(
        user_message=f"मला '{request.topic}' हा घटक संपूर्ण सोप्या भाषेत टप्प्याटप्प्याने शिकव.",
        context_str=context_str,
        citations=citations,
        mode="teacher_mode"
    )

    return {
        "topic": request.topic,
        "subject": request.subject,
        "lesson_markdown": answer,
        "sources": citations,
        "has_uploaded_sources": has_context
    }

@router.post("/teacher/exam-focus")
async def get_exam_focus_points(request: TeacherTopicRequest, db: AsyncSession = Depends(get_db)):
    """
    Exam Mode: High-density factual summary (Dates, Articles, Acts, Committees).
    """
    citations, context_str, has_context = rag_retriever.retrieve(
        query=f"MPSC facts {request.topic}",
        top_k=4
    )

    answer = await llm_provider.generate_chat_response(
        user_message=f"'{request.topic}' या घटकावरील MPSC परीक्षेसाठी महत्त्वाचे सर्व तथ्ये, कलमे, समित्या व तारखांची यादी दे.",
        context_str=context_str,
        citations=citations,
        mode="exam_mode"
    )

    return {
        "topic": request.topic,
        "exam_facts_markdown": answer,
        "sources": citations
    }
