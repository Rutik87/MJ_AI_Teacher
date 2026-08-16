from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.schema import User, ChatSession, ChatMessage
from app.schemas.pydantic_models import (
    ChatMessageResponse, ChatSessionResponse, SourceCitation
)
from app.services.ai.direct_chatgpt_service import direct_chatgpt_service
from app.utils.logger import logger

router = APIRouter(tags=["ChatGPT Workspace"])

class DirectChatRequest(BaseModel):
    session_id: Optional[int] = None
    message: str
    book_id: Optional[int] = None
    book_ids: Optional[List[int]] = None
    mode: Optional[str] = "general_chat"
    user_id: Optional[int] = 1

class CreateSessionRequest(BaseModel):
    title: Optional[str] = "नवीन चर्चा"
    mode: Optional[str] = "general_chat"
    attached_book_ids: Optional[List[int]] = []
    user_id: Optional[int] = 1

class GenerateArtifactRequest(BaseModel):
    session_id: Optional[int] = None
    source_book_id: Optional[int] = None
    title: str = "MPSC Study Notes"
    content: str
    artifact_type: str = "pdf"  # "pdf" or "txt"
    user_id: Optional[int] = 1

@router.get("/chat/sessions")
async def list_chat_sessions(user_id: int = Query(1), db: AsyncSession = Depends(get_db)):
    """
    Returns all chat conversation sessions for the user.
    """
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "mode": s.mode,
            "attached_book_ids": s.attached_book_ids or [],
            "message_count": len(s.messages) if s.messages else 0,
            "created_at": s.created_at.isoformat() if s.created_at else "",
            "updated_at": s.updated_at.isoformat() if s.updated_at else ""
        }
        for s in sessions
    ]

@router.post("/chat/sessions")
async def create_chat_session(
    payload: CreateSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new persistent chat session with optional attached books.
    """
    user_id = payload.user_id or 1
    u_res = await db.execute(select(User).where(User.id == user_id))
    if not u_res.scalar_one_or_none():
        user = User(id=user_id, username=f"user_{user_id}", display_name="MPSC Aspirant")
        db.add(user)
        await db.commit()

    session = ChatSession(
        user_id=user_id,
        title=payload.title or "नवीन चर्चा",
        mode=payload.mode or "general_chat",
        attached_book_ids=payload.attached_book_ids or []
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {
        "id": session.id,
        "title": session.title,
        "mode": session.mode,
        "attached_book_ids": session.attached_book_ids or [],
        "created_at": session.created_at.isoformat() if session.created_at else ""
    }

@router.get("/chat/sessions/{session_id}/messages")
async def get_session_messages(session_id: int, user_id: int = Query(1), db: AsyncSession = Depends(get_db)):
    """
    Returns all messages for a specific chat session with ownership verification.
    """
    s_res = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )
    session = s_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="चॅट संभाषण सापडले नाही.")

    result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    
    return [
        {
            "id": m.id,
            "session_id": m.session_id,
            "sender": m.sender,
            "message": m.message,
            "sources": m.sources or [],
            "mode": m.mode,
            "has_audio": False,
            "audio_url": None,
            "created_at": m.created_at.isoformat() if m.created_at else ""
        }
        for m in messages
    ]

@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: int, user_id: int = Query(1), db: AsyncSession = Depends(get_db)):
    """
    Deletes a chat session and all its messages.
    """
    s_res = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )
    session = s_res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="चॅट संभाषण सापडले नाही.")

    await db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    await db.delete(session)
    await db.commit()
    return {"success": True, "message": "चॅट संभाषण हटवले."}

@router.post("/chat/message")
async def send_chat_message(request: DirectChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Direct official OpenAI ChatGPT messaging with native document attachments,
    session persistence, and natural Marathi responses.
    """
    user_id = request.user_id or 1
    
    # Consolidate attached book IDs
    attached_ids = []
    if request.book_ids:
        attached_ids.extend(request.book_ids)
    if request.book_id and request.book_id not in attached_ids:
        attached_ids.append(request.book_id)

    response_data = await direct_chatgpt_service.execute_chat(
        user_message=request.message,
        session_id=request.session_id,
        user_id=user_id,
        attached_book_ids=attached_ids,
        db=db,
        mode=request.mode or "general_chat"
    )

    return response_data

@router.post("/chat/generate-artifact")
async def generate_chat_artifact(request: GenerateArtifactRequest, db: AsyncSession = Depends(get_db)):
    """
    Generates a downloadable artifact (PDF or TXT) from ChatGPT output,
    uploads it permanently to Supabase Storage, and registers it in the library.
    """
    user_id = request.user_id or 1
    result = await direct_chatgpt_service.generate_and_save_artifact(
        title=request.title,
        content=request.content,
        artifact_type=request.artifact_type,
        user_id=user_id,
        session_id=request.session_id,
        source_book_id=request.source_book_id,
        db=db
    )
    return result
