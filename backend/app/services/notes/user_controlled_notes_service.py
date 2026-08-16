"""
User-Controlled Document Notes Generator & Multi-Chapter Service (Browser Prototype)
Enables explicit user control over:
1. Subject (History, Polity, Geography, Economics, Science, Maharashtra Special, Custom)
2. Scope (Full File, Chapter, Selected Pages)
3. Chapter (Auto-detected breakdown)
4. Exam Target (MPSC Prelims, Mains, Prelims+Mains, General, Custom)
5. Output Type (Handwritten Notes, Short Revision, Detailed Notes, One-Day Revision, PYQ/MCQ Focused, Summary, Custom)
6. Language (Marathi default)
7. Free-Form User Instruction (PRIMARY priority over default formats)
"""

import os
import re
import json
import uuid
import asyncio
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

# In-memory session registry for prototype testing
PROTOTYPE_SESSIONS: Dict[str, Dict[str, Any]] = {}

STANDARD_MPSC_SUBJECTS = [
    "इतिहास (History)",
    "महाराष्ट्राचा इतिहास (Maharashtra History)",
    "भूगोल (Geography)",
    "महाराष्ट्राचा भूगोल (Maharashtra Geography)",
    "राज्यशास्त्र (Polity & Governance)",
    "अर्थशास्त्र (Economics & Planning)",
    "सामान्य विज्ञान व तंत्रज्ञान (General Science)",
    "पर्यावरण व जैवविविधता (Environment)",
    "चालू घडामोडी (Current Affairs)",
    "महाराष्ट्र विशेष (Maharashtra Special)",
    "सामान्य ज्ञान (General Knowledge)",
    "इतर / सानुकूल विषय (Custom Subject)"
]

OUTPUT_TYPES = [
    {"id": "handwritten_notes", "label_mr": "✍️ Handwritten Notebook Notes", "desc": "रुल्ड नोटबुक स्टाइल, बॉक्सेस, फ्लोचार्ट व ट्रिक्स"},
    {"id": "short_revision", "label_mr": "⚡ Short Revision Notes", "desc": "संक्षिप्त बुलेट पॉईंट्स व कीवर्ड्स"},
    {"id": "detailed_notes", "label_mr": "📚 Detailed Comprehensive Notes", "desc": "सखोल विश्लेषण, पार्श्वभूमी व कारणे-परिणाम"},
    {"id": "one_day_revision", "label_mr": "🎯 One-Day Exam Revision Sheet", "desc": "परीक्षेच्या आदल्या दिवशी वाचायची २-पानांची शीट"},
    {"id": "pyq_focused", "label_mr": "📝 PYQ Focused Points", "desc": "आयोगाच्या विचारसरणीनुसार संभाव्य प्रश्न व विश्लेषण"},
    {"id": "mcq_focused", "label_mr": "❓ 30+ MPSC MCQs with Explanations", "desc": "बहुपर्यायी प्रश्न, उत्तरे व मराठी स्पष्टीकरण"},
    {"id": "summary", "label_mr": "📌 Simple Marathi Summary", "desc": "सोप्या भाषेत संक्षिप्त सारांश"},
    {"id": "custom", "label_mr": "🛠️ Custom Output Format", "desc": "वापरकर्त्याच्या विशेष आज्ञेनुसार सानुकूल रचना"}
]

EXAM_TARGETS = [
    {"id": "mpsc_prelims", "label": "MPSC पूर्व परीक्षा (Prelims - Rajyaseva / Combine)"},
    {"id": "mpsc_mains", "label": "MPSC मुख्य परीक्षा (Mains - GS 1, 2, 3, 4)"},
    {"id": "prelims_mains", "label": "MPSC पूर्व + मुख्य संयुक्त (Integrated Prelims & Mains)"},
    {"id": "general", "label": "सर्व स्पर्धा परीक्षा (General Competitive Exams)"},
    {"id": "custom", "label": "इतर परीक्षा (Custom Exam)"}
]

