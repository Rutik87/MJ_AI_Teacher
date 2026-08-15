import os
import re
import unicodedata
from typing import List, Dict, Any, Tuple, Optional, Callable
from app.utils.logger import logger

class TXTExtractor:
    """
    High-performance TXT file extractor and normalizer supporting Marathi Unicode,
    UTF-8 decoding, chapter/section detection, and logical page/chunk preservation.
    """

    @staticmethod
    def decode_and_validate(raw_bytes: bytes) -> str:
        """
        Safely decodes raw bytes as UTF-8 with strict validation.
        Rejects binary or invalid encoded files safely.
        """
        # Reject obvious binary files (containing null bytes in sample)
        if b'\x00' in raw_bytes[:1024]:
            raise ValueError("Invalid text file: binary data or null bytes detected.")

        # Try UTF-8 decoding
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback attempt with utf-8-sig (BOM) or error
            try:
                text = raw_bytes.decode("utf-8-sig")
            except UnicodeDecodeError as e:
                raise ValueError(f"Invalid text encoding. File must be valid UTF-8. Details: {e}")

        # Unicode normalization (NFKC) for Marathi / Devanagari consistency
        text = unicodedata.normalize("NFKC", text)

        # Standardize line breaks
        text = re.sub(r'\r\n|\r', '\n', text)
        text = re.sub(r'\n{4,}', '\n\n\n', text)

        if not text.strip():
            raise ValueError("Text file is empty or contains only whitespace.")

        return text

    @classmethod
    def process_txt_file(
        cls,
        file_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Extracts structured chapters and page-like segments from a TXT document.
        """
        with open(file_path, "rb") as f:
            raw_bytes = f.read()

        full_text = cls.decode_and_validate(raw_bytes)
        
        # 1. Check for explicit page markers
        pages_data = cls._extract_pages(full_text)
        total_pages = len(pages_data)

        # 2. Detect chapters / sections
        chapters = cls._detect_chapters(full_text, pages_data)

        if progress_callback and total_pages > 0:
            progress_callback(total_pages, total_pages)

        return {
            "total_pages": total_pages,
            "metadata": {
                "format": "txt",
                "char_count": len(full_text),
                "total_lines": len(full_text.splitlines())
            },
            "chapters": chapters,
            "pages": pages_data,
            "is_scanned": False
        }

    @classmethod
    def extract_from_text(cls, text: str, title: str = "") -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Directly extracts pages and chapters from a text string with Marathi Unicode normalization.
        """
        norm_text = unicodedata.normalize("NFKC", text)
        pages_data = cls._extract_pages(norm_text)
        chapters_data = cls._detect_chapters(norm_text, pages_data)
        return pages_data, chapters_data

    @staticmethod
    def _extract_pages(full_text: str) -> List[Dict[str, Any]]:
        """
        Splits text into pages if page markers exist, or logical segments (e.g. 2000 chars)
        without inventing fake physical pages.
        """
        # Explicit page delimiter regex:
        # e.g., '--- Page 1 ---', '=== पान २ ===', '[Page 3]', Form Feed '\f'
        page_delim_regex = re.compile(
            r'(?:[\r\n]|^)\s*(?:---|===|___)?\s*(?:\[?\s*(?:Page|पान|पृष्ठ)\s*([०-९0-9]+)\s*\]?)\s*(?:---|===|___)?\s*(?:[\r\n]|$)',
            re.IGNORECASE
        )

        pages = []
        if '\f' in full_text:
            raw_pages = full_text.split('\f')
            for i, p_text in enumerate(raw_pages, 1):
                clean = p_text.strip()
                if clean:
                    pages.append({
                        "page_number": i,
                        "text": clean,
                        "has_images": False,
                        "is_ocr": False,
                        "char_count": len(clean)
                    })
        elif page_delim_regex.search(full_text):
            splits = page_delim_regex.split(full_text)
            # splits will be: [preamble, page_num_1, text_1, page_num_2, text_2, ...]
            current_page = 1
            if splits[0].strip():
                pages.append({
                    "page_number": current_page,
                    "text": splits[0].strip(),
                    "has_images": False,
                    "is_ocr": False,
                    "char_count": len(splits[0].strip())
                })
                current_page += 1

            for idx in range(1, len(splits), 2):
                if idx + 1 < len(splits):
                    p_num_str = splits[idx]
                    p_text = splits[idx + 1].strip()
                    try:
                        # Convert Devanagari numerals if any
                        dev_digits = str.maketrans("०१२३४५६७८९", "0123456789")
                        p_num = int(p_num_str.translate(dev_digits))
                    except Exception:
                        p_num = current_page
                    
                    if p_text:
                        pages.append({
                            "page_number": p_num,
                            "text": p_text,
                            "has_images": False,
                            "is_ocr": False,
                            "char_count": len(p_text)
                        })
                        current_page = p_num + 1

        # If no page markers found, chunk into logical sections/pages of ~2000 chars at paragraph boundaries
        if not pages:
            paragraphs = full_text.split("\n\n")
            current_chunk = []
            current_chars = 0
            page_num = 1

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                current_chunk.append(para)
                current_chars += len(para)

                if current_chars >= 2000:
                    page_text = "\n\n".join(current_chunk)
                    pages.append({
                        "page_number": page_num,
                        "text": page_text,
                        "has_images": False,
                        "is_ocr": False,
                        "char_count": len(page_text)
                    })
                    page_num += 1
                    current_chunk = []
                    current_chars = 0

            if current_chunk:
                page_text = "\n\n".join(current_chunk)
                pages.append({
                    "page_number": page_num,
                    "text": page_text,
                    "has_images": False,
                    "is_ocr": False,
                    "char_count": len(page_text)
                })

        if not pages:
            pages.append({
                "page_number": 1,
                "text": full_text.strip(),
                "has_images": False,
                "is_ocr": False,
                "char_count": len(full_text.strip())
            })

        return pages

    @staticmethod
    def _detect_chapters(full_text: str, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detects chapter/section headings in text.
        """
        chapters = []
        chapter_regex = re.compile(
            r'(?:^|\n)\s*(?:#+\s*)?(?:प्रकरण|घटक|धडा|भाग|Chapter|Unit|Module|Section)\s*([०-९0-9IVXLCDM]+)?[\s:\-\.]*([^\n]{3,80})',
            re.IGNORECASE
        )

        for p in pages_data:
            matches = chapter_regex.finditer(p["text"])
            for m in matches:
                num_part = m.group(1) or ""
                title_part = m.group(2).strip()
                full_title = f"{num_part} {title_part}".strip()
                if len(full_title) > 3:
                    chapters.append({
                        "title": full_title,
                        "start_page": p["page_number"],
                        "end_page": p["page_number"],
                        "level": 1
                    })

        total_pages = len(pages_data)
        if chapters:
            for i in range(len(chapters)):
                if i < len(chapters) - 1:
                    chapters[i]["end_page"] = max(chapters[i]["start_page"], chapters[i+1]["start_page"] - 1)
                else:
                    chapters[i]["end_page"] = total_pages
        else:
            chapters = [{"title": "General Content", "start_page": 1, "end_page": total_pages, "level": 1}]

        return chapters

txt_extractor = TXTExtractor()
