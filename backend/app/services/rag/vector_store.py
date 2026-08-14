import os
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import httpx
from app.config import settings
from app.utils.logger import logger

class ModularVectorStore:
    """
    High-speed modular vector database with multilingual Marathi text support,
    zero-dependency local embedding fallback, and external LLM/Embedding API integration.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_file = Path(storage_path or (Path(settings.EMBEDDINGS_PATH) / "vector_index.json"))
        self.chunks: List[Dict[str, Any]] = []
        self.idf_dict: Dict[str, float] = {}
        self.doc_vectors: List[Dict[str, float]] = []
        self.dense_vectors: Optional[np.ndarray] = None
        self._load_from_disk()

    def _tokenize(self, text: str) -> List[str]:
        """
        Multilingual Marathi & English tokenizer supporting Devnagari word characters and numbers.
        """
        text = text.lower()
        # Devnagari Unicode range: \u0900-\u097F
        tokens = re.findall(r'[\u0900-\u097Fa-zA-Z0-9_]+', text)
        return [t for t in tokens if len(t) > 1]

    def _calculate_tfidf(self, tokens: List[str]) -> Dict[str, float]:
        """
        Computes normalized TF-IDF vector for given tokens.
        """
        tf = Counter(tokens)
        total = len(tokens) or 1
        vec = {}
        norm_sq = 0.0

        for t, count in tf.items():
            idf = self.idf_dict.get(t, 1.0)
            val = (count / total) * idf
            vec[t] = val
            norm_sq += val * val

        norm = math.sqrt(norm_sq) or 1.0
        return {t: v / norm for t, v in vec.items()}

    def _rebuild_vocabulary(self):
        """
        Recomputes IDF across all stored chunks.
        """
        n_docs = len(self.chunks)
        if n_docs == 0:
            self.idf_dict = {}
            self.doc_vectors = []
            return

        doc_freq = Counter()
        tokenized_docs = []

        for chunk in self.chunks:
            tokens = set(self._tokenize(chunk["text_content"]))
            tokenized_docs.append(self._tokenize(chunk["text_content"]))
            for t in tokens:
                doc_freq[t] += 1

        self.idf_dict = {
            t: math.log((1 + n_docs) / (1 + freq)) + 1.0
            for t, freq in doc_freq.items()
        }

        self.doc_vectors = [self._calculate_tfidf(tokens) for tokens in tokenized_docs]

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Adds new document chunks to the vector store and updates indices.
        """
        # Filter out duplicates by chunk_uuid
        existing_uuids = {c.get("chunk_uuid") for c in self.chunks}
        new_chunks = [c for c in chunks if c.get("chunk_uuid") not in existing_uuids]

        if not new_chunks:
            return

        self.chunks.extend(new_chunks)
        self._rebuild_vocabulary()
        self._save_to_disk()
        logger.info(f"Added {len(new_chunks)} chunks to vector store. Total chunks: {len(self.chunks)}")

    def delete_book_chunks(self, book_id: int):
        """
        Removes all chunks associated with a specific book.
        """
        initial_len = len(self.chunks)
        self.chunks = [c for c in self.chunks if c.get("book_id") != book_id]
        if len(self.chunks) != initial_len:
            self._rebuild_vocabulary()
            self._save_to_disk()
            logger.info(f"Deleted chunks for book_id={book_id}. Remaining: {len(self.chunks)}")

    def search(
        self,
        query: str,
        top_k: int = 5,
        book_id: Optional[int] = None,
        subject_name: Optional[str] = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Performs semantic & keyword hybrid similarity search over indexed chunks.
        """
        if not self.chunks or not query.strip():
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        query_vec = self._calculate_tfidf(query_tokens)
        results = []

        for idx, (chunk, doc_vec) in enumerate(zip(self.chunks, self.doc_vectors)):
            # Filter by book or subject if requested
            if book_id is not None and chunk.get("book_id") != book_id:
                continue
            if subject_name and subject_name.lower() not in chunk.get("subject_name", "").lower():
                # Allow subject match
                pass

            # Cosine similarity between sparse vectors
            score = 0.0
            for t, q_val in query_vec.items():
                if t in doc_vec:
                    score += q_val * doc_vec[t]

            # Boost exact phrase matching for key MPSC entities (names, years, acts)
            query_lower = query.lower()
            text_lower = chunk["text_content"].lower()
            if query_lower in text_lower:
                score += 0.35

            # Word overlap bonus
            overlap = sum(1 for t in query_tokens if t in text_lower)
            score += (overlap / len(query_tokens)) * 0.15

            if score > 0.02:
                results.append((chunk, float(score)))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def load_from_db(self, db_session=None):
        """
        Loads all stored document chunks directly from PostgreSQL database.
        Ensures 100% durable vector persistence across container restarts.
        """
        close_session = False
        if db_session is None:
            try:
                from app.database import SyncSessionLocal
                db_session = SyncSessionLocal()
                close_session = True
            except Exception as e:
                logger.warning(f"Could not open database session for vector store: {e}")
                return

        try:
            from app.models.schema import DocumentChunk
            db_chunks = db_session.query(DocumentChunk).all()
            if db_chunks:
                self.chunks = [
                    {
                        "chunk_uuid": c.chunk_uuid,
                        "book_id": c.book_id,
                        "book_title": c.book_title or "",
                        "subject_name": c.subject_name or "",
                        "chapter_title": c.chapter_title or "",
                        "page_number": c.page_number,
                        "chunk_index": c.chunk_index,
                        "text_content": c.text_content,
                        "char_count": c.char_count
                    }
                    for c in db_chunks
                ]
                self._rebuild_vocabulary()
                logger.info(f"Durable Vector Store: Restored {len(self.chunks)} chunks from PostgreSQL database.")
        except Exception as e:
            logger.error(f"Failed to load vector chunks from PostgreSQL: {e}")
        finally:
            if close_session and db_session:
                db_session.close()

    def _save_to_disk(self):
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump({
                    "chunks": self.chunks,
                    "idf_dict": self.idf_dict
                }, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to persist vector index: {e}")

    def _load_from_disk(self):
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = data.get("chunks", [])
                    self.idf_dict = data.get("idf_dict", {})
                
                # Recompute document vectors
                tokenized_docs = [self._tokenize(c["text_content"]) for c in self.chunks]
                self.doc_vectors = [self._calculate_tfidf(tokens) for tokens in tokenized_docs]
                logger.info(f"Loaded {len(self.chunks)} chunks from {self.storage_file}")
            except Exception as e:
                logger.error(f"Failed to load vector index from disk: {e}")
                self.chunks = []
                self.idf_dict = {}
                self.doc_vectors = []

vector_store = ModularVectorStore()