class UserControlledNotesService:
    """
    Orchestrates user-guided document extraction, chapter segmentation,
    ChatGPT prompt construction respecting user instruction priority, and multi-page rendering.
    """

    async def process_upload(
        self,
        file_bytes: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """Uploads and analyzes document chapters."""
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
            if extracted_doc.pages:
                for idx, p in enumerate(extracted_doc.pages, start=1):
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
            "generated_chapters": [],
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
            ],
            "standard_subjects": STANDARD_MPSC_SUBJECTS,
            "output_types": OUTPUT_TYPES,
            "exam_targets": EXAM_TARGETS
        }

    async def _generate_single_chapter(
        self,
        chapter_title: str,
        chapter_text: str,
        filename: str,
        subject: str,
        exam_target: str,
        output_type: str,
        custom_instruction: Optional[str]
    ) -> Dict[str, Any]:
        """Generates structured notes for a single chapter respecting user priorities."""
        # 1. Base user instruction priority
        instruction_text = (
            custom_instruction.strip()
            if custom_instruction and custom_instruction.strip()
            else f"या अध्यायाचे {subject} विषयानुसार MPSC परीक्षेसाठी सोपे, संक्षिप्त व परिपूर्ण handwritten notes तयार करा."
        )

        # 2. Exam target specific nuance
        exam_guidance = ""
        if exam_target == "mpsc_prelims":
            exam_guidance = "लक्ष्य: MPSC पूर्व परीक्षा (वस्तुनिष्ठ तथ्ये, तारखा, आकडेवारी, जोड्या जुळवा व MCQ कीवर्ड्सवर भर)."
        elif exam_target == "mpsc_mains":
            exam_guidance = "लक्ष्य: MPSC मुख्य परीक्षा (संकल्पनात्मक स्पष्टता, कारणे-परिणाम, धोरणात्मक विश्लेषण व मुद्देसूद मांडणी)."
        elif exam_target == "prelims_mains":
            exam_guidance = "लक्ष्य: MPSC पूर्व + मुख्य संयुक्त (तथ्ये व विश्लेषण दोन्हीचा समतोल)."

        # 3. Output type specific nuance
        output_guidance = ""
        if output_type == "short_revision":
            output_guidance = "फॉरमॅट: अत्यंत संक्षिप्त कीवर्ड्स, २-३ ओळींचे बुलेट पॉईंट्स व जलद उजळणी तक्ते."
        elif output_type == "mcq_focused":
            output_guidance = "फॉरमॅट: प्रकरणातील प्रत्येक महत्त्वाच्या मुद्द्यावर आधारित MPSC दर्जाचे MCQs व स्पष्टीकरण."
        elif output_type == "one_day_revision":
            output_guidance = "फॉरमॅट: परीक्षेच्या आदल्या दिवशी वाचण्यासाठी केवळ अति-महत्त्वाचे कोर मुद्दे व ट्रिक्स."
        elif output_type == "pyq_focused":
            output_guidance = "फॉरमॅट: मागील वर्षांच्या प्रश्नांचे स्वरूप व संभाव्य परीक्षा प्रश्न."

        system_prompt = (
            "तू MPSC आणि स्पर्धा परीक्षांसाठी एक उच्च दर्जाचा शिक्षक व नोट्स तज्ज्ञ आहेस.\n"
            "तुझे कर्तव्य आहे की वापरकर्त्याच्या दिलेल्या आज्ञेनुसार मूळ मजकुरावरून परिपूर्ण मराठी नोट्स तयार करणे.\n"
            "नियम:\n"
            "१. सर्वोच्च प्राधान्य: वापरकर्त्याची थेट आज्ञा (User Custom Instruction).\n"
            "२. सत्यता व आधार: १००% दिलेल्या मूळ मजकुरावरच आधारित राहा (Strict Grounding, No Hallucinations).\n"
            "३. भाषा: ९८-१००% अस्खलित देवनागरी मराठी. इंग्रजी केवळ अपरिहार्य तांत्रिक शब्दांसाठी.\n"
            "४. आउटपुट: केवळ आणि केवळ खालील वैध JSON स्ट्रक्चरमध्येच दे."
        )

        user_prompt = f"""
पुस्तकाचे नाव: {filename}
विषय (Subject): {subject}
अध्याय / प्रकरण: {chapter_title}
परीक्षेचे स्वरूप (Exam Target): {exam_guidance}
नोट्स शैली (Output Type): {output_guidance}

=== वापरकर्त्याची थेट व मुख्य आज्ञा (PRIMARY USER INSTRUCTION) ===
{instruction_text}
==============================================================

=== संदर्भ मजकूर (GROUNDED SOURCE CONTENT) ===
{chapter_text[:11000]}
=== संदर्भ समाप्त ===

JSON SCHEMA (सर्व फील्ड्स मराठीत भरा):
{{
  "heading_mr": "{chapter_title}",
  "subheading_mr": "{subject} • {output_type.replace('_', ' ').title()}",
  "short_definition_mr": "विषयाची किंवा संकल्पनेची सोपी व्याख्या / प्रस्तावना",
  "important_concepts": [
    {{"title_mr": "संकल्पना १", "explanation_mr": "स्पष्टीकरण"}},
    {{"title_mr": "संकल्पना २", "explanation_mr": "स्पष्टीकरण"}}
  ],
  "key_points": [
    "१. महत्त्वाचा मुद्दा १",
    "२. महत्त्वाचा मुद्दा २",
    "३. महत्त्वाचा मुद्दा ३"
  ],
  "important_dates": [
    "📅 १. तारीख / वर्ष - घटना",
    "📅 २. तारीख / वर्ष - घटना"
  ],
  "important_personalities": [
    "👤 १. व्यक्तीचे नाव - कार्य व योगदान",
    "👤 २. व्यक्तीचे नाव - कार्य व योगदान"
  ],
  "memory_tricks": [
    "💡 लक्षात ठेवण्याची ट्रिक १"
  ],
  "table": {{
    "title_mr": "महत्त्वाचा तुलनात्मक तक्ता",
    "headers": ["मुद्दा / घटक", "तपशील", "MPSC संदर्भ"],
    "rows": [
      ["घटक १", "तपशील १", "महत्त्व १"],
      ["घटक २", "तपशील २", "महत्त्व २"]
    ]
  }},
  "flowchart_steps": [
    "पायरी १: प्रारंभ / कारणे",
    "पायरी २: घटना / विकास",
    "पायरी ३: परिणाम / निष्कर्ष"
  ],
  "exam_points": [
    "🎯 MPSC परीक्षेत विचारले जाणारे अति-महत्त्वाचे मुद्दे व संभाव्य ट्रॅप्स"
  ],
  "quick_revision_box": [
    "⚡ Quick Revision: जलद उजळणीचे मुख्य मुद्दे"
  ],
  "common_mistakes": [
    "⚠️ विद्यार्थ्यांच्या सामान्य चुका / संभ्रमाचे मुद्दे टाळा"
  ]
}}
"""

        res_tuple = await llm_provider._execute_with_provider(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.25,
            max_tokens=2500
        )
        res_text = res_tuple[0] if isinstance(res_tuple, tuple) else res_tuple
        if not res_text:
            raise ValueError("ChatGPT कडून प्रतिसाद मिळाला नाही.")

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
            logger.warning(f"[UserControlledNotes] JSON parsing fallback: {e}")
            parsed_json = {
                "heading_mr": chapter_title,
                "subheading_mr": f"{subject} • अभ्यास नोट्स",
                "short_definition_mr": f"{chapter_title} बाबत महत्त्वाच्या मुद्द्यांची मांडणी.",
                "key_points": [l.strip() for l in chapter_text.split("\n") if len(l.strip()) > 20][:5],
                "important_dates": ["प्रकरणातील प्रमुख ऐतिहासिक / तांत्रिक कालक्रम."],
                "important_personalities": ["महत्त्वाच्या व्यक्ती व संदर्भ."],
                "memory_tricks": ["💡 कीवर्ड्स लक्षात ठेवा."],
                "exam_points": ["🎯 MPSC परीक्षेसाठी अति-महत्त्वाचा भाग."],
                "quick_revision_box": ["⚡ मुख्य मुद्द्यांची जलद उजळणी करा."],
                "common_mistakes": ["⚠️ चुकीचे पर्याय व गोंधळ टाळा."]
            }

        return parsed_json

    async def generate_user_controlled_notes(
        self,
        doc_id: str,
        subject: str = "सामान्य ज्ञान (General Knowledge)",
        scope: str = "chapter",  # 'chapter', 'full_file', 'selected_pages'
        chapter_id: Optional[int] = None,
        exam_target: str = "mpsc_prelims",
        output_type: str = "handwritten_notes",
        language: str = "mr",
        custom_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes user-controlled note generation.
        If 'full_file' is selected, generates chapter-by-chapter and combines into a multi-chapter PDF.
        """
        if doc_id not in PROTOTYPE_SESSIONS:
            raise ValueError("सत्र सापडले नाही. कृपया फाईल पुन्हा अपलोड करा.")

        session = PROTOTYPE_SESSIONS[doc_id]
        chapters_to_process: List[Dict[str, Any]] = []

        if scope == "full_file" or (chapter_id is not None and chapter_id == 0):
            # Process all detected chapters individually (up to 6 chapters for safe prototype limits)
            chapters_to_process = session["chapters"][:6]
        elif chapter_id is not None and chapter_id > 0:
            ch_match = next((c for c in session["chapters"] if c["id"] == chapter_id), None)
            if ch_match:
                chapters_to_process = [ch_match]
            else:
                chapters_to_process = [session["chapters"][0]] if session["chapters"] else []
        else:
            chapters_to_process = [session["chapters"][0]] if session["chapters"] else []

        if not chapters_to_process:
            raise ValueError("प्रक्रिया करण्यासाठी कोणतेही प्रकरण सापडले नाही.")

        logger.info(f"[UserControlledNotes] Generating {len(chapters_to_process)} chapters for doc_id {doc_id} (Subject: {subject}, Exam: {exam_target}, Output: {output_type})")

        generated_chapter_notes: List[Dict[str, Any]] = []
        for ch in chapters_to_process:
            ch_note = await self._generate_single_chapter(
                chapter_title=ch["title"],
                chapter_text=ch["text"],
                filename=session["filename"],
                subject=subject,
                exam_target=exam_target,
                output_type=output_type,
                custom_instruction=custom_instruction
            )
            generated_chapter_notes.append(ch_note)

        # Render combined multi-chapter notebook PDF
        pdf_path, pdf_url, page_count = await pdf_note_renderer.render_notebook_pdf(
            book_id=int(hash(doc_id) % 10000),
            book_title=f"{subject} - {session['filename']}",
            chapters=generated_chapter_notes
        )

        session["generated_note"] = generated_chapter_notes[0] if generated_chapter_notes else {}
        session["generated_chapters"] = generated_chapter_notes
        session["pdf_path"] = pdf_path
        session["pdf_url"] = f"/api/prototype/notes/{doc_id}/pdf"

        return {
            "doc_id": doc_id,
            "subject": subject,
            "scope": scope,
            "exam_target": exam_target,
            "output_type": output_type,
            "total_processed_chapters": len(generated_chapter_notes),
            "structured_note": generated_chapter_notes[0] if generated_chapter_notes else {},
            "all_chapters_notes": generated_chapter_notes,
            "page_count": max(len(generated_chapter_notes) * 2, page_count),
            "pdf_url": session["pdf_url"]
        }

    def get_session(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return PROTOTYPE_SESSIONS.get(doc_id)

user_controlled_notes_service = UserControlledNotesService()
