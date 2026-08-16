"""
MPSC AI v1.0 — Simple Study Schedule & AI Timetable Analyzer Endpoint.
Allows MPSC aspirants to manage their daily study plan, target exam date,
and request ChatGPT-powered schedule analysis and timetable optimization.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.schema import User, Subject, StudySession
from app.services.ai.llm_provider import llm_provider
from app.services.ai.prompts import MPSC_TEACHER_SYSTEM_PROMPT
from app.utils.logger import logger

router = APIRouter(tags=["Schedule & Study Planner"])

class ScheduleSlot(BaseModel):
    time_slot: str  # e.g., "07:00 AM - 09:00 AM"
    subject: str    # e.g., "महाराष्ट्राचा इतिहास"
    topic: str      # e.g., "१८५७ चा उठाव व समाजसुधारक"
    activity: str   # e.g., "वाचन व नोट्स"

class StudyPlanRequest(BaseModel):
    user_id: int = 1
    target_exam: str = "MPSC राज्यसेवा / संयुक्त पूर्व परीक्षा"
    exam_date: Optional[str] = "2026-11-15"
    daily_study_hours: float = 6.0
    primary_subjects: List[str] = ["इतिहास", "राज्यशास्त्र", "भूगोल", "अर्थशास्त्र"]
    slots: List[ScheduleSlot] = []

class ScheduleAnalyzeRequest(BaseModel):
    user_id: int = 1
    target_exam: str = "MPSC राज्यसेवा / संयुक्त पूर्व परीक्षा"
    daily_study_hours: float = 6.0
    exam_date: Optional[str] = "2026-11-15"
    weak_subjects: List[str] = ["अर्थशास्त्र", "विज्ञान व तंत्रज्ञान"]
    current_schedule: Optional[str] = ""

# In-memory default schedule fallback
_IN_MEMORY_SCHEDULES: Dict[int, Dict[str, Any]] = {
    1: {
        "target_exam": "MPSC राज्यसेवा / संयुक्त पूर्व परीक्षा",
        "exam_date": "2026-11-15",
        "daily_study_hours": 6.0,
        "primary_subjects": ["इतिहास", "राज्यशास्त्र", "भूगोल", "अर्थशास्त्र"],
        "slots": [
            {"time_slot": "07:00 AM - 09:00 AM", "subject": "राज्यशास्त्र", "topic": "मूलभूत हक्क व मार्गदर्शक तत्त्वे", "activity": "सखोल वाचन"},
            {"time_slot": "10:00 AM - 12:00 PM", "subject": "इतिहास", "topic": "महाराष्ट्रातील समाजसुधारक", "activity": "नोट्स व रिव्हिजन"},
            {"time_slot": "02:00 PM - 03:30 PM", "subject": "भूगोल", "topic": "महाराष्ट्राची प्राकृतिक रचना व नद्या", "activity": "नकाशा वाचन"},
            {"time_slot": "07:00 PM - 08:30 PM", "subject": "अर्थशास्त्र", "topic": "राष्ट्रीय उत्पन्न व पंचवार्षिक योजना", "activity": "MCQ सराव"},
        ],
        "updated_at": datetime.utcnow().isoformat()
    }
}

@router.get("/schedule")
async def get_study_schedule(user_id: int = Query(1), db: AsyncSession = Depends(get_db)):
    """
    Retrieves the user's current study plan and timetable slots.
    """
    if user_id in _IN_MEMORY_SCHEDULES:
        return _IN_MEMORY_SCHEDULES[user_id]

    # Default starter schedule
    return {
        "target_exam": "MPSC राज्यसेवा / संयुक्त पूर्व परीक्षा",
        "exam_date": "2026-11-15",
        "daily_study_hours": 6.0,
        "primary_subjects": ["इतिहास", "राज्यशास्त्र", "भूगोल", "अर्थशास्त्र"],
        "slots": [
            {"time_slot": "07:00 AM - 09:00 AM", "subject": "राज्यशास्त्र", "topic": "घटनेची निर्मिती व ठळक वैशिष्ट्ये", "activity": "वाचन"},
            {"time_slot": "10:00 AM - 12:00 PM", "subject": "इतिहास", "topic": "आधुनिक भारताचा इतिहास", "activity": "नोट्स"},
            {"time_slot": "04:00 PM - 06:00 PM", "subject": "भूगोल व अर्थशास्त्र", "topic": "महत्त्वाचे घटक", "activity": "सराव"}
        ],
        "updated_at": datetime.utcnow().isoformat()
    }

@router.post("/schedule")
async def save_study_schedule(plan: StudyPlanRequest, db: AsyncSession = Depends(get_db)):
    """
    Saves or updates the user's study schedule and time slots.
    """
    _IN_MEMORY_SCHEDULES[plan.user_id] = {
        "target_exam": plan.target_exam,
        "exam_date": plan.exam_date,
        "daily_study_hours": plan.daily_study_hours,
        "primary_subjects": plan.primary_subjects,
        "slots": [s.model_dump() for s in plan.slots],
        "updated_at": datetime.utcnow().isoformat()
    }
    logger.info(f"Updated study schedule for user_id={plan.user_id}, {len(plan.slots)} slots.")
    return {
        "success": True,
        "message": "अभ्यास नियोजन यशस्वीरित्या सेव्ह केले.",
        "schedule": _IN_MEMORY_SCHEDULES[plan.user_id]
    }

@router.post("/schedule/analyze")
async def analyze_study_schedule(req: ScheduleAnalyzeRequest):
    """
    Uses OpenAI ChatGPT directly to analyze the aspirant's study schedule,
    identify gaps/weak areas, and generate an actionable, balanced MPSC study timetable.
    """
    weak_str = ", ".join(req.weak_subjects) if req.weak_subjects else "कोणतेही नमूद नाही"
    
    prompt = f"""
