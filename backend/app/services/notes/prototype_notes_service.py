"""
Prototype Notes Service (Browser-First Validation)
Extracts chapters from PDF/TXT, sends chapter-scoped RAG grounded prompt to ChatGPT,
structures content into rich multi-page handwritten-style sections, and renders A4 notebook PDF.
"""

import os
import re
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from app.config import settings
from app.services.pdf.extractor import pdf_extractor
from app.services.text.txt_extractor import txt_extractor
from app.services.ai.llm_provider import llm_provider
from app.services.notes.pdf_note_renderer import pdf_note_renderer
from app.utils.logger import logger

PROTOTYPE_DATA_DIR = Path("data/prototype_notes")
PROTOTYPE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# In-memory storage for prototype session
PROTOTYPE_SESSIONS: Dict[str, Dict[str, Any]] = {}

class PrototypeNotesService:
    """
    Handles browser prototype uploads, chapter analysis, ChatGPT handwritten notes generation,
    and multi-page PDF rendering.
    """

    async def process_upload(
        self,
        file_bytes: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """Processes uploaded PDF or TXT file and detects chapter structure."""
        doc_id = str(uuid.uuid4())[:8]
        is_pdf = filename.lower().endswith(".pdf")
        saved_file_path = PROTOTYPE_DATA_DIR / f"{doc_id}_{filename}"
        
        with open(saved_file_path, "wb") as f:
            f.write(file_bytes)

        chapters: List[Dict[str, Any]] = []
        full_text = ""

        if is_pdf:
            extracted_doc = await pdf_extractor.extract(str(saved_file_path))
            full_text = extracted_doc.full_text
            # Detect chapters from extracted pages
            if extracted_doc.pages:
                for idx, p in enumerate(extracted_doc.pages, start=1):
                    # Check for chapter title in page text
                    lines = [l.strip() for l in p.text.split("\n") if l.strip()]
                    ch_title = f"प्रकरण {idx}: पान क्र. {p.page_number}"
                    for l in lines[:3]:
                        if any(k in l.lower() for k in ["प्रकरण", "अध्याय", "chapter", "भाग", "विषय"]):
                            ch_title = l[:60]
                            break
                    chapters.append({
                        "id": idx,
                        "title": ch_title,
                        "page_start": p.page_number,
                        "page_end": p.page_number,
                        "text": p.text
                    })
        else:
            full_text = txt_extractor.decode_and_validate(file_bytes)
            # Detect chapters by delimiters in TXT (supporting both English 0-9 and Marathi ०-९ digits)
            sections = [
                s.strip() for s in re.split(r'(?:\r?\n)+(?=(?:प्रकरण|अध्याय|Chapter|भाग)\s+[0-9०-९\dIVXLCDMivxlcdm]+)', full_text, flags=re.IGNORECASE)
                if s.strip()
            ]
            if len(sections) > 1:
                for idx, sec in enumerate(sections, start=1):
                    first_line = sec.strip().split("\n")[0][:60]
                    chapters.append({
                        "id": idx,
                        "title": first_line if first_line else f"प्रकरण {idx}",
                        "page_start": idx,
                        "page_end": idx,
                        "text": sec.strip()
                    })
            else:
                # Default single chapter / chunks
                chapters.append({
                    "id": 1,
                    "title": filename.replace(".txt", "").replace(".pdf", ""),
                    "page_start": 1,
                    "page_end": 1,
                    "text": full_text
                })

        session_data = {
            "id": doc_id,
            "filename": filename,
            "file_path": str(saved_file_path),
            "is_pdf": is_pdf,
            "total_chapters": len(chapters),
            "chapters": chapters,
            "full_text": full_text,
            "generated_note": None,
            "pdf_path": None,
            "pdf_url": None
        }
        PROTOTYPE_SESSIONS[doc_id] = session_data

        return {
            "id": doc_id,
            "filename": filename,
            "total_chapters": len(chapters),
            "chapters": [
                {"id": ch["id"], "title": ch["title"], "page_start": ch["page_start"], "page_end": ch["page_end"]}
                for ch in chapters
            ]
        }

    async def generate_chapter_notes(
        self,
        doc_id: str,
        chapter_id: Optional[int] = None,
        custom_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generates multi-page structured handwritten notes via ChatGPT."""
        if doc_id not in PROTOTYPE_SESSIONS:
            raise ValueError("सत्र सापडले नाही. कृपया फाईल पुन्हा अपलोड करा.")

        session = PROTOTYPE_SESSIONS[doc_id]
        selected_text = ""
        chapter_title = "संपूर्ण पुस्तक"

        if chapter_id is not None and chapter_id > 0:
            ch_match = next((c for c in session["chapters"] if c["id"] == chapter_id), None)
            if ch_match:
                selected_text = ch_match["text"]
                chapter_title = ch_match["title"]
        else:
            selected_text = session["full_text"][:14000]

        if not selected_text.strip():
            raise ValueError("निवडलेल्या अध्यायामध्ये वाचण्यायोग्य मजकूर सापडला नाही.")

        # Default prompt if custom instruction not given
        instruction = (
            custom_instruction.strip()
            if custom_instruction and custom_instruction.strip()
            else "या अध्यायाचे MPSC परीक्षेच्या दृष्टीने सोपे, संक्षिप्त पण पूर्ण handwritten notes तयार करा. सर्व महत्त्वाची माहिती, तारखा, व्यक्ती, कारणे, घटना, परिणाम आणि परीक्षा-उपयोगी मुद्दे स्रोतामधून घ्या. माहिती गाळू नका आणि बाहेरील माहिती बनवू नका."
        )

        system_prompt = (
            "तू MPSC आणि स्पर्धा परीक्षांसाठी एक उत्कृष्ट शिक्षक व हस्तलिखित (Handwritten) नोट्स तज्ज्ञ आहेस.\n"
            "तुझे काम दिलेल्या मूळ मजकुरावरून अत्यंत सोप्या, सुंदर, आकर्षक आणि बहुपृष्ठीय (Multi-page) मराठी हस्तलिखित नोट्स तयार करणे आहे.\n"
            "नियम:\n"
            "१. भाषा: ~९८% शुद्ध, सोपी व प्रभावी मराठी. इंग्रजी शब्द जास्तीत जास्त २% (केवळ तांत्रिक संज्ञा जसे की SQL, Python, GDP, Articles, Acts इत्यादी).\n"
            "२. मूळ मजकुरावरच पूर्णपणे आधारित राहा (Factually 100% Grounded, no external hallucinations).\n"
            "३. खालील JSON फॉरमॅटमध्येच वैध JSON आउटपुट दे, कोणताही अतिरिक्त मजकूर नको."
        )

        user_prompt = f"""
पुस्तकाचे नाव: {session["filename"]}
अध्याय / टॉपिक: {chapter_title}
वापरकर्त्याची विशेष आज्ञा: {instruction}

=== संदर्भ मजकूर (SOURCE CONTENT) ===
{selected_text[:12000]}
=== संदर्भ समाप्त ===

JSON SCHEMA:
{{
  "heading_mr": "मुख्य शीर्षक (उदा. {chapter_title})",
  "subheading_mr": "MPSC विशेष हस्तलिखित अभ्यास नोट्स",
  "short_definition_mr": "विषयाची किंवा संकल्पनेची २-३ ओळींत अत्यंत सोपी व्याख्या / पार्श्वभूमी",
  "important_concepts": [
    {{"title_mr": "संकल्पना १", "explanation_mr": "सोप्या भाषेत स्पष्टीकरण"}},
    {{"title_mr": "संकल्पना २", "explanation_mr": "सोप्या भाषेत स्पष्टीकरण"}}
  ],
  "key_points": [
    "१. पहिला महत्त्वाचा मुद्दा",
    "२. दुसरा महत्त्वाचा मुद्दा",
    "३. तिसरा महत्त्वाचा मुद्दा",
    "४. चौथा महत्त्वाचा मुद्दा"
  ],
  "important_dates": [
    "📅 १. महत्त्वाची तारीख १ - घडलेली घटना",
    "📅 २. महत्त्वाची तारीख २ - घडलेली घटना"
  ],
  "important_personalities": [
    "👤 १. महत्त्वाची व्यक्ती १ - कार्य व योगदान",
    "👤 २. महत्त्वाची व्यक्ती २ - कार्य व योगदान"
  ],
  "memory_tricks": [
    "💡 लक्षात ठेवण्याची सोपी ट्रिक १",
    "💡 लक्षात ठेवण्याची सोपी ट्रिक २"
  ],
  "table": {{
    "title_mr": "महत्त्वाचा तुलनात्मक तक्ता",
    "headers": ["घटक / मुद्दा", "तपशील", "MPSC महत्त्व"],
    "rows": [
      ["मुद्दा १", "तपशील १", "महत्त्व १"],
      ["मुद्दा २", "तपशील २", "महत्त्व २"]
    ]
  }},
  "flowchart_steps": [
    "पायरी १: प्रारंभ / कारणे",
    "पायरी २: प्रत्यक्ष घटना / विकास",
    "पायरी ३: परिणाम / निष्कर्ष"
  ],
  "exam_points": [
    "🎯 MPSC पूर्व व मुख्य परीक्षेत थेट विचारले जाणारे अति-महत्त्वाचे मुद्दे",
    "🎯 आयोगाचे संभाव्य ट्रॅप्स व कीवर्ड्स"
  ],
  "quick_revision_box": [
    "⚡ Quick Revision: परीक्षेच्या आदल्या दिवशी वाचायचे ५ मुख्य मुद्दे"
  ],
  "common_mistakes": [
    "⚠️ विद्यार्थ्यांच्या सामान्य चुका: परीक्षेतील संभ्रम किंवा फसवे पर्याय टाळा"
  ]
}}
"""

        logger.info(f"[PrototypeNotes] Generating notes for doc_id {doc_id}, chapter: {chapter_title}")
        res_tuple = await llm_provider._execute_with_provider(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.25,
            max_tokens=2500
        )
        res_text = res_tuple[0] if isinstance(res_tuple, tuple) else res_tuple
        if not res_text:
            raise ValueError("ChatGPT कडून प्रतिसाद मिळाला नाही.")

        # Clean JSON markdown fences
        cleaned = res_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            parsed_json = json.loads(cleaned)
        except Exception as e:
            logger.warning(f"[PrototypeNotes] JSON parse error: {e}, using heuristic fallback")
            parsed_json = {
                "heading_mr": chapter_title,
                "subheading_mr": "MPSC विशेष हस्तलिखित नोट्स",
                "short_definition_mr": "या प्रकरणातील मुख्य संकल्पनांचे संक्षिप्त रूप.",
                "important_concepts": [{"title_mr": "मुख्य संकल्पना", "explanation_mr": selected_text[:200]}],
                "key_points": [line.strip() for line in selected_text.split("\n") if len(line.strip()) > 20][:5],
                "important_dates": ["ऐतिहासिक कालक्रम व घडामोडी."],
                "important_personalities": ["महत्त्वाच्या ऐतिहासिक व अभ्यासक्रम व्यक्ती."],
                "memory_tricks": ["💡 कीवर्ड्स आणि क्रम लक्षात ठेवा."],
                "exam_points": ["🎯 MPSC परीक्षेसाठी अति-महत्त्वाचा भाग."],
                "quick_revision_box": ["⚡ मुख्य मुद्द्यांची जलद उजळणी करा."],
                "common_mistakes": ["⚠️ तारखा व व्यक्तींची नावे यात संभ्रम टाळा."]
            }

        # Render Multi-Page Notebook PDF
        pdf_path, pdf_url, page_count = await pdf_note_renderer.render_notebook_pdf(
            book_id=int(hash(doc_id) % 10000),
            book_title=session["filename"],
            chapters=[parsed_json]
        )

        session["generated_note"] = parsed_json
        session["pdf_path"] = pdf_path
        session["pdf_url"] = f"/api/prototype/notes/{doc_id}/pdf"

        return {
            "doc_id": doc_id,
            "chapter_title": chapter_title,
            "structured_note": parsed_json,
            "page_count": max(2, page_count),
            "pdf_url": session["pdf_url"]
        }

    def get_session(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return PROTOTYPE_SESSIONS.get(doc_id)

prototype_notes_service = PrototypeNotesService()
