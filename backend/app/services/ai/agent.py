from typing import Dict, Any, List, Optional
from app.services.rag.retriever import rag_retriever
from app.services.ai.llm_provider import llm_provider
from app.utils.logger import logger

class MPSCAgent:
    """
    Intelligent ChatGPT-powered MPSC assistant that executes RAG search
    across uploaded files and generates natural Marathi answers.
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
        Executes file-aware ChatGPT chat using shared RAG retriever.
        """
        logger.info(f"ChatGPT Agent processing query: '{user_message[:40]}' (book_id={book_id})")
        return await self._handle_rag_chat(user_message, book_id, history, mode)

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

mpsc_agent = MPSCAgent()
