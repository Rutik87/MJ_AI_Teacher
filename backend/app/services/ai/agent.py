import json
import re
from typing import Dict, Any, List, Optional
from app.services.rag.retriever import rag_retriever
from app.services.rag.vector_store import vector_store
from app.services.ai.llm_provider import llm_provider
from app.utils.logger import logger

class MPSCAgent:
    """
    Intelligent agent that routes user queries to appropriate tools:
    RAG search, chapter lookup, MCQ generation, progress analysis, or revision.
    """

    async def execute(
        self,
        user_message: str,
        mode: str = "general_chat",
        user_id: int = 1,
        book_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        history: Optional[List[Dict[str, str]]] = None,
        db_session=None
    ) -> Dict[str, Any]:
        """
        Main execution router.
        """
        # Determine intent
        intent = self._classify_intent(user_message, mode)
        logger.info(f"Agent classified query '{user_message[:40]}' as intent='{intent}'")

        if intent == "teacher_mode" or mode == "teacher_mode":
            return await self._handle_teacher_mode(user_message, book_id, history)
        elif intent == "exam_mode" or mode == "exam_mode":
            return await self._handle_exam_mode(user_message, book_id, history)
        elif intent == "pyq_analysis" or mode == "pyq_analysis":
            return await self._handle_pyq_analysis(user_message, book_id, history)
        else:
            return await self._handle_rag_chat(user_message, book_id, history, mode)

    def _classify_intent(self, message: str, current_mode: str) -> str:
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["शिकव", "समजावून सांग", "teach me", "explain simply", "सोप्या भाषेत"]):
            return "teacher_mode"
        if any(w in msg_lower for w in ["exam points", "मुद्दे", "परीक्षेसाठी", "facts", "कलमे", "कायदा"]):
            return "exam_mode"
        if any(w in msg_lower for w in ["pyq", "मागील वर्ष", "काठिण्य", "किती प्रश्न आले", "previous year"]):
            return "pyq_analysis"
        return current_mode

    async def _handle_rag_chat(
        self,
        message: str,
        book_id: Optional[int],
        history: Optional[List[Dict[str, str]]],
        mode: str
    ) -> Dict[str, Any]:
        citations, context_str, has_context = rag_retriever.retrieve(
            query=message,
            top_k=4,
            book_id=book_id
        )

        answer = await llm_provider.generate_chat_response(
            user_message=message,
            context_str=context_str,
            citations=citations,
            mode=mode,
            history=history
        )

        return {
            "answer": answer,
            "citations": citations,
            "has_context": has_context,
            "mode": mode
        }

    async def _handle_teacher_mode(
        self,
        message: str,
        book_id: Optional[int],
        history: Optional[List[Dict[str, str]]]
    ) -> Dict[str, Any]:
        citations, context_str, has_context = rag_retriever.retrieve(
            query=message,
            top_k=5,
            book_id=book_id
        )

        answer = await llm_provider.generate_chat_response(
            user_message=message,
            context_str=context_str,
            citations=citations,
            mode="teacher_mode",
            history=history
        )

        return {
            "answer": answer,
            "citations": citations,
            "has_context": has_context,
            "mode": "teacher_mode"
        }

    async def _handle_exam_mode(
        self,
        message: str,
        book_id: Optional[int],
        history: Optional[List[Dict[str, str]]]
    ) -> Dict[str, Any]:
        citations, context_str, has_context = rag_retriever.retrieve(
            query=message,
            top_k=4,
            book_id=book_id
        )

        answer = await llm_provider.generate_chat_response(
            user_message=message,
            context_str=context_str,
            citations=citations,
            mode="exam_mode",
            history=history
        )

        return {
            "answer": answer,
            "citations": citations,
            "has_context": has_context,
            "mode": "exam_mode"
        }

    async def _handle_pyq_analysis(
        self,
        message: str,
        book_id: Optional[int],
        history: Optional[List[Dict[str, str]]]
    ) -> Dict[str, Any]:
        citations, context_str, has_context = rag_retriever.retrieve(
            query=f"PYQ {message}",
            top_k=5,
            book_id=book_id
        )

        answer = await llm_provider.generate_chat_response(
            user_message=message,
            context_str=context_str,
            citations=citations,
            mode="pyq_analysis",
            history=history
        )

        return {
            "answer": answer,
            "citations": citations,
            "has_context": has_context,
            "mode": "pyq_analysis"
        }

mpsc_agent = MPSCAgent()
