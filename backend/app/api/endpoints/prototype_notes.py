"""
FastAPI Endpoints and Interactive HTML Prototype for User-Controlled Handwritten Notes Generator.
Provides explicit user control over Subject, Scope, Chapter, Exam Target, Output Type,
and Free-Form Custom Instructions with live visual preview and PDF download.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel

from app.services.notes.user_controlled_notes_service import (
    user_controlled_notes_service,
    STANDARD_MPSC_SUBJECTS,
    OUTPUT_TYPES,
    EXAM_TARGETS
)
from app.utils.logger import logger

router = APIRouter(prefix="/prototype/notes", tags=["User-Controlled Notes Prototype"])

class UserGenerateRequest(BaseModel):
    doc_id: str
    subject: str = "इतिहास (History)"
    scope: str = "chapter"
    chapter_id: Optional[int] = None
    exam_target: str = "mpsc_prelims"
    output_type: str = "handwritten_notes"
    language: str = "mr"
    custom_instruction: Optional[str] = None

@router.post("/upload")
async def upload_document_for_prototype(
    file: UploadFile = File(...)
):
    """Uploads a PDF or TXT file and detects chapter breakdown."""
    filename = file.filename or "uploaded_document.pdf"
    if not (filename.lower().endswith(".pdf") or filename.lower().endswith(".txt")):
        raise HTTPException(status_code=400, detail="केवळ .pdf किंवा .txt फाईल्स स्वीकारल्या जातात.")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="रिकामी फाईल अपलोड करता येत नाही.")

    result = await user_controlled_notes_service.process_upload(contents, filename)
    return result

@router.post("/generate")
async def generate_user_controlled_notes(
    body: UserGenerateRequest
):
    """Generates structured Marathi notes strictly adhering to user configurations and instructions."""
    try:
        result = await user_controlled_notes_service.generate_user_controlled_notes(
            doc_id=body.doc_id,
            subject=body.subject,
            scope=body.scope,
            chapter_id=body.chapter_id,
            exam_target=body.exam_target,
            output_type=body.output_type,
            language=body.language,
            custom_instruction=body.custom_instruction
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"[PrototypeNotes] Generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Notes जनरेशन त्रुटी: {e}")

@router.get("/{doc_id}")
async def get_prototype_notes_details(doc_id: str):
    """Returns session info and generated notes JSON."""
    session = user_controlled_notes_service.get_session(doc_id)
    if not session:
        raise HTTPException(status_code=404, detail="सत्र सापडले नाही.")
    return {
        "doc_id": doc_id,
        "filename": session["filename"],
        "total_chapters": session["total_chapters"],
        "generated_note": session["generated_note"],
        "generated_chapters": session.get("generated_chapters", []),
        "pdf_url": session["pdf_url"]
    }

@router.get("/{doc_id}/pdf")
async def download_prototype_pdf(doc_id: str):
    """Serves the generated high-resolution ruled notebook PDF."""
    session = user_controlled_notes_service.get_session(doc_id)
    if not session or not session.get("pdf_path"):
        raise HTTPException(status_code=404, detail="PDF उपलब्ध नाही.")

    p = Path(session["pdf_path"])
    if not p.exists():
        raise HTTPException(status_code=404, detail="PDF फाईल सर्व्हरवर सापडली नाही.")

    return FileResponse(
        path=str(p),
        media_type="application/pdf",
        filename=f"MPSC_Notes_{session['filename']}.pdf",
        headers={"Content-Disposition": f"inline; filename=MPSC_Notes_{doc_id}.pdf"}
    )

@router.get("", response_class=HTMLResponse)
async def serve_prototype_web_app():
    """Serves the rich user-controlled configuration and live preview browser app."""
    html = """<!DOCTYPE html>
