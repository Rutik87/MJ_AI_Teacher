import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF
from app.utils.logger import logger
from app.services.pdf.ocr_service import ocr_service

class PDFExtractor:
    """
    High-performance PDF text and structure extractor with OCR fallback.
    """
    
    @staticmethod
    def extract_metadata_and_toc(doc: fitz.Document) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Extracts document metadata and chapter outline (Table of Contents).
        """
        metadata = doc.metadata or {}
        toc = doc.get_toc()  # [[lvl, title, page, ...], ...]
        
        chapters = []
        if toc:
            for item in toc:
                level, title, page = item[0], item[1].strip(), item[2]
                if title and page > 0:
                    chapters.append({
                        "title": title,
                        "start_page": page,
                        "end_page": page,  # will adjust in post-processing
                        "level": level
                    })
            # Adjust end pages
            total_pages = len(doc)
            for i in range(len(chapters)):
                if i < len(chapters) - 1:
                    chapters[i]["end_page"] = max(chapters[i]["start_page"], chapters[i+1]["start_page"] - 1)
                else:
                    chapters[i]["end_page"] = total_pages
        return metadata, chapters

    @classmethod
    def extract_page(cls, doc: fitz.Document, page_num: int) -> Dict[str, Any]:
        """
        Extracts text from a single 1-indexed page, running OCR if text is minimal and images exist.
        """
        page = doc.load_page(page_num - 1)
        text = page.get_text("text").strip()
        
        # Clean control characters while preserving Marathi Unicode
        text = re.sub(r'[\r\f\v]', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        image_list = page.get_images(full=True)
        has_images = len(image_list) > 0
        is_ocr = False

        # If text is too small and page has images, attempt OCR
        if len(text) < 40 and has_images:
            logger.info(f"Page {page_num} appears scanned ({len(text)} chars). Attempting OCR...")
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            ocr_text = ocr_service.extract_text_from_image(img_bytes)
            if ocr_text and len(ocr_text) > len(text):
                text = ocr_text
                is_ocr = True

        return {
            "page_number": page_num,
            "text": text,
            "char_count": len(text),
            "has_images": has_images,
            "is_ocr": is_ocr
        }

    @classmethod
    def process_pdf_file(
        cls, 
        file_path: str,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Extracts all pages from the PDF with optional live progress callback.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at: {file_path}")

        doc = fitz.open(file_path)
        total_pages = len(doc)
        
        metadata, chapters = cls.extract_metadata_and_toc(doc)
        pages_data = []
        is_scanned_overall = False
        scanned_count = 0

        for page_num in range(1, total_pages + 1):
            page_data = cls.extract_page(doc, page_num)
            pages_data.append(page_data)
            if page_data["is_ocr"]:
                scanned_count += 1
            
            if progress_callback:
                progress_callback(page_num, total_pages)

        if total_pages > 0 and (scanned_count / total_pages) > 0.4:
            is_scanned_overall = True

        # If no TOC was found, detect heuristic chapters (e.g. 'प्रकरण', 'धडा', 'Chapter')
        if not chapters:
            chapters = cls._detect_heuristic_chapters(pages_data)

        doc.close()

        return {
            "total_pages": total_pages,
            "metadata": metadata,
            "chapters": chapters,
            "pages": pages_data,
            "is_scanned": is_scanned_overall
        }

    @staticmethod
    def _detect_heuristic_chapters(pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Heuristically finds chapter headings like 'प्रकरण १', 'घटक २', 'Chapter 1' in extracted text.
        """
        chapters = []
        chapter_regex = re.compile(
            r'(?:^|\n)\s*(?:प्रकरण|घटक|धडा|भाग|Chapter|Unit|Module)\s*([०-९0-9IVXLCDM]+)?[\s:\-\.]*([^\n]{3,60})',
            re.IGNORECASE
        )
        
        for p in pages_data:
            text = p["text"]
            match = chapter_regex.search(text[:300])  # Search top of page
            if match:
                num_part = match.group(1) or ""
                title_part = match.group(2).strip()
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

pdf_extractor = PDFExtractor()
