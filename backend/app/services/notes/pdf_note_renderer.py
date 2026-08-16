"""
Visual Handwritten Notebook PDF Renderer for MPSC AI.
Generates printable, notebook-styled PDF pages with ruled lines, margin,
colorful callout boxes, comparison tables, and Devanagari typography.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from app.config import settings
from app.utils.logger import logger

class NumberedNotebookCanvas(canvas.Canvas):
    """
    Custom Canvas that draws notebook ruled lines, left red margin line,
    header, and dynamic page numbering 'पृष्ठ X / Y'.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_notebook_background(num_pages)
            super().showPage()
        super().save()

    def draw_notebook_background(self, total_pages: int):
        width, height = A4
        self.saveState()

        # 1. White paper background
        self.setFillColor(colors.HexColor("#FFFFFF"))
        self.rect(0, 0, width, height, fill=1, stroke=0)

        # 2. Notebook ruled horizontal lines (light soft blue)
        self.setStrokeColor(colors.HexColor("#E3EEF9"))
        self.setLineWidth(0.6)
        line_start_y = 45
        line_end_y = height - 55
        spacing = 22
        current_y = line_start_y
        while current_y <= line_end_y:
            self.line(30, current_y, width - 30, current_y)
            current_y += spacing

        # 3. Red left vertical margin line
        self.setStrokeColor(colors.HexColor("#FFB4B4"))
        self.setLineWidth(1.2)
        self.line(65, 35, 65, height - 35)

        # 4. Top Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#007791"))
        self.drawString(75, height - 35, "MPSC AI • हस्तलिखित अभ्यास नोट्स")

        self.setStrokeColor(colors.HexColor("#00A8CC"))
        self.setLineWidth(0.8)
        self.line(75, height - 40, width - 35, height - 40)

        # 5. Footer (Page Numbering)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#666666"))
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(width - 35, 25, page_str)
        self.drawString(75, 25, "MJ AI अभ्यास सहाय्यक")

        self.restoreState()


