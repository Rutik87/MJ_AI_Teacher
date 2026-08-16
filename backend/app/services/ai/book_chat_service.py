"""
Dedicated ChatGPT Service for Book-Specific Workspace & Interaction.
Provides grounded Q&A, chapter analysis, MCQ/test generation, structured notes,
important dates extraction, and revision sheets using Common PostgreSQL RAG.
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.models.schema import Book, Chapter, Page, DocumentChunk, BookChatMessage
from app.services.rag.retriever import rag_retriever
from app.services.ai.llm_provider import llm_provider
from app.services.ai.prompts import (
    MPSC_TEACHER_SYSTEM_PROMPT,
    CHATGPT_ANSWER_FORMATTER_INSTRUCTIONS
)
from app.utils.logger import logger

class BookChatService:
    """
    Manages book-specific ChatGPT conversations with strict source grounding,
    scope filtering (entire book, chapter, pages), intent classification, and history persistence.
    """

    def _classify_intent(self, message: str) -> str:
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["handwritten notes", "हस्तलिखित नोट्स", "notes banav", "नोट्स बनव"]):
            return "handwritten_notes"
        elif any(w in msg_lower for w in ["mcq", "प्रश्न", "test", "क्विझ", "quiz", "प्रश्नपत्रिका"]):
            return "mcq"
        elif any(w in msg_lower for w in ["तारीख", "तारखा", "dates", "कालक्रम", "chronology", "years"]):
            return "dates"
        elif any(w in msg_lower for w in ["revision", "उजळणी", "revision sheet", "रिव्हिजन"]):
            return "revision"
        elif any(w in msg_lower for w in ["तुलना", "compare", "तक्ता", "table"]):
            return "comparison"
        elif any(w in msg_lower for w in ["सारांश", "summary", "थोडक्यात"]):
            return "summary"
        return "chat"

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
        Executes a book-grounded ChatGPT interaction, returning structured Marathi output,
        source citations, and saving to isolated book chat history.
        """
        # 1. Validate book ownership and existence
        book_res = await db.execute(
            select(Book).where(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_res.scalar_one_or_none()
        if not book:
            raise ValueError("पुस्तक सापडले नाही किंवा या पुस्तकावर तुमचा अधिकार नाही.")

        intent = self._classify_intent(message)
        logger.info(f"[BookChat] Book ID: {book_id}, Intent: {intent}, Query: '{message}'")

        # 2. Scope-filtered RAG Retrieval
        citations, context_text, has_context = rag_retriever.retrieve(
            query=message,
            top_k=6,
            book_id=book_id
        )

        # Apply chapter_id / page filters if provided
        if citations and (chapter_id is not None or page_start is not None):
            filtered_citations = []
            for c in citations:
                if chapter_id is not None and getattr(c, "chapter_id", None) and c.chapter_id != chapter_id:
                    continue
                if page_start is not None and c.page_number < page_start:
                    continue
                if page_end is not None and c.page_number > page_end:
                    continue
                filtered_citations.append(c)

            if filtered_citations:
                citations = filtered_citations
                context_text = "\n\n".join([f"[{c.book_name} | {c.chapter} | पान {c.page_number}]: {c.text_snippet}" for c in citations])
                has_context = True

        # 3. Source Grounding Guardrail
        if not has_context or not context_text.strip():
            fallback_msg = f"या पुस्तकातील ({book.title}) उपलब्ध मजकुरामध्ये '{message}' बाबत माहिती सापडली नाही. कृपया पुस्तकातील उपलब्ध प्रकरणांनुसार प्रश्न विचारा."
            
            # Save user message & AI response to book history
            user_msg_record = BookChatMessage(
                book_id=book_id,
                user_id=user_id,
                chapter_id=chapter_id,
                sender="user",
                message=message,
                output_type="chat"
            )
            ai_msg_record = BookChatMessage(
                book_id=book_id,
                user_id=user_id,
                chapter_id=chapter_id,
                sender="ai",
                message=fallback_msg,
                output_type="chat",
                sources=[]
            )
            db.add_all([user_msg_record, ai_msg_record])
            await db.commit()

            return {
                "answer": fallback_msg,
                "source_citations": [],
                "output_type": "chat",
                "book_id": book_id,
                "pdf_url": None
            }

        # 4. Construct Intent-Specific Prompt
        intent_guidance = ""
        if intent == "mcq":
            intent_guidance = (
                "\n\n[विशेष सूचना]: वरील संदर्भाच्या आधारे MPSC परीक्षेसाठी अत्यंत दर्जेदार, बहुपर्यायी प्रश्न (MCQs) तयार कर. "
                "प्रत्येक प्रश्नाचे ४ पर्याय (A, B, C, D), योग्य उत्तर आणि सविस्तर मराठी स्पष्टीकरण दे."
            )
        elif intent == "dates":
            intent_guidance = (
                "\n\n[विशेष सूचना]: वरील संदर्भातील सर्व ऐतिहासिक / महत्त्वाच्या तारखा, वर्षे, आणि त्या दिवशी घडलेल्या घटनांचा "
                "कालक्रमानुसार (Chronological) सुंदर Markdown तक्ता (Table) तयार कर."
            )
        elif intent == "comparison":
            intent_guidance = (
                "\n\n[विशेष सूचना]: वरील संदर्भातील घटकांची तुलना करणारा एक व्यवस्थित Markdown तक्ता (Table) तयार कर."
            )
        elif intent == "revision":
            intent_guidance = (
                "\n\n[विशेष सूचना]: परीक्षेच्या आदल्या दिवशी जलद उजळणी (Revision) करण्यासाठी अत्यंत महत्त्वाचे बुलेट पॉईंट्स व कीवर्ड्स तयार कर."
            )
        elif intent == "handwritten_notes":
            intent_guidance = (
                "\n\n[विशेष सूचना]: MPSC विद्यार्थ्यांसाठी हस्तलिखित नोट्सच्या शैलीत मुख्य व्याख्या, महत्त्वाचे मुद्दे, आणि लक्षात ठेवण्याच्या ट्रिक्स संरचित स्वरूपात दे."
            )

        prompt = f"""
पुस्तकाचे नाव: {book.title}
वापरकर्त्याची विचारणा / आज्ञा: {message}

=== संदर्भ मजकूर (GROUNDED CONTEXT FROM UPLOADED BOOK) ===
{context_text}
=== संदर्भ समाप्त ===
{intent_guidance}

नियम:
१. फक्त आणि फक्त वरील संदर्भ मजकुराच्या आधारेच उत्तर दे.
२. ९८-१००% अस्खलित देवनागरी मराठीत उत्तर दे.
३. शेवटी योग्य संदर्भ (📖 स्रोत: पुस्तक नाव व पान क्र.) नमूद कर.
"""

        # 5. Generate Answer via direct ChatGPT
        ai_reply_tuple = await llm_provider.generate_completion(
            prompt=prompt,
            system_prompt=MPSC_TEACHER_SYSTEM_PROMPT
        )
        ai_reply = ai_reply_tuple[0] if isinstance(ai_reply_tuple, tuple) else ai_reply_tuple
        if not ai_reply:
            ai_reply = llm_provider._generate_heuristic_response(
                user_message=message,
                context_str=context_text,
                citations=citations,
                mode="general_chat"
            )

        # Format citations
        formatted_citations = [
            {
                "book_name": c.book_name,
                "chapter": c.chapter,
                "page_number": c.page_number,
                "text_snippet": c.text_snippet[:150] + "..." if len(c.text_snippet) > 150 else c.text_snippet
            }
            for c in citations
        ]

        # 6. Check for Notes PDF reference if applicable
        pdf_url = f"/api/notes/{book_id}/download" if intent == "handwritten_notes" else None

        # 7. Save to isolated BookChatMessage table
        user_msg = BookChatMessage(
            book_id=book_id,
            user_id=user_id,
            chapter_id=chapter_id,
            sender="user",
            message=message,
            output_type=intent
        )
        ai_msg = BookChatMessage(
            book_id=book_id,
            user_id=user_id,
            chapter_id=chapter_id,
            sender="ai",
            message=ai_reply,
            output_type=intent,
            sources=formatted_citations,
            pdf_url=pdf_url
        )
        db.add_all([user_msg, ai_msg])
        await db.commit()
        await db.refresh(ai_msg)

        return {
            "answer": ai_reply,
            "source_citations": formatted_citations,
            "output_type": intent,
            "book_id": book_id,
            "pdf_url": pdf_url,
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
        )
        await db.commit()
        return True

book_chat_service = BookChatService()
