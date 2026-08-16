"""
Dedicated ChatGPT Service for Book-Specific Workspace & Interaction.
Provides grounded Q&A, chapter analysis, MCQ/test generation, structured notes,
important dates extraction, and revision sheets using Direct ChatGPT Service.
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.models.schema import Book, BookChatMessage
from app.services.ai.direct_chatgpt_service import direct_chatgpt_service
from app.utils.logger import logger

class BookChatService:
    """
    Manages book-specific ChatGPT conversations with full document comprehension,
    session memory, and official OpenAI ChatGPT integration.
    """

    async def execute_book_chat(
        self,
        book_id: int,
        user_id: int,
        message: str,
        db: AsyncSession,
        chapter_id: Optional[int] = None,
        page_start: Optional[int] = None,
        page_end: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes a book-grounded ChatGPT interaction using direct OpenAI document context.
        """
        book_res = await db.execute(
            select(Book).where(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_res.scalar_one_or_none()
        if not book:
            raise ValueError("पुस्तक सापडले नाही किंवा या पुस्तकावर तुमचा अधिकार नाही.")

        logger.info(f"[BookChat] Executing Direct ChatGPT for book id={book_id}, query='{message[:40]}'")

        # Load complete document and ask OpenAI ChatGPT directly
        doc_context, sources_meta = await direct_chatgpt_service._load_attached_documents([book_id], user_id, db)

        # Build prompt with full document context
        system_content = (
            f"तुम्ही MPSC चे अनुभवी शिक्षक आहात. खालील पुस्तकाच्या आधारे विद्यार्थ्याच्या प्रश्नाचे नैसर्गिक मराठीत (९८-१००%) उत्तर द्या.\n\n"
            f"{doc_context}"
        )

        openai_messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": message}
        ]

        answer_text, prov_name = await direct_chatgpt_service._call_openai_api(openai_messages)
        citations = direct_chatgpt_service._extract_citations(answer_text, sources_meta)

        # Save to isolated BookChatMessage table for book history
        user_msg = BookChatMessage(
            book_id=book_id,
            user_id=user_id,
            chapter_id=chapter_id,
            sender="user",
            message=message,
            output_type="chat"
        )
        ai_msg = BookChatMessage(
            book_id=book_id,
            user_id=user_id,
            chapter_id=chapter_id,
            sender="ai",
            message=answer_text,
            output_type="chat",
            sources=citations
        )
        db.add_all([user_msg, ai_msg])
        await db.commit()
        await db.refresh(ai_msg)

        return {
            "answer": answer_text,
            "source_citations": citations,
            "output_type": "chat",
            "book_id": book_id,
            "pdf_url": None,
            "history_id": ai_msg.id
        }

    async def get_book_chat_history(
        self,
        book_id: int,
        user_id: int,
        db: AsyncSession,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieves isolated conversation history for a specific book."""
        result = await db.execute(
            select(BookChatMessage)
            .where(BookChatMessage.book_id == book_id, BookChatMessage.user_id == user_id)
            .order_by(BookChatMessage.created_at.asc())
            .limit(limit)
        )
        messages = result.scalars().all()
        return [
            {
                "id": m.id,
                "sender": m.sender,
                "message": m.message,
                "output_type": m.output_type,
                "sources": m.sources or [],
                "pdf_url": m.pdf_url,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in messages
        ]

    async def clear_book_chat_history(
        self,
        book_id: int,
        user_id: int,
        db: AsyncSession
    ) -> bool:
        """Clears isolated conversation history for a specific book."""
        await db.execute(
            delete(BookChatMessage)
            .where(BookChatMessage.book_id == book_id, BookChatMessage.user_id == user_id)
            .order_by(BookChatMessage.id.asc())
        )
        await db.commit()
        return True

book_chat_service = BookChatService()
