from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.schema import User, ChatSession, ChatMessage
from app.schemas.pydantic_models import (
    ChatRequest, ChatMessageResponse, ChatSessionResponse, SourceCitation
)
from app.services.ai.agent import mpsc_agent
from app.services.tts.tts_service import tts_service
from app.utils.logger import logger

router = APIRouter(tags=["AI Chat & Assistant"])

@router.get("/chat/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(user_id: int = 1, db: AsyncSession = Depends(get_db)):
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
    return sessions

@router.post("/chat/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    title: str = "नवीन चर्चा",
    mode: str = "general_chat",
    user_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new chat session.
    """
    # Ensure default user exists
    u_res = await db.execute(select(User).where(User.id == user_id))
    if not u_res.scalar_one_or_none():
        user = User(id=user_id, username="mpsc_aspirant", display_name="MPSC Aspirant")
        db.add(user)
        await db.commit()

    session = ChatSession(
        user_id=user_id,
        title=title,
        mode=mode
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

@router.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(session_id: int, db: AsyncSession = Depends(get_db)):
    """
    Returns all messages for a specific chat session.
    """
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    
    # Format sources
    response_list = []
    for m in messages:
        citations = [SourceCitation(**s) for s in (m.sources or []) if isinstance(s, dict)]
        response_list.append(ChatMessageResponse(
            id=m.id,
            sender=m.sender,
            message=m.message,
            sources=citations,
            mode=m.mode,
            has_audio=m.has_audio,
            audio_url=m.audio_url,
            created_at=m.created_at
        ))
    return response_list

@router.post("/chat/message", response_model=ChatMessageResponse)
async def send_chat_message(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Processes user question with RAG, Marathi prompt engineering, and returns answer with sources.
    """
    user_id = 1
    # Ensure user exists
    u_res = await db.execute(select(User).where(User.id == user_id))
    if not u_res.scalar_one_or_none():
        user = User(id=user_id, username="mpsc_aspirant", display_name="MPSC Aspirant")
        db.add(user)
        await db.commit()

    # Get or create chat session
    session_id = request.session_id
    if not session_id:
        # Create new session with title from query
        title_snippet = request.message[:30] + ("..." if len(request.message) > 30 else "")
        session = ChatSession(
            user_id=user_id,
            title=title_snippet,
            mode=request.mode or "general_chat"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        session_id = session.id
    else:
        s_res = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = s_res.scalar_one_or_none()
        if not session:
            session = ChatSession(user_id=user_id, title="नवीन चर्चा", mode=request.mode or "general_chat")
            db.add(session)
            await db.commit()
            await db.refresh(session)
            session_id = session.id

    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        sender="user",
        message=request.message,
        mode=request.mode or "general_chat"
    )
    db.add(user_msg)
    await db.commit()

    # Fetch recent history
    history_res = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
    )
    all_msgs = history_res.scalars().all()
    history = [{"role": m.sender, "content": m.message} for m in all_msgs[-6:]]

    # Execute AI Agent
    result = await mpsc_agent.execute(
        user_message=request.message,
        mode=request.mode or session.mode or "general_chat",
        user_id=user_id,
        book_id=request.book_id,
        subject_id=request.subject_id,
        history=history,
        db_session=db
    )

    answer = result["answer"]
    citations_data = [c.dict() if hasattr(c, 'dict') else c for c in result["citations"]]

    # Save AI message
    ai_msg = ChatMessage(
        session_id=session_id,
        sender="ai",
        message=answer,
        sources=citations_data,
        mode=result.get("mode", "general_chat"),
        has_audio=False,
        audio_url=None
    )
    db.add(ai_msg)
    await db.commit()
    await db.refresh(ai_msg)

    return ChatMessageResponse(
        id=ai_msg.id,
        sender=ai_msg.sender,
        message=ai_msg.message,
        sources=result["citations"],
        mode=ai_msg.mode,
        has_audio=ai_msg.has_audio,
        audio_url=ai_msg.audio_url,
        created_at=ai_msg.created_at
    )

@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """
    Deletes a conversation session and its messages.
    """
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="सत्र सापडले नाही.")

    await db.delete(session)
    await db.commit()
    return {"message": "चर्चा सत्र यशस्वीरित्या हटवले.", "session_id": session_id}
