from typing import List, Dict, Any, Optional, Tuple
from app.services.rag.vector_store import vector_store
from app.schemas.pydantic_models import SourceCitation
from app.config import settings

class RAGRetriever:
    """
    RAG retrieval engine that searches indexed books and builds structured contexts with citations.
    """

    def __init__(self):
        self.top_k = settings.TOP_K_RESULTS

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        book_id: Optional[int] = None,
        subject_name: Optional[str] = None
    ) -> Tuple[List[SourceCitation], str, bool]:
        """
        Retrieves relevant chunks and builds both citation objects and prompt context string.
        Returns: (citations_list, formatted_context_str, has_sufficient_context)
        """
        k = top_k or self.top_k
        raw_results = vector_store.search(
            query=query,
            top_k=k,
            book_id=book_id,
            subject_name=subject_name
        )

        if not raw_results:
            return [], "", False

        citations: List[SourceCitation] = []
        context_parts: List[str] = []

        for idx, (chunk, score) in enumerate(raw_results, 1):
            citation = SourceCitation(
                book_id=chunk.get("book_id", 0),
                book_name=chunk.get("book_title", "Unknown Book"),
                subject_name=chunk.get("subject_name", ""),
                chapter=chunk.get("chapter_title", "General"),
                page_number=chunk.get("page_number", 1),
                text_snippet=chunk.get("text_content", "")[:280] + ("..." if len(chunk.get("text_content", "")) > 280 else ""),
                relevance_score=round(score, 3)
            )
            citations.append(citation)

            # Format context for LLM prompt
            context_parts.append(
                f"--- संदर्भ {idx} ---\n"
                f"पुस्तक: {citation.book_name}\n"
                f"प्रकरण: {citation.chapter}\n"
                f"पान क्रमांक: {citation.page_number}\n"
                f"माहिती:\n{chunk.get('text_content', '').strip()}\n"
            )

        formatted_context = "\n".join(context_parts)
        has_sufficient_context = len(raw_results) > 0 and raw_results[0][1] > 0.05

        return citations, formatted_context, has_sufficient_context

rag_retriever = RAGRetriever()
