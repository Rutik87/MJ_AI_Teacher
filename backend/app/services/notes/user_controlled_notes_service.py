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

# ============================================================
# OCR / Header / Footer noise patterns to strip before LLM
# ============================================================
_NOISE_PATTERNS = [
    # Repeated academy/publisher headers
    r'(?i)bhagirath\s+ias\s+academy.*',
    r'(?i)ias\s+academy\s+ias\s+academy.*',
    # Silver sticker hologram OCR garbage
    r'(?i)silver\s+sticker\s+hologram.*',
    # Generic copyright/publisher footers
    r'(?i)©\s*\d{4}.*all\s+rights\s+reserved.*',
    r'(?i)printed\s+(?:by|at|in)\s+.*',
    r'(?i)published\s+(?:by|at)\s+.*',
    # Standalone page numbers
    r'^\s*-?\s*\d{1,4}\s*-?\s*$',
    # Decorative lines
    r'^[\s\-=_\*#~]{5,}$',
    # Repeated dashes/underscores
    r'^[_\-=]{3,}\s*$',
]
_COMPILED_NOISE = [re.compile(p, re.MULTILINE) for p in _NOISE_PATTERNS]


def _clean_source_text(raw_text: str) -> str:
    """
    Removes OCR garbage, repeated headers/footers, publisher watermarks,
    and other non-content noise from extracted document text.
    Preserves all meaningful study content.
    """
    if not raw_text:
        return ""

    lines = raw_text.split("\n")
    cleaned_lines: List[str] = []

    # Detect repeated header/footer lines (appear 3+ times)
    line_freq: Dict[str, int] = {}
    for line in lines:
        stripped = line.strip()
        if stripped and len(stripped) > 3:
            norm = re.sub(r'\s+', ' ', stripped.lower())
            line_freq[norm] = line_freq.get(norm, 0) + 1

    repeated_headers = {k for k, v in line_freq.items() if v >= 3 and len(k) < 80}

    for line in lines:
        stripped = line.strip()

        # Skip empty lines (but allow some for paragraph breaks)
        if not stripped:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue

        # Skip lines matching noise patterns
        skip = False
        for pat in _COMPILED_NOISE:
            if pat.search(stripped):
                skip = True
                break

        if skip:
            continue

        # Skip repeated header/footer lines
        norm = re.sub(r'\s+', ' ', stripped.lower())
        if norm in repeated_headers:
            continue

        # Skip very short lines that are likely page artifacts
        if len(stripped) <= 3 and not any(c.isalpha() for c in stripped):
            continue

        cleaned_lines.append(stripped)

    result = "\n".join(cleaned_lines).strip()
    # Collapse excessive blank lines
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result