<html lang="mr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MPSC AI • User-Controlled Document Notes Generator</title>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600;700;800&family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #070B11;
      --card-bg: #0E1726;
      --card-border: #1E293B;
      --primary: #00E5FF;
      --accent: #00E676;
      --amber: #FAAD14;
      --red: #FF4D4F;
      --text: #F1F5F9;
      --text-muted: #94A3B8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Noto Sans Devanagari', 'Poppins', sans-serif;
      padding: 20px;
      line-height: 1.5;
    }
    .container { max-width: 1300px; margin: 0 auto; }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 20px;
    }
    .badge {
      background: rgba(0, 229, 255, 0.15);
      color: var(--primary);
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: bold;
      border: 1px solid var(--primary);
    }
    .grid { display: grid; grid-template-columns: 460px 1fr; gap: 20px; }
    @media (max-width: 980px) { .grid { grid-template-columns: 1fr; } }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 18px;
      margin-bottom: 16px;
    }
    h2 { font-size: 16px; margin-bottom: 12px; color: var(--primary); display: flex; align-items: center; gap: 6px; }
    label { font-size: 12px; color: var(--text-muted); display: block; margin-bottom: 4px; font-weight: 600; }
    input[type="file"], select, textarea, input[type="text"] {
      width: 100%;
      background: #141E33;
      border: 1px solid var(--card-border);
      color: var(--text);
      padding: 9px 12px;
      border-radius: 8px;
      font-family: inherit;
      font-size: 13px;
      margin-bottom: 12px;
      outline: none;
    }
    input[type="file"]:focus, select:focus, textarea:focus, input[type="text"]:focus { border-color: var(--primary); }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    button {
      width: 100%;
      background: linear-gradient(135deg, #00E5FF, #00B0FF);
      color: #000;
      border: none;
      padding: 11px 16px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s;
    }
    button:hover { opacity: 0.92; transform: translateY(-1px); }
    button:disabled { background: #334155; color: #64748B; cursor: not-allowed; transform: none; }
    .btn-secondary { background: #1E293B; color: var(--text); margin-top: 8px; }
    .quick-chips { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 12px; }
    .chip {
      background: #141E33;
      border: 1px solid var(--card-border);
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 11px;
      cursor: pointer;
    }
    .chip:hover { border-color: var(--primary); color: var(--primary); }
    .status-box {
      padding: 10px;
      border-radius: 8px;
      font-size: 12px;
      margin-top: 10px;
      display: none;
    }
    .status-box.loading { background: rgba(0, 229, 255, 0.1); border: 1px solid var(--primary); color: var(--primary); display: block; }
    .status-box.success { background: rgba(0, 230, 118, 0.1); border: 1px solid var(--accent); color: var(--accent); display: block; }
    .status-box.error { background: rgba(255, 77, 79, 0.1); border: 1px solid var(--red); color: var(--red); display: block; }

    /* Notebook Preview Visualizer */
    .notebook-viewer {
      background: #FFFFFF;
      color: #1A1A1A;
      border-radius: 10px;
      padding: 28px 36px;
      min-height: 600px;
      background-image: linear-gradient(#E3EEF9 1px, transparent 1px);
      background-size: 100% 24px;
      box-shadow: 0 15px 35px rgba(0,0,0,0.6);
      border-left: 2px solid #FFB4B4;
    }
    .notebook-header {
      border-bottom: 2px solid #00A8CC;
      padding-bottom: 6px;
      margin-bottom: 14px;
      color: #007791;
      font-weight: bold;
      font-size: 13px;
      display: flex;
      justify-content: space-between;
    }
    .note-h1 { font-size: 20px; color: #007791; font-weight: 800; margin-bottom: 4px; }
    .note-h2 { font-size: 13px; color: #555; font-style: italic; margin-bottom: 14px; }
    .box {
      border-radius: 8px;
      padding: 10px 14px;
      margin-bottom: 12px;
      font-size: 12px;
    }
    .box-blue { background: #E6F7FF; border: 1.5px solid #1890FF; }
    .box-amber { background: #FFF7E6; border: 1.5px solid #FFA940; }
    .box-green { background: #F6FFED; border: 1.5px solid #52C41A; }
    .box-red { background: #FFF1F0; border: 1.5px solid #FF4D4F; }
    .box-yellow { background: #FEFFE6; border: 1.5px solid #FAAD14; }
    .bullets { margin-left: 18px; margin-bottom: 12px; font-size: 12px; }
    .bullets li { margin-bottom: 5px; }
    .table-container table { width: 100%; border-collapse: collapse; margin-bottom: 12px; font-size: 11px; }
    .table-container th, .table-container td { border: 1px solid #ADC6FF; padding: 5px 8px; text-align: left; }
    .table-container th { background: #F0F5FF; font-weight: bold; }
    .empty-preview {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 500px;
      color: var(--text-muted);
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1 style="font-size: 20px; font-weight: 800;">⚙️ MPSC AI • User-Controlled Notes Generator</h1>
        <p style="font-size: 12px; color: var(--text-muted);">Configure Subject, Chapter, Exam Target, Style, and Custom Instructions</p>
      </div>
      <div class="badge">PROTOTYPE ONLY</div>
    </header>

    <div class="grid">
      <!-- Control Form -->
      <div>
        <!-- Step 1: Upload -->
        <div class="card">
          <h2>📁 १. फाईल अपलोड (PDF / TXT)</h2>
          <label>अभ्यास साहित्य निवडा (.pdf किंवा .txt):</label>
          <input type="file" id="fileInput" accept=".pdf,.txt">
          <button id="uploadBtn" onclick="uploadFile()">📤 Upload & Load Config Options</button>
          <div id="uploadStatus" class="status-box"></div>
        </div>

        <!-- Step 2: Full User Configuration -->
        <div class="card" id="configCard" style="display:none;">
          <h2>🎛️ २. वापरकर्ता नियंत्रण (User Configuration)</h2>
          
          <!-- Subject Selector -->
          <label>A. विषय (Subject):</label>
          <select id="subjectSelect" onchange="checkCustomSubject()">
            <option value="इतिहास (History)">इतिहास (History)</option>
            <option value="महाराष्ट्राचा इतिहास (Maharashtra History)">महाराष्ट्राचा इतिहास (Maharashtra History)</option>
            <option value="भूगोल (Geography)">भूगोल (Geography)</option>
            <option value="महाराष्ट्राचा भूगोल (Maharashtra Geography)">महाराष्ट्राचा भूगोल (Maharashtra Geography)</option>
            <option value="राज्यशास्त्र (Polity & Governance)">राज्यशास्त्र (Polity & Governance)</option>
            <option value="अर्थशास्त्र (Economics & Planning)">अर्थशास्त्र (Economics & Planning)</option>
            <option value="सामान्य विज्ञान व तंत्रज्ञान (General Science)">सामान्य विज्ञान व तंत्रज्ञान (General Science)</option>
            <option value="पर्यावरण व जैवविविधता (Environment)">पर्यावरण व जैवविविधता (Environment)</option>
            <option value="चालू घडामोडी (Current Affairs)">चालू घडामोडी (Current Affairs)</option>
            <option value="महाराष्ट्र विशेष (Maharashtra Special)">महाराष्ट्र विशेष (Maharashtra Special)</option>
            <option value="सामान्य ज्ञान (General Knowledge)">सामान्य ज्ञान (General Knowledge)</option>
            <option value="custom">✍️ सानुकूल विषय (Custom Subject)...</option>
          </select>
          <input type="text" id="customSubjectInput" placeholder="उदा. प्राचीन भारताचा इतिहास" style="display:none;">

          <!-- Scope & Chapter Selector -->
          <div class="row">
            <div>
              <label>B. व्याप्ती (Scope):</label>
              <select id="scopeSelect" onchange="onScopeChanged()">
                <option value="chapter">प्रकरणानुसार (Specific Chapter)</option>
                <option value="full_file">संपूर्ण फाईल (Full Book / All Chapters)</option>
              </select>
            </div>
            <div>
              <label>C. प्रकरण (Chapter):</label>
              <select id="chapterSelect"></select>
            </div>
          </div>

          <!-- Exam Target & Output Style -->
          <div class="row">
            <div>
              <label>D. परीक्षा (Target Exam):</label>
              <select id="examSelect">
                <option value="mpsc_prelims">MPSC पूर्व परीक्षा (Prelims)</option>
                <option value="mpsc_mains">MPSC मुख्य परीक्षा (Mains)</option>
                <option value="prelims_mains">पूर्व + मुख्य संयुक्त (Combined)</option>
                <option value="general">सर्व स्पर्धा परीक्षा (General)</option>
              </select>
            </div>
            <div>
              <label>E. नोट्स शैली (Output Type):</label>
              <select id="outputTypeSelect">
                <option value="handwritten_notes">✍️ Handwritten Notes (रुल्ड नोटबुक)</option>
                <option value="short_revision">⚡ Short Revision Notes (संक्षिप्त)</option>
                <option value="detailed_notes">📚 Detailed Comprehensive Notes (सखोल)</option>
                <option value="one_day_revision">🎯 One-Day Revision Sheet (२ पाने)</option>
                <option value="pyq_focused">📝 PYQ Focused Points</option>
                <option value="mcq_focused">❓ 30+ MPSC MCQs with Solutions</option>
                <option value="summary">📌 सोप्या भाषेत Summary</option>
              </select>
            </div>
          </div>

          <!-- Free-Form User Instruction (PRIMARY) -->
          <label style="color:var(--primary); margin-top:6px;">G. तुमची विशेष आज्ञा (Custom Instruction - सर्वोच्च प्राधान्य):</label>
          <textarea id="instructionInput" rows="3" placeholder="उदा. या chapter चे MPSC Prelims साठी handwritten notes बनव. महत्त्वाच्या तारखांची timeline, flowcharts आणि शेवटी quick revision दे."></textarea>

          <div class="quick-chips">
            <span class="chip" onclick="setPrompt('फक्त MPSC Prelims साठी महत्त्वाचे मुद्दे व वस्तुनिष्ठ तथ्ये दे.')">🎯 Prelims Points</span>
            <span class="chip" onclick="setPrompt('हा chapter ३ पानांत revise करता येईल अशा Handwritten Notes बनव.')">📝 3-Page Notes</span>
            <span class="chip" onclick="setPrompt('सर्व महत्त्वाच्या तारखा व घटनांचा Chronological तक्ता बनव.')">📅 Dates & Timeline</span>
            <span class="chip" onclick="setPrompt('कारणे आणि परिणाम यांची तुलना करणारा Table तयार कर.')">📊 Compare Table</span>
            <span class="chip" onclick="setPrompt('या chapter मधून ३० संभाव्य MPSC MCQs स्पष्टीकरणासह तयार कर.')">❓ 30 MCQs</span>
          </div>

          <button id="generateBtn" onclick="generateNotes()">✨ Generate Configured Notes</button>
          <div id="genStatus" class="status-box"></div>
        </div>

        <!-- Step 3: Download & Regenerate -->
        <div class="card" id="downloadCard" style="display:none;">
          <h2>📥 ३. PDF डाउनलोड व फेरबदल</h2>
          <button onclick="downloadPDF()" style="background:#00E676; color:#000;">📄 Download Ruled Notebook PDF</button>
          <button class="btn-secondary" onclick="generateNotes()">🔄 Regenerate with Updated Config</button>
        </div>
      </div>

      <!-- Live Visual Preview -->
      <div>
        <div class="card" style="padding: 16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <h2>📖 Live Notebook Preview</h2>
            <div id="pdfActionBtns" style="display:none;">
              <a id="openPdfLink" target="_blank" style="color:var(--primary); font-size:12px; font-weight:bold; text-decoration:none;">🔗 Open Full PDF in New Tab</a>
            </div>
          </div>

          <div id="previewContainer" class="notebook-viewer">
            <div class="empty-preview" id="emptyState">
              <div style="font-size: 42px; margin-bottom: 10px;">📝</div>
              <h3>कोणतीही फाईल निवडलेली नाही</h3>
              <p style="font-size: 12px; margin-top: 6px;">डावीकडे PDF/TXT अपलोड करा, विषय व आज्ञा निवडा आणि 'Generate' वर क्लिक करा.<br/>त्यानंतर येथे अस्सल रुल्ड नोटबुक शैलीतील हस्तलिखित नोट्स दिसतील.</p>
            </div>
            <div id="notesRender" style="display:none;"></div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let currentDocId = null;

    function setPrompt(text) {
      document.getElementById('instructionInput').value = text;
    }

    function checkCustomSubject() {
      const select = document.getElementById('subjectSelect');
      const customInput = document.getElementById('customSubjectInput');
      if (select.value === 'custom') {
        customInput.style.display = 'block';
      } else {
        customInput.style.display = 'none';
      }
    }

    function onScopeChanged() {
      const scope = document.getElementById('scopeSelect').value;
      const chapterSelect = document.getElementById('chapterSelect');
      if (scope === 'full_file') {
        chapterSelect.disabled = true;
      } else {
        chapterSelect.disabled = false;
      }
    }

    async function uploadFile() {
      const fileInput = document.getElementById('fileInput');
      if (!fileInput.files || fileInput.files.length === 0) {
        alert('कृपया PDF किंवा TXT फाईल निवडा.');
        return;
      }

      const file = fileInput.files[0];
      const formData = new FormData();
      formData.append('file', file);

      const status = document.getElementById('uploadStatus');
      const btn = document.getElementById('uploadBtn');
      status.className = 'status-box loading';
      status.innerText = 'फाईल वाचत आहे व पर्याय लोड करत आहे...';
      btn.disabled = true;

      try {
        const resp = await fetch('/prototype/notes/upload', {
          method: 'POST',
          body: formData
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || 'Upload failed');

        currentDocId = data.id;
        status.className = 'status-box success';
        status.innerText = `यशस्वी! ${data.total_chapters} प्रकरणे आढळली.`;

        // Populate chapter dropdown
        const select = document.getElementById('chapterSelect');
        select.innerHTML = '';
        data.chapters.forEach(ch => {
          const opt = document.createElement('option');
          opt.value = ch.id;
          opt.innerText = `${ch.title}`;
          select.appendChild(opt);
        });

        document.getElementById('configCard').style.display = 'block';
      } catch (err) {
        status.className = 'status-box error';
        status.innerText = `त्रुटी: ${err.message}`;
      } finally {
        btn.disabled = false;
      }
    }

    async function generateNotes() {
      if (!currentDocId) return;

      const subjectSel = document.getElementById('subjectSelect').value;
      const customSubj = document.getElementById('customSubjectInput').value;
      const subject = (subjectSel === 'custom' && customSubj.trim()) ? customSubj.trim() : subjectSel;

      const scope = document.getElementById('scopeSelect').value;
      const chapterId = scope === 'full_file' ? 0 : (parseInt(document.getElementById('chapterSelect').value) || 1);
      const exam = document.getElementById('examSelect').value;
      const outputType = document.getElementById('outputTypeSelect').value;
      const instruction = document.getElementById('instructionInput').value;

      const status = document.getElementById('genStatus');
      const btn = document.getElementById('generateBtn');

      status.className = 'status-box loading';
      status.innerText = 'ChatGPT द्वारे सानुकूलित नोट्स तयार होत आहेत (User-Controlled RAG)...';
      btn.disabled = true;

      try {
        const resp = await fetch('/prototype/notes/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            doc_id: currentDocId,
            subject: subject,
            scope: scope,
            chapter_id: chapterId,
            exam_target: exam,
            output_type: outputType,
            language: 'mr',
            custom_instruction: instruction
          })
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || 'Generation failed');

        status.className = 'status-box success';
        status.innerText = `Notes यशस्वीपणे तयार झाल्या (${data.page_count} Pages, ${data.total_processed_chapters} Chapters)!`;

        document.getElementById('downloadCard').style.display = 'block';
        document.getElementById('pdfActionBtns').style.display = 'block';
        document.getElementById('openPdfLink').href = data.pdf_url;

        renderNotesPreview(data.structured_note, data.subject, data.all_chapters_notes);
      } catch (err) {
        status.className = 'status-box error';
        status.innerText = `त्रुटी: ${err.message}`;
      } finally {
        btn.disabled = false;
      }
    }

    function renderNotesPreview(note, subject, allChapters) {
      document.getElementById('emptyState').style.display = 'none';
      const render = document.getElementById('notesRender');
      render.style.display = 'block';

      let chaptersList = allChapters && allChapters.length > 0 ? allChapters : [note];
      let html = '';

      chaptersList.forEach((chNote, cIdx) => {
        html += `
          <div style="${cIdx > 0 ? 'margin-top: 30px; padding-top: 20px; border-top: 2px dashed #00A8CC;' : ''}">
            <div class="notebook-header">
              <span>MPSC AI • ${subject}</span>
              <span>प्रकरण ${cIdx + 1} / ${chaptersList.length}</span>
            </div>
            <div class="note-h1">✍️ ${chNote.heading_mr || 'अभ्यास नोट्स'}</div>
            <div class="note-h2">${chNote.subheading_mr || subject}</div>
        `;

        if (chNote.short_definition_mr) {
          html += `
            <div class="box box-blue">
              <b>📌 व्याख्या / प्रस्तावना:</b><br/>
              ${chNote.short_definition_mr}
            </div>
          `;
        }

        if (chNote.key_points && chNote.key_points.length > 0) {
          html += `<div style="font-weight:bold; color:#007791; margin: 10px 0 4px 0;">📝 मुख्य मुद्दे:</div><ul class="bullets">`;
          chNote.key_points.forEach(p => { html += `<li>${p}</li>`; });
          html += `</ul>`;
        }

        if (chNote.important_dates && chNote.important_dates.length > 0) {
          html += `
            <div class="box box-amber">
              <b>📅 महत्त्वाच्या तारखा व कालक्रम:</b><br/>
              ${chNote.important_dates.join('<br/>')}
            </div>
          `;
        }

        if (chNote.important_personalities && chNote.important_personalities.length > 0) {
          html += `
            <div class="box box-green">
              <b>👤 महत्त्वाच्या व्यक्ती व कार्य:</b><br/>
              ${chNote.important_personalities.join('<br/>')}
            </div>
          `;
        }

        if (chNote.memory_tricks && chNote.memory_tricks.length > 0) {
          html += `
            <div class="box box-yellow">
              <b>💡 लक्षात ठेवण्याची ट्रिक:</b><br/>
              ${chNote.memory_tricks.join('<br/>')}
            </div>
          `;
        }

        if (chNote.table && chNote.table.headers && chNote.table.rows) {
          html += `
            <div class="table-container">
              <div style="font-weight:bold; color:#007791; margin-bottom:4px;">📊 ${chNote.table.title_mr || 'तुलनात्मक तक्ता'}:</div>
              <table>
                <thead><tr>${chNote.table.headers.map(h => `<th>${h}</th>`).join('')}</tr></thead>
                <tbody>
                  ${chNote.table.rows.map(row => `<tr>${row.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}
                </tbody>
              </table>
            </div>
          `;
        }

        if (chNote.exam_points && chNote.exam_points.length > 0) {
          html += `
            <div class="box box-amber">
              <b>🎯 MPSC परीक्षेसाठी अति-महत्त्वाचे:</b><br/>
              ${chNote.exam_points.join('<br/>')}
            </div>
          `;
        }

        if (chNote.quick_revision_box && chNote.quick_revision_box.length > 0) {
          html += `
            <div class="box box-yellow">
              <b>⚡ Quick Revision (उजळणी):</b><br/>
              ${chNote.quick_revision_box.join('<br/>')}
            </div>
          `;
        }

        if (chNote.common_mistakes && chNote.common_mistakes.length > 0) {
          html += `
            <div class="box box-red">
              <b>⚠️ संभ्रम व सामान्य चुका टाळा:</b><br/>
              ${chNote.common_mistakes.join('<br/>')}
            </div>
          `;
        }

        html += `</div>`;
      });

      render.innerHTML = html;
    }

    function downloadPDF() {
      if (!currentDocId) return;
      window.open(`/prototype/notes/${currentDocId}/pdf`, '_blank');
    }
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html)
