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

class MJConverseResponse(BaseModel):
    reply_text: str
    speech_text: str
    intent: str
    action: str
    sources: List[Dict[str, Any]] = []

@router.post("/converse", response_model=MJConverseResponse)
async def converse_with_mj(
    payload: MJConverseRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await mj_assistant_service.process_mj_conversation(
        user_query=payload.query,
        db=db,
        book_id=payload.book_id,
        current_page=payload.current_page,
        conversation_history=payload.conversation_history
    )
    return result