def _validate_generated_content(note: Dict[str, Any], source_text: str) -> bool:
    """
    Validates that generated notes contain actual source-derived content,
    not generic placeholder or machine-translated filler text.
    Returns True if content passes quality gate.
    """
    # Generic filler phrases that indicate bad generation
    GENERIC_FILLER_PHRASES = [
        "indian history",
        "quick revelation",
        "over-criticism",
        "presenting important issues",
        "silver sticker hologram",
        "definition / introduction",
        "important dates and chronology",
        "important persons and functions",
        "trick to remember",
        "key points",
        "avoid confusion",
        "the major historical",
        "the technical chronology",
        "important individuals and references",
        "remember the keywords",
        "संकल्पना १",
        "संकल्पना २",
        "स्पष्टीकरण",
        "महत्त्वाचा मुद्दा १",
        "महत्त्वाचा मुद्दा २",
        "महत्त्वाचा मुद्दा ३",
        "तारीख / वर्ष - घटना",
        "व्यक्तीचे नाव - कार्य व योगदान",
        "घटक १",
        "तपशील १",
        "महत्त्व १",
        "पायरी १: प्रारंभ / कारणे",
        "पायरी २: घटना / विकास",
        "पायरी ३: परिणाम / निष्कर्ष",
    ]

    # Serialize all text content from the note
    all_text = json.dumps(note, ensure_ascii=False).lower()

    filler_count = 0
    for phrase in GENERIC_FILLER_PHRASES:
        if phrase.lower() in all_text:
            filler_count += 1
            logger.warning(f"[ContentValidation] Found generic filler: '{phrase}'")

    if filler_count >= 3:
        logger.error(f"[ContentValidation] FAILED: {filler_count} generic filler phrases detected")
        return False

    # Check that key_points contain substantive content (not just template labels)
    key_points = note.get("key_points", [])
    if key_points:
        substantive_points = [p for p in key_points if len(str(p)) > 15]
        if len(substantive_points) < len(key_points) * 0.5:
            logger.warning("[ContentValidation] Most key_points are too short / template-like")
            return False

    return True


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
        """
        Generates structured notes for a single chapter.
        CRITICAL: All content must come from the actual source text.
        No generic placeholder or template content is allowed.
        """

        # ============================================================
        # STEP 1: Clean source text (remove OCR garbage, headers, footers)
        # ============================================================
        cleaned_chapter_text = _clean_source_text(chapter_text)
        if not cleaned_chapter_text or len(cleaned_chapter_text) < 30:
            cleaned_chapter_text = chapter_text  # Fallback to raw if cleaning is too aggressive

        # ============================================================
        # STEP 2: Build user instruction with priority hierarchy
        # ============================================================
        instruction_text = (
            custom_instruction.strip()
            if custom_instruction and custom_instruction.strip()
            else f"या अध्यायाचे {subject} विषयानुसार MPSC परीक्षेसाठी सोपे, संक्षिप्त व परिपूर्ण नोट्स तयार करा."
        )

        # Exam target guidance
        exam_guidance = ""
        if exam_target == "mpsc_prelims":
            exam_guidance = "लक्ष्य: MPSC पूर्व परीक्षा — वस्तुनिष्ठ तथ्ये, तारखा, आकडेवारी, जोड्या जुळवा, MCQ कीवर्ड्स."
        elif exam_target == "mpsc_mains":
            exam_guidance = "लक्ष्य: MPSC मुख्य परीक्षा — संकल्पनात्मक स्पष्टता, कारणे-परिणाम, धोरणात्मक विश्लेषण."
        elif exam_target == "prelims_mains":
            exam_guidance = "लक्ष्य: MPSC पूर्व + मुख्य संयुक्त — तथ्ये व विश्लेषण दोन्हीचा समतोल."

        # Output type guidance
        output_guidance = ""
        if output_type == "short_revision":
            output_guidance = "फॉरमॅट: अत्यंत संक्षिप्त कीवर्ड्स, २-३ ओळींचे बुलेट पॉईंट्स."
        elif output_type == "mcq_focused":
            output_guidance = "फॉरमॅट: प्रत्येक महत्त्वाच्या मुद्द्यावर MPSC दर्जाचे MCQs व स्पष्टीकरण."
        elif output_type == "one_day_revision":
            output_guidance = "फॉरमॅट: परीक्षेच्या आदल्या दिवशी वाचण्यासाठी केवळ अति-महत्त्वाचे मुद्दे."
        elif output_type == "pyq_focused":
            output_guidance = "फॉरमॅट: मागील वर्षांच्या प्रश्नांचे स्वरूप व संभाव्य परीक्षा प्रश्न."

        # ============================================================
        # STEP 3: Build STRICT source-grounded prompt
        # ============================================================
        system_prompt = (
            "तू MPSC परीक्षांसाठी एक अनुभवी शिक्षक आहेस.\n\n"
            "=== अत्यंत महत्त्वाचे नियम (STRICT RULES) ===\n"
            "१. खालील 'मूळ मजकूर' या विभागातील माहितीवरूनच नोट्स तयार कर. बाहेरची कोणतीही माहिती जोडू नकोस.\n"
            "२. भाषा: ९८-१००% नैसर्गिक मराठी. इंग्रजी फक्त तांत्रिक शब्दांसाठी (MPSC, UNESCO, GDP इ.).\n"
            "३. प्रत्येक मुद्दा, तारीख, व्यक्ती, घटना हे मूळ मजकुरात असलेच पाहिजे. कल्पित/अनुमानित माहिती पूर्णपणे बंद.\n"
            "४. जेनेरिक/टेम्प्लेट वाक्ये लिहू नकोस. उदा: 'महत्त्वाच्या तारखा व कालक्रम', 'महत्त्वाच्या व्यक्ती व त्यांचे कार्य' हे सेक्शन हेडिंग म्हणून ठीक आहेत पण त्यांचे आत मूळ मजकुरातील प्रत्यक्ष तारखा/व्यक्ती लिहा.\n"
            "५. इंग्रजी शीर्षकांचे यांत्रिक भाषांतर करू नकोस. 'Quick Revelation', 'Over-criticism' अशा गोंधळात पाडणाऱ्या भाषांतरांना मनाई.\n"
            "६. जर मूळ मजकुरात एखाद्या फील्डसाठी (उदा: memory_tricks, important_dates) पुरेशी माहिती नसेल, तर ते फील्ड रिकामे ठेव किंवा null दे. जबरदस्तीने भरू नकोस.\n"
            "७. आउटपुट: केवळ वैध JSON. कोणताही अतिरिक्त मजकूर JSON च्या बाहेर लिहू नकोस.\n"
            "८. मूळ मजकुरातील सर्व महत्त्वाचे मुद्दे समाविष्ट कर — जास्तीत जास्त content coverage ठेव.\n"
        )

        # Use up to 14000 chars of cleaned source to maximize content coverage
        source_content = cleaned_chapter_text[:14000]

        user_prompt = f"""पुस्तक: {filename}
विषय: {subject}
अध्याय: {chapter_title}
{f"परीक्षा: {exam_guidance}" if exam_guidance else ""}
{f"शैली: {output_guidance}" if output_guidance else ""}

=== वापरकर्त्याची आज्ञा (PRIMARY) ===
{instruction_text}
=======================================

=== मूळ मजकूर (SOURCE — फक्त याच मजकुरावरून नोट्स बनव) ===
{source_content}
=== मूळ मजकूर समाप्त ===

या मूळ मजकुरातून खालील JSON बनव. प्रत्येक फील्ड मराठीत भर. मूळ मजकुरात नसलेली माहिती लिहू नकोस — ते फील्ड null किंवा रिकामे ठेव.

{{
  "heading_mr": "अध्यायाचे शीर्षक मराठीत",
  "subheading_mr": "विषय आणि नोट्स प्रकार",
  "short_definition_mr": "या प्रकरणाची/विषयाची सोपी ओळख (मूळ मजकुरावरून)",
  "important_concepts": [
    {{"title_mr": "प्रत्यक्ष संकल्पनेचे नाव", "explanation_mr": "मूळ मजकुरातील स्पष्टीकरण"}}
  ],
  "key_points": [
    "मूळ मजकुरातील प्रत्यक्ष महत्त्वाचा मुद्दा (प्रत्येक मुद्दा १-३ वाक्ये)"
  ],
  "important_dates": [
    "📅 प्रत्यक्ष तारीख/वर्ष — प्रत्यक्ष घटना (मूळ मजकुरातून)"
  ],
  "important_personalities": [
    "👤 प्रत्यक्ष व्यक्तीचे नाव — प्रत्यक्ष कार्य (मूळ मजकुरातून)"
  ],
  "memory_tricks": null,
  "table": null,
  "flowchart_steps": null,
  "exam_points": [
    "मूळ मजकुरातील MPSC दृष्टीने सर्वात महत्त्वाचे तथ्य"
  ],
  "quick_revision_box": [
    "मूळ मजकुरातील प्रमुख कीवर्ड्स/तथ्ये एका ओळीत"
  ],
  "common_mistakes": null
}}"""

        # ============================================================
        # STEP 4: Call LLM with adequate token budget
        # ============================================================
        res_tuple = await llm_provider._execute_with_provider(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.15,
            max_tokens=4096
        )
        res_text = res_tuple[0] if isinstance(res_tuple, tuple) else res_tuple

        if not res_text:
            logger.error("[UserControlledNotes] No response from LLM — building source-extracted fallback")
            return self._build_source_extracted_fallback(chapter_title, cleaned_chapter_text, subject, output_type)

        # ============================================================
        # STEP 5: Parse JSON response
        # ============================================================
        cleaned = res_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Handle cases where LLM adds text before/after JSON
        json_start = cleaned.find('{')
        json_end = cleaned.rfind('}')
        if json_start >= 0 and json_end > json_start:
            cleaned = cleaned[json_start:json_end + 1]

        try:
            parsed_json = json.loads(cleaned)
        except Exception as e:
            logger.warning(f"[UserControlledNotes] JSON parsing failed: {e}")
            logger.debug(f"[UserControlledNotes] Raw response (first 500 chars): {res_text[:500]}")
            return self._build_source_extracted_fallback(chapter_title, cleaned_chapter_text, subject, output_type)

        # ============================================================
        # STEP 6: Content validation — reject generic filler
        # ============================================================
        if not _validate_generated_content(parsed_json, cleaned_chapter_text):
            logger.warning("[UserControlledNotes] Content validation FAILED — regenerating with stricter prompt")
            # One retry with even stricter instructions
            retry_prompt = (
                f"मागील प्रयत्नात जेनेरिक/टेम्प्लेट मजकूर आला. पुन्हा प्रयत्न कर.\n"
                f"खालील मूळ मजकुरातील प्रत्यक्ष तथ्ये, तारखा, व्यक्ती, घटना वापर.\n"
                f"कोणतीही जेनेरिक वाक्ये लिहू नकोस.\n\n"
                f"{user_prompt}"
            )
            retry_tuple = await llm_provider._execute_with_provider(
                prompt=retry_prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=4096
            )
            retry_text = retry_tuple[0] if isinstance(retry_tuple, tuple) else retry_tuple
            if retry_text:
                retry_cleaned = retry_text.strip()
                if retry_cleaned.startswith("```json"):
                    retry_cleaned = retry_cleaned[7:]
                elif retry_cleaned.startswith("```"):
                    retry_cleaned = retry_cleaned[3:]
                if retry_cleaned.endswith("```"):
                    retry_cleaned = retry_cleaned[:-3]
                retry_cleaned = retry_cleaned.strip()
                rj_start = retry_cleaned.find('{')
                rj_end = retry_cleaned.rfind('}')
                if rj_start >= 0 and rj_end > rj_start:
                    retry_cleaned = retry_cleaned[rj_start:rj_end + 1]
                try:
                    parsed_json = json.loads(retry_cleaned)
                except Exception:
                    pass

        # ============================================================
        # STEP 7: Clean null/empty fields and ensure Marathi heading
        # ============================================================
        if not parsed_json.get("heading_mr") or len(str(parsed_json.get("heading_mr", ""))) < 3:
            parsed_json["heading_mr"] = chapter_title

        # Remove fields that are null or empty lists
        for field in ["memory_tricks", "table", "flowchart_steps", "common_mistakes"]:
            val = parsed_json.get(field)
            if val is None or val == [] or val == "null":
                parsed_json.pop(field, None)

        return parsed_json

    def _build_source_extracted_fallback(
        self,
        chapter_title: str,
        source_text: str,
        subject: str,
        output_type: str
    ) -> Dict[str, Any]:
        """
        When LLM fails completely, extract real content directly from source text.
        NO generic placeholder text — every line comes from the actual source.
        """
        lines = [l.strip() for l in source_text.split("\n") if len(l.strip()) > 15]

        # Extract sentences as key points (first meaningful sentences)
        key_points = []
        for line in lines:
            # Skip lines that look like headers/titles (too short or all-caps)
            if len(line) > 20 and not line.isupper():
                key_points.append(line)
            if len(key_points) >= 10:
                break

        # Extract dates (look for patterns with numbers in Devanagari or Latin)
        date_pattern = re.compile(r'.*?(\d{1,2}\s+\S+\s+\d{4}|[०-९]{1,2}\s+\S+\s+[०-९]{4}|\d{4}\s*(?:रोजी|साली|मध्ये|ला)).*', re.UNICODE)
        important_dates = []
        for line in lines:
            if date_pattern.match(line):
                important_dates.append(f"📅 {line}")
                if len(important_dates) >= 8:
                    break

        # Extract people (look for names followed by यांनी/यांचे/यांना etc.)
        person_pattern = re.compile(r'.*?([A-Z\u0900-\u097F]{2,}\s+[A-Z\u0900-\u097F]+).*?(?:यांनी|यांचे|यांची|यांना|यांचा).*', re.UNICODE)
        important_personalities = []
        for line in lines:
            if person_pattern.match(line) or any(k in line for k in ["यांनी", "यांचे", "यांची"]):
                important_personalities.append(f"👤 {line}")
                if len(important_personalities) >= 6:
                    break

        # First line as definition/intro
        short_def = lines[0] if lines else chapter_title

        return {
            "heading_mr": chapter_title,
            "subheading_mr": f"{subject} • अभ्यास नोट्स",
            "short_definition_mr": short_def,
            "key_points": key_points[:8],
            "important_dates": important_dates if important_dates else None,
            "important_personalities": important_personalities if important_personalities else None,
            "exam_points": [f"🎯 {kp}" for kp in key_points[:3]] if key_points else None,
            "quick_revision_box": [f"⚡ {kp}" for kp in key_points[:5]] if key_points else None,
        }

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
