"""
AI Handwritten Notes Generator Service (Marathi-First & Exam-Oriented)
Processes complete document text across all chapters and produces structured,
high-yield Marathi handwritten-style study notes.
"""

import json
import re
from typing import Dict, List, Any, Optional, Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.schema import Book, Chapter, Page, DocumentChunk, HandwrittenNote
from app.services.ai.llm_provider import llm_provider
from app.utils.logger import logger

class NoteGeneratorService:
    """
    Generates structured, exam-oriented Marathi handwritten study notes from complete books.
    """

    async def generate_notes_for_book(
        self,
        book_id: int,
        user_id: int,
        db: AsyncSession,
        progress_callback: Optional[Callable[[str, float, str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        Extracts all chapters and pages, analyzes complete text, and formats structured notes.
        """
        # 1. Fetch book with chapters, pages, and chunks
        logger.info(f"[NoteGenerator] Starting notes generation for Book ID: {book_id}, User ID: {user_id}")
        
        async def update_status(status_code: str, percent: float, msg_mr: str):
            if progress_callback:
                await progress_callback(status_code, percent, msg_mr)

        await update_status("reading", 10.0, "Content वाचत आहे...")

        book_query = await db.execute(
            select(Book)
            .options(
                selectinload(Book.chapters),
                selectinload(Book.pages),
                selectinload(Book.chunks)
            )
            .where(Book.id == book_id, Book.user_id == user_id)
        )
        book = book_query.scalar_one_or_none()
        if not book:
            raise ValueError("पुस्तक सापडले नाही किंवा परवानगी नाही.")

        # 2. Extract complete text grouped by chapters or page blocks
        chapters_data = []
        if book.chapters and len(book.chapters) > 0:
            sorted_chapters = sorted(book.chapters, key=lambda c: c.start_page)
            for ch in sorted_chapters:
                # Aggregate text for chapter pages
                ch_pages = [p for p in book.pages if ch.start_page <= p.page_number <= ch.end_page]
                ch_text = "\n".join(p.extracted_text for p in sorted(ch_pages, key=lambda x: x.page_number) if p.extracted_text)
                if not ch_text.strip():
                    # Fallback to document chunks
                    ch_chunks = [c for c in book.chunks if c.chapter_id == ch.id]
                    ch_text = "\n".join(c.text_content for c in sorted(ch_chunks, key=lambda x: x.chunk_index))
                
                if ch_text.strip():
                    chapters_data.append({
                        "chapter_title": ch.title,
                        "start_page": ch.start_page,
                        "end_page": ch.end_page,
                        "text": ch_text
                    })

        # If no explicit chapters found, group pages into logical chapters
        if not chapters_data and book.pages and len(book.pages) > 0:
            sorted_pages = sorted(book.pages, key=lambda p: p.page_number)
            page_group_size = max(1, min(5, len(sorted_pages)))
            for i in range(0, len(sorted_pages), page_group_size):
                grp = sorted_pages[i:i+page_group_size]
                grp_text = "\n".join(p.extracted_text for p in grp if p.extracted_text)
                if grp_text.strip():
                    ch_name = f"प्रकरण {len(chapters_data) + 1}: पान क्र. {grp[0].page_number} - {grp[-1].page_number}"
                    chapters_data.append({
                        "chapter_title": ch_name,
                        "start_page": grp[0].page_number,
                        "end_page": grp[-1].page_number,
                        "text": grp_text
                    })

        # If still empty, check document chunks
        if not chapters_data and book.chunks and len(book.chunks) > 0:
            sorted_chunks = sorted(book.chunks, key=lambda c: (c.page_number, c.chunk_index))
            full_text = "\n".join(c.text_content for c in sorted_chunks if c.text_content)
            if full_text.strip():
                chapters_data.append({
                    "chapter_title": f"{book.title} - संपूर्ण अभ्यासक्रम",
                    "start_page": 1,
                    "end_page": max(1, book.total_pages),
                    "text": full_text
                })

        if not chapters_data:
            raise ValueError("पुस्तकामध्ये वाचण्यायोग्य मजकूर सापडला नाही.")

        await update_status("analyzing", 30.0, "Chapter समजून घेत आहे...")

        # 3. Process each chapter to generate structured handwritten notes
        generated_chapters: List[Dict[str, Any]] = []
        total_ch = len(chapters_data)

        for idx, ch_info in enumerate(chapters_data, start=1):
            progress_pct = 30.0 + (50.0 * (idx / total_ch))
            await update_status(
                "formatting",
                progress_pct,
                f"Important points व Notes तयार करत आहे... ({idx}/{total_ch})"
            )

            chapter_note = await self._generate_chapter_note(
                book_title=book.title,
                chapter_title=ch_info["chapter_title"],
                chapter_text=ch_info["text"]
            )
            chapter_note["chapter_number"] = idx
            chapter_note["start_page"] = ch_info.get("start_page", 1)
            chapter_note["end_page"] = ch_info.get("end_page", 1)
            generated_chapters.append(chapter_note)

        await update_status("formatting", 85.0, "Diagrams व PDF Layout तयार करत आहे...")

        # 4. Generate combined Markdown content
        markdown_content = self._build_markdown_notes(book.title, generated_chapters)

        # 5. Render Notebook-styled PDF
        from app.services.notes.pdf_note_renderer import pdf_note_renderer
        pdf_path, pdf_url, page_count = await pdf_note_renderer.render_notebook_pdf(
            book_id=book.id,
            book_title=book.title,
            chapters=generated_chapters
        )

        await update_status("completed", 100.0, "Notes तयार आहेत 🎉")

        return {
            "book_id": book.id,
            "title": f"{book.title} - Handwritten Notes",
            "chapter_count": len(generated_chapters),
            "page_count": page_count,
            "chapters": generated_chapters,
            "markdown_content": markdown_content,
            "pdf_path": pdf_path,
            "pdf_url": pdf_url
        }

    async def _generate_chapter_note(
        self,
        book_title: str,
        chapter_title: str,
        chapter_text: str
    ) -> Dict[str, Any]:
        """
        Sends structured Marathi extraction prompt to LLM to create rich note elements.
        """
        # Trim text to prevent exceeding context while retaining complete key points
        trimmed_text = chapter_text[:12000]

        system_prompt = (
            "तू MPSC आणि स्पर्धा परीक्षांसाठी एक उत्कृष्ट शिक्षक व हस्तलिखित (Handwritten) नोट्स तज्ज्ञ आहेस.\n"
            "तुझे काम दिलेल्या मूळ मजकुरावरून अत्यंत सोप्या, सुंदर, आकर्षक आणि परीक्षेसाठी १००% उपयुक्त मराठी हस्तलिखित नोट्स तयार करणे आहे.\n"
            "नियम:\n"
            "१. भाषा: ~९८% शुद्ध, सोपी व प्रभावी मराठी. इंग्रजी शब्द जास्तीत जास्त २% (केवळ तांत्रिक संज्ञा जसे की SQL, Python, GDP, Articles, Acts इत्यादी).\n"
            "२. मूळ मजकुरावरच पूर्णपणे आधारित राहा (Factually 100% Grounded, no hallucinations).\n"
            "३. खालील JSON फॉरमॅटमध्येच वैध JSON आउटपुट दे, कोणताही अतिरिक्त मजकूर नको."
        )

        user_prompt = f"""
पुस्तकाचे नाव: {book_title}
प्रकरण / टॉपिक: {chapter_title}

खालील मजकुराचा सखोल अभ्यास कर आणि MPSC च्या विद्यार्थ्यांसाठी आकर्षक हस्तलिखित नोट्सचा JSON तयार कर:

=== मजकूर (SOURCE CONTENT) ===
{trimmed_text}
=== मजकूर समाप्त ===

JSON SCHEMA:
{{
  "heading_mr": "मुख्य शीर्षक (उदा. १८५७ चा उठाव - पार्श्वभूमी व कारणे)",
  "subheading_mr": "उपशीर्षक किंवा विषयाची व्याप्ती",
  "short_definition_mr": "विषयाची किंवा संकल्पनेची २-३ ओळींत अत्यंत सोपी व्याख्या/प्रस्तावना",
  "important_concepts": [
    {{"title_mr": "संकल्पना १", "explanation_mr": "सोप्या भाषेत स्पष्टीकरण"}}
  ],
  "key_points": [
    "१. पहिला महत्त्वाचा मुद्दा",
    "२. दुसरा महत्त्वाचा मुद्दा",
    "३. तिसरा महत्त्वाचा मुद्दा"
  ],
  "examples": [
    "उदा. १: ऐतिहासिक किंवा व्यावहारिक उदाहरण"
  ],
  "formulas_or_laws": [
    "महत्त्वाचे कायदे / कलमे / सूत्रे (उदा. कलम १४: कायद्यापुढे समानता)"
  ],
  "table": {{
    "title_mr": "महत्त्वाचा तुलनात्मक तक्ता (असल्यास)",
    "headers": ["घटक", "वैशिष्ट्ये", "MPSC महत्त्व"],
    "rows": [
      ["मुद्दा १", "तपशील १", "महत्त्व १"],
      ["मुद्दा २", "तपशील २", "महत्त्व २"]
    ]
  }},
  "flowchart_steps": [
    "पायरी १: प्रारंभ",
    "पायरी २: मुख्य घटना / विकास",
    "पायरी ३: परिणाम / निष्कर्ष"
  ],
  "exam_points": [
    "🎯 परीक्षेसाठी अति-महत्त्वाचे: MPSC पूर्व व मुख्य परीक्षेत थेट विचारले जाणारे मुद्दे"
  ],
  "quick_revision_box": [
    "⚡ Quick Revision: परीक्षेच्या आदल्या दिवशी वाचायचे ५ मुख्य बुलेट्स"
  ],
  "common_mistakes": [
    "⚠️ विद्यार्थ्यांच्या सामान्य चुका: परीक्षेतील संभ्रम किंवा फसवे पर्याय"
  ]
}}
"""
        try:
            res_tuple = await llm_provider._execute_with_provider(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=2200
            )
            res_text = res_tuple[0] if isinstance(res_tuple, tuple) else res_tuple
            if not res_text:
                raise ValueError("No response from LLM provider")

            # Clean markdown code block if present
            cleaned = res_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            parsed = json.loads(cleaned)
            return self._normalize_chapter_dict(parsed, chapter_title)
        except Exception as e:
            logger.warning(f"[NoteGenerator] LLM JSON parse failed for chapter '{chapter_title}': {e}. Using robust Marathi heuristic generator.")
            return self._fallback_chapter_note(chapter_title, chapter_text)

    def _normalize_chapter_dict(self, data: Dict[str, Any], default_title: str) -> Dict[str, Any]:
        """Ensures all expected keys exist and are properly typed."""
        return {
            "heading_mr": data.get("heading_mr") or default_title,
            "subheading_mr": data.get("subheading_mr") or "MPSC विशेष हस्तलिखित नोट्स",
            "short_definition_mr": data.get("short_definition_mr") or "या प्रकरणातील मुख्य संकल्पनांचे सारांश रूप.",
            "important_concepts": data.get("important_concepts") or [],
            "key_points": data.get("key_points") or [],
            "examples": data.get("examples") or [],
            "formulas_or_laws": data.get("formulas_or_laws") or [],
            "table": data.get("table") or None,
            "flowchart_steps": data.get("flowchart_steps") or [],
            "exam_points": data.get("exam_points") or [],
            "quick_revision_box": data.get("quick_revision_box") or [],
            "common_mistakes": data.get("common_mistakes") or []
        }

    def _fallback_chapter_note(self, chapter_title: str, text: str) -> Dict[str, Any]:
        """Deterministic Marathi fallback notes extractor if LLM is unavailable."""
        lines = [line.strip() for line in text.split("\n") if line.strip() and len(line.strip()) > 15]
        key_lines = lines[:10] if lines else ["या प्रकरणातील महत्त्वाचा अभ्यासक्रम."]
        
        return {
            "heading_mr": chapter_title,
            "subheading_mr": "MPSC अभ्यासक्रम हस्तलिखित नोट्स",
            "short_definition_mr": f"{chapter_title} या घटकातील सर्व महत्त्वाचे मुद्दे व संकल्पना स्पर्धा परीक्षेच्या दृष्टिकोनातून येथे एकत्रित केले आहेत.",
            "important_concepts": [
                {"title_mr": f"प्रमुख संकल्पना {i+1}", "explanation_mr": line}
                for i, line in enumerate(key_lines[:3])
            ],
            "key_points": [f"{i+1}. {line}" for i, line in enumerate(key_lines[:6])],
            "examples": [f"उदा. {chapter_title} मधील महत्त्वाचा संदर्भ"],
            "formulas_or_laws": ["महत्त्वाचे कायदे व तरतुदींचे पुनरावलोकन"],
            "table": {
                "title_mr": "महत्त्वाचे तुलनात्मक मुद्दे",
                "headers": ["घटक", "वैशिष्ट्ये", "परीक्षेचे महत्त्व"],
                "rows": [
                    ["मुद्दा १", key_lines[0][:50] if key_lines else "तपशील", "उच्च"],
                    ["मुद्दा २", key_lines[1][:50] if len(key_lines) > 1 else "तपशील", "मध्यम"]
                ]
            },
            "flowchart_steps": [
                f"१. {chapter_title} प्रारंभ व पार्श्वभूमी",
                "२. मुख्य घडामोडी व घटनाक्रम",
                "३. परिणाम व MPSC निष्कर्ष"
            ],
            "exam_points": [
                f"🎯 MPSC परीक्षेसाठी {chapter_title} मधील संकल्पना व तारीख/कलम वारंवार विचारले जातात."
            ],
            "quick_revision_box": [
                f"⚡ {chapter_title} मधील प्रमुख घटकांचे नियमित उजळणी करा."
            ],
            "common_mistakes": [
                "⚠️ तारखा आणि संबंधित व्यक्तींच्या नावांमध्ये संभ्रम होऊ देऊ नका."
            ]
        }

    def _build_markdown_notes(self, book_title: str, chapters: List[Dict[str, Any]]) -> str:
        """Constructs rich GFM Markdown notes from structured chapter data."""
        md = [f"# ✍️ {book_title} — हस्तलिखित नोट्स (Handwritten Notes)\n"]
        md.append(f"> **MPSC AI शिक्षक विशेष आवृत्ती** | एकूण प्रकरणे: {len(chapters)}\n\n---\n")

        for idx, ch in enumerate(chapters, start=1):
            md.append(f"## 📖 प्रकरण {idx}: {ch['heading_mr']}\n")
            if ch.get("subheading_mr"):
                md.append(f"*{ch['subheading_mr']}*\n\n")

            md.append(f"### 📌 व्याख्या / प्रस्तावना\n{ch['short_definition_mr']}\n\n")

            if ch.get("important_concepts"):
                md.append("### 💡 महत्त्वाच्या संकल्पना\n")
                for c in ch["important_concepts"]:
                    md.append(f"- **{c.get('title_mr', '')}**: {c.get('explanation_mr', '')}\n")
                md.append("\n")

            if ch.get("key_points"):
                md.append("### 📝 मुख्य मुद्दे (Key Points)\n")
                for kp in ch["key_points"]:
                    md.append(f"- {kp}\n")
                md.append("\n")

            if ch.get("table") and ch["table"].get("headers") and ch["table"].get("rows"):
                tbl = ch["table"]
                md.append(f"### 📊 {tbl.get('title_mr', 'तुलनात्मक तक्ता')}\n\n")
                md.append("| " + " | ".join(tbl["headers"]) + " |\n")
                md.append("| " + " | ".join(["---"] * len(tbl["headers"])) + " |\n")
                for row in tbl["rows"]:
                    md.append("| " + " | ".join(str(cell) for cell in row) + " |\n")
                md.append("\n")

            if ch.get("flowchart_steps"):
                md.append("### 🔄 प्रवाह आकृती (Process Flowchart)\n")
                for step in ch["flowchart_steps"]:
                    md.append(f"➡️ **{step}**\n")
                md.append("\n")

            if ch.get("exam_points"):
                md.append("### 🎯 परीक्षेसाठी अति-महत्त्वाचे (Exam Alert)\n")
                for ep in ch["exam_points"]:
                    md.append(f"> 🎯 {ep}\n")
                md.append("\n")

            if ch.get("quick_revision_box"):
                md.append("### ⚡ Quick Revision Box\n")
                for qr in ch["quick_revision_box"]:
                    md.append(f"- ⚡ {qr}\n")
                md.append("\n")

            if ch.get("common_mistakes"):
                md.append("### ⚠️ सामान्य चुका व संभ्रम टाळा\n")
                for cm in ch["common_mistakes"]:
                    md.append(f"- ⚠️ {cm}\n")
                md.append("\n")

            md.append("---\n\n")

        return "\n".join(md)

note_generator_service = NoteGeneratorService()