class PDFNoteRenderer:
    """
    Renders structured note data into an authentic notebook-style PDF.
    """
    def __init__(self):
        self._setup_fonts()

    def _setup_fonts(self):
        """Registers Devanagari font if available on system or uses clean Unicode font."""
        self.font_regular = "Helvetica"
        self.font_bold = "Helvetica-Bold"

        font_paths = [
            "C:/Windows/Fonts/Nirmala.ttc",
            "C:/Windows/Fonts/mangal.ttf",
            "C:/Windows/Fonts/aparaj.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.otf"
        ]

        for p in font_paths:
            if os.path.exists(p):
                try:
                    font_name = "DevanagariFont"
                    pdfmetrics.registerFont(TTFont(font_name, p))
                    self.font_regular = font_name
                    self.font_bold = font_name
                    logger.info(f"[PDFNoteRenderer] Registered Unicode font from: {p}")
                    break
                except Exception as font_err:
                    logger.debug(f"[PDFNoteRenderer] Font register note for {p}: {font_err}")

    async def render_notebook_pdf(
        self,
        book_id: int,
        book_title: str,
        chapters: List[Dict[str, Any]]
    ) -> Tuple[str, str, int]:
        """
        Renders chapters into a notebook PDF file on disk.
        Returns: (file_path, api_url, page_count)
        """
        output_dir = Path("data/notes")
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = output_dir / f"notes_book_{book_id}.pdf"

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            leftMargin=75,
            rightMargin=35,
            topMargin=55,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()

        # Custom Handwritten Styles
        title_style = ParagraphStyle(
            'BookTitle',
            parent=styles['Heading1'],
            fontName=self.font_bold,
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0D1B2A"),
            spaceAfter=8
        )

        chapter_title_style = ParagraphStyle(
            'ChapterTitle',
            parent=styles['Heading2'],
            fontName=self.font_bold,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#005670"),
            spaceBefore=12,
            spaceAfter=6
        )

        subheading_style = ParagraphStyle(
            'Subheading',
            fontName=self.font_regular,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#4A5568"),
            spaceAfter=10
        )

        body_style = ParagraphStyle(
            'NoteBody',
            parent=styles['Normal'],
            fontName=self.font_regular,
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#1A202C")
        )

        box_body_style = ParagraphStyle(
            'BoxBody',
            parent=styles['Normal'],
            fontName=self.font_regular,
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#2D3748")
        )

        box_header_style = ParagraphStyle(
            'BoxHeader',
            fontName=self.font_bold,
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#0D1B2A")
        )

        story = []

        # Cover / Header Banner
        story.append(Paragraph(f"✍️ {book_title}", title_style))
        story.append(Paragraph("<b>MPSC AI • हस्तलिखित अभ्यास नोट्स</b>", subheading_style))
        story.append(Spacer(1, 10))

        for idx, ch in enumerate(chapters, start=1):
            if idx > 1:
                story.append(PageBreak())

            # Chapter Title
            heading_text = f"प्रकरण {idx}: {ch.get('heading_mr', 'अध्याय')}"
            story.append(Paragraph(heading_text, chapter_title_style))
            if ch.get("subheading_mr"):
                story.append(Paragraph(f"<i>{ch['subheading_mr']}</i>", subheading_style))

            # 1. Definition Box (Soft Cyan Theme)
            if ch.get("short_definition_mr"):
                def_p = Paragraph(f"<b>📌 परिचय:</b><br/>{ch['short_definition_mr']}", box_body_style)
                def_table = Table([[def_p]], colWidths=[480])
                def_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#E6F7FF")),
                    ('BOX', (0, 0), (-1, -1), 1.0, colors.HexColor("#1890FF")),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(def_table)
                story.append(Spacer(1, 8))

            # 2. Key Points
            if ch.get("key_points"):
                story.append(Paragraph("<b>📝 मुख्य मुद्दे:</b>", box_header_style))
                story.append(Spacer(1, 4))
                for kp in ch["key_points"]:
                    story.append(Paragraph(f"• {kp}", body_style))
                    story.append(Spacer(1, 3))
                story.append(Spacer(1, 6))

            # 2a. Important Dates & Timelines
            if ch.get("important_dates"):
                story.append(Paragraph("<b>📅 महत्त्वाच्या तारखा:</b>", box_header_style))
                story.append(Spacer(1, 4))
                for d in ch["important_dates"]:
                    story.append(Paragraph(f"• {d}", body_style))
                    story.append(Spacer(1, 3))
                story.append(Spacer(1, 6))

            # 2b. Important Personalities
            if ch.get("important_personalities"):
                story.append(Paragraph("<b>👤 महत्त्वाच्या व्यक्ती:</b>", box_header_style))
                story.append(Spacer(1, 4))
                for p in ch["important_personalities"]:
                    story.append(Paragraph(f"• {p}", body_style))
                    story.append(Spacer(1, 3))
                story.append(Spacer(1, 6))

            # 2c. Memory Tricks (Soft Green Theme)
            if ch.get("memory_tricks"):
                trick_items = "<br/>".join([f"💡 {tr}" for tr in ch["memory_tricks"]])
                trick_p = Paragraph(f"<b>💡 लक्षात ठेवण्याची युक्ती:</b><br/>{trick_items}", box_body_style)
                trick_table = Table([[trick_p]], colWidths=[480])
                trick_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F6FFED")),
                    ('BOX', (0, 0), (-1, -1), 1.0, colors.HexColor("#52C41A")),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(trick_table)
                story.append(Spacer(1, 8))

            # 3. Important Concepts
            if ch.get("important_concepts"):
                story.append(Paragraph("<b>💡 महत्त्वाच्या संकल्पना:</b>", box_header_style))
                story.append(Spacer(1, 4))
                for c in ch["important_concepts"]:
                    c_title = c.get("title_mr", "")
                    c_exp = c.get("explanation_mr", "")
                    story.append(Paragraph(f"<b>{c_title}:</b> {c_exp}", body_style))
                    story.append(Spacer(1, 3))
                story.append(Spacer(1, 6))

            # 4. Tables if present
            if ch.get("table") and ch["table"].get("headers") and ch["table"].get("rows"):
                tbl_data = ch["table"]
                story.append(Paragraph(f"<b>📊 {tbl_data.get('title_mr', 'तुलनात्मक तक्ता')}:</b>", box_header_style))
                story.append(Spacer(1, 4))
                
                table_matrix = [[Paragraph(f"<b>{h}</b>", box_header_style) for h in tbl_data["headers"]]]
                for row in tbl_data["rows"]:
                    table_matrix.append([Paragraph(str(cell), box_body_style) for cell in row])
                
                col_w = 480 / max(1, len(tbl_data["headers"]))
                rendered_table = Table(table_matrix, colWidths=[col_w] * len(tbl_data["headers"]))
                rendered_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F0F5FF")),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#ADC6FF")),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(rendered_table)
                story.append(Spacer(1, 8))

            # 5. Exam High-Yield Points Box (Soft Amber/Orange)
            if ch.get("exam_points"):
                exam_items = "<br/>".join([f"🎯 {ep}" for ep in ch["exam_points"]])
                exam_p = Paragraph(f"<b>🎯 MPSC परीक्षेसाठी महत्त्वाचे:</b><br/>{exam_items}", box_body_style)
                exam_table = Table([[exam_p]], colWidths=[480])
                exam_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFF7E6")),
                    ('BOX', (0, 0), (-1, -1), 1.0, colors.HexColor("#FFA940")),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(exam_table)
                story.append(Spacer(1, 8))

            # 6. Quick Revision Box (Soft Yellow Theme)
            if ch.get("quick_revision_box"):
                rev_items = "<br/>".join([f"⚡ {qr}" for qr in ch["quick_revision_box"]])
                rev_p = Paragraph(f"<b>⚡ झटपट उजळणी:</b><br/>{rev_items}", box_body_style)
                rev_table = Table([[rev_p]], colWidths=[480])
                rev_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEFFE6")),
                    ('BOX', (0, 0), (-1, -1), 1.0, colors.HexColor("#FAAD14")),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(rev_table)
                story.append(Spacer(1, 8))

            # 7. Common Mistakes / Traps (Soft Red Theme)
            if ch.get("common_mistakes"):
                mistake_items = "<br/>".join([f"⚠️ {cm}" for cm in ch["common_mistakes"]])
                mistake_p = Paragraph(f"<b>⚠️ गोंधळाचे मुद्दे:</b><br/>{mistake_items}", box_body_style)
                mistake_table = Table([[mistake_p]], colWidths=[480])
                mistake_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFF1F0")),
                    ('BOX', (0, 0), (-1, -1), 1.0, colors.HexColor("#FF4D4F")),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(mistake_table)
                story.append(Spacer(1, 8))

        # Build PDF with custom notebook canvas
        doc.build(story, canvasmaker=NumberedNotebookCanvas)

        # Estimate page count
        estimated_pages = max(1, len(chapters))
        pdf_url = f"/api/notes/{book_id}/download"
        logger.info(f"[PDFNoteRenderer] Successfully generated notebook PDF: {pdf_path} ({estimated_pages} pages)")
        return str(pdf_path), pdf_url, estimated_pages

pdf_note_renderer = PDFNoteRenderer()
