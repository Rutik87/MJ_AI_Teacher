from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import mj_assistant_service

router = APIRouter(prefix="/mj", tags=["MJ Voice Assistant"])

class MJConverseRequest(BaseModel):
    query: str
    book_id: Optional[int] = None
    current_page: Optional[int] = None
    conversation_history: Optional[List[Dict[str, str]]] = None
    preferred_mode: Optional[str] = None

class MJConverseResponse(BaseModel):
    reply_text: str
    speech_text: str
    audio_url: Optional[str] = None
    intent: str
    mode: str = "FRIEND"
    emotion: str = "friendly"
    action: str = "continue_chat"
    sources: List[Dict[str, Any]] = []

@router.post("/converse", response_model=MJConverseResponse)
async def converse_with_mj(
    payload: MJConverseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Unified conversational endpoint with single MJ voice, multi-turn memory,
    emotion analysis, RAG grounding, and pre-rendered speech audio.
    """
    result = await mj_assistant_service.process_mj_conversation(
        user_query=payload.query,
        db=db,
        book_id=payload.book_id,
        current_page=payload.current_page,
        conversation_history=payload.conversation_history,
        preferred_mode=payload.preferred_mode
    )
    return result
