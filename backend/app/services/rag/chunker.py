import re
import uuid
from typing import List, Dict, Any
from app.config import settings

class DocumentChunker:
    """
    Sentence-aware chunker that splits document pages into coherent chunks
    while preserving page, chapter, and book metadata.
    """

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk_book_pages(
        self,
        book_id: int,
        book_title: str,
        subject_name: str,
        pages_data: List[Dict[str, Any]],
        chapters_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunks all pages of a book while linking each chunk to its corresponding chapter.
        """
        all_chunks = []
        chunk_index = 0

        for p in pages_data:
            page_num = p["page_number"]
            page_text = p["text"]
            if not page_text or len(page_text.strip()) < 10:
                continue

            # Find matching chapter
            chapter_title = "General"
            for chap in chapters_data:
                if chap["start_page"] <= page_num <= chap["end_page"]:
                    chapter_title = chap["title"]
                    break

            # Split page text into chunks
            page_chunks = self._split_text_into_chunks(page_text)
            for text_chunk in page_chunks:
                if len(text_chunk.strip()) < 20:
                    continue

                chunk_uuid = str(uuid.uuid4())
                all_chunks.append({
                    "chunk_uuid": chunk_uuid,
                    "book_id": book_id,
                    "book_title": book_title,
                    "subject_name": subject_name,
                    "chapter_title": chapter_title,
                    "page_number": page_num,
                    "chunk_index": chunk_index,
                    "text_content": text_chunk.strip(),
                    "char_count": len(text_chunk.strip())
                })
                chunk_index += 1

        return all_chunks

    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Splits text into chunks respecting Marathi and English sentence boundaries.
        """
        # Split by paragraph first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_chunk = ""

        # Sentence delimiters: Marathi danda (।), double danda (॥), period, exclamation, question mark, newline
        sentence_endings = re.compile(r'(?<=[।॥\.!\?\n])\s+')

        for para in paragraphs:
            if len(current_chunk) + len(para) < self.chunk_size:
                current_chunk = f"{current_chunk}\n\n{para}".strip()
            else:
                sentences = sentence_endings.split(para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if len(current_chunk) + len(sentence) < self.chunk_size:
                        current_chunk = f"{current_chunk} {sentence}".strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        # Overlap: keep last few characters of previous chunk
                        if self.chunk_overlap > 0 and len(current_chunk) > self.chunk_overlap:
                            overlap_text = current_chunk[-self.chunk_overlap:]
                            current_chunk = f"{overlap_text} {sentence}".strip()
                        else:
                            current_chunk = sentence

        if current_chunk and len(current_chunk.strip()) > 0:
            chunks.append(current_chunk.strip())

        return chunks

chunker = DocumentChunker()