तुम्ही MPSC चे अनुभवी मार्गदर्शक व मेंटॉर आहात. विद्यार्थ्याच्या खालील अभ्यास नियोजनाचे विश्लेषण करा आणि त्याला परिपूर्ण वेळापत्रक (Timetable) तयार करून द्या.

विद्यार्थ्याची माहिती:
• लक्ष्य परीक्षा: {req.target_exam}
• परीक्षेची अंदाजित तारीख: {req.exam_date or '३-४ महिने'}
• रोज उपलब्ध अभ्यासाचे तास: {req.daily_study_hours} तास
• कमजोर / कठीण वाटणारे विषय: {weak_str}
• सद्यस्थितीतील नियोजन: {req.current_schedule or 'नियमित वाचन'}

कृपया खालील संरचनेत शुद्ध, नैसर्गिक मराठीत (९८-१००%) सविस्तर मार्गदर्शन द्या:

### 🎯 १. अभ्यास नियोजनाचे विश्लेषण (Schedule Analysis)
(वेळेचे योग्य नियोजन, विषयांचा समतोल, आणि सुधारणांचे मुद्दे)

### 🗓️ २. शिफारस केलेले दैनिक वेळापत्रक (Optimized Daily Timetable)
(सकाळ, दुपार, संध्याकाळ अशा स्लॉट्सचा सुंदर Markdown तक्ता)

### ⚡ ३. कमजोर विषयांसाठी विशेष रणनीती (Weak Subjects Strategy)
({weak_str} विषयांवर प्रभुत्व मिळवण्यासाठी सोप्या ट्रिक्स)

### 📌 ४. यशस्वी MPSC विद्यार्थ्यांसाठी ३ सुवर्ण नियम
(उजळणी, सातत्य, आणि सराव प्रश्नांचे महत्त्व)
"""

    ai_tuple = await llm_provider.generate_completion(
        prompt=prompt,
        system_prompt=MPSC_TEACHER_SYSTEM_PROMPT,
        temperature=0.3,
        max_tokens=2500
    )
    
    analysis_text = ai_tuple[0] if isinstance(ai_tuple, tuple) else ai_tuple
    if not analysis_text:
        analysis_text = (
            "### 🎯 अभ्यास नियोजन विश्लेषण\n\n"
            "• **दैनिक वेळ:** रोज किमान ६ तास नियमित अभ्यास आवश्यक आहे.\n"
            "• **विषय समतोल:** सकाळच्या शांत वेळेत कठीण विषय (उदा. राज्यशास्त्र/अर्थशास्त्र) अभ्यासावेत.\n"
            "• **रिव्हिजन:** रोज रात्री १ तास त्या दिवशी वाचलेल्या घटकांची उजळणी करावी."
        )

    return {
        "success": True,
        "target_exam": req.target_exam,
        "daily_study_hours": req.daily_study_hours,
        "analysis_markdown": analysis_text,
        "generated_at": datetime.utcnow().isoformat()
    }
