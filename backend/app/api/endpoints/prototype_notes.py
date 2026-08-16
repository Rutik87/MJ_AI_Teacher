"""
FastAPI Endpoints and Interactive HTML Prototype for Browser-Only Handwritten Notes Validation.
Allows testing PDF/TXT upload, chapter detection, ChatGPT structured notes generation,
and live visual PDF preview/download directly in the browser.
"""

from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel

from app.services.notes.prototype_notes_service import prototype_notes_service
from app.utils.logger import logger

router = APIRouter(prefix="/prototype/notes", tags=["Prototype Notes"])

class GenerateRequest(BaseModel):
    doc_id: str
    chapter_id: Optional[int] = None
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

    result = await prototype_notes_service.process_upload(contents, filename)
    return result

@router.post("/generate")
async def generate_prototype_notes(
    body: GenerateRequest
):
    """Generates structured Marathi handwritten notes via ChatGPT."""
    try:
        result = await prototype_notes_service.generate_chapter_notes(
            doc_id=body.doc_id,
            chapter_id=body.chapter_id,
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
    """Returns metadata and generated structured notes JSON."""
    session = prototype_notes_service.get_session(doc_id)
    if not session:
        raise HTTPException(status_code=404, detail="सत्र सापडले नाही.")
    return {
        "doc_id": doc_id,
        "filename": session["filename"],
        "total_chapters": session["total_chapters"],
        "generated_note": session["generated_note"],
        "pdf_url": session["pdf_url"]
    }

@router.get("/{doc_id}/pdf")
async def download_prototype_pdf(doc_id: str):
    """Serves the generated high-resolution ruled notebook PDF."""
    session = prototype_notes_service.get_session(doc_id)
    if not session or not session.get("pdf_path"):
        raise HTTPException(status_code=404, detail="PDF उपलब्ध नाही.")

    p = Path(session["pdf_path"])
    if not p.exists():
        raise HTTPException(status_code=404, detail="PDF फाईल सर्व्हरवर सापडली नाही.")

    return FileResponse(
        path=str(p),
        media_type="application/pdf",
        filename=f"Handwritten_Notes_{session['filename']}.pdf",
        headers={"Content-Disposition": f"inline; filename=Handwritten_Notes_{doc_id}.pdf"}
    )

@router.get("", response_class=HTMLResponse)
async def serve_prototype_web_app():
    """Serves the interactive browser UI for validating handwritten notes."""
    html = """<!DOCTYPE html>
<html lang="mr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MPSC AI • Handwritten Notes Browser Prototype</title>
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
      padding: 24px;
      line-height: 1.6;
    }
    .container { max-width: 1200px; margin: 0 auto; }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 24px;
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
    .grid { display: grid; grid-template-columns: 380px 1fr; gap: 24px; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 20px;
      margin-bottom: 20px;
    }
    h2 { font-size: 18px; margin-bottom: 14px; color: var(--primary); display: flex; align-items: center; gap: 8px; }
    label { font-size: 13px; color: var(--text-muted); display: block; margin-bottom: 6px; }
    input[type="file"], select, textarea {
      width: 100%;
      background: #141E33;
      border: 1px solid var(--card-border);
      color: var(--text);
      padding: 10px 14px;
      border-radius: 10px;
      font-family: inherit;
      font-size: 13px;
      margin-bottom: 14px;
      outline: none;
    }
    input[type="file"]:focus, select:focus, textarea:focus { border-color: var(--primary); }
    button {
      width: 100%;
      background: linear-gradient(135deg, #00E5FF, #00B0FF);
      color: #000;
      border: none;
      padding: 12px 20px;
      border-radius: 10px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s;
    }
    button:hover { opacity: 0.92; transform: translateY(-1px); }
    button:disabled { background: #334155; color: #64748B; cursor: not-allowed; transform: none; }
    .btn-secondary {
      background: #1E293B;
      color: var(--text);
      margin-top: 8px;
    }
    .quick-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
    .chip {
      background: #141E33;
      border: 1px solid var(--card-border);
      padding: 5px 10px;
      border-radius: 8px;
      font-size: 11px;
      cursor: pointer;
    }
    .chip:hover { border-color: var(--primary); color: var(--primary); }
    .status-box {
      padding: 12px;
      border-radius: 10px;
      font-size: 13px;
      margin-top: 14px;
      display: none;
    }
    .status-box.loading { background: rgba(0, 229, 255, 0.1); border: 1px solid var(--primary); color: var(--primary); display: block; }
    .status-box.success { background: rgba(0, 230, 118, 0.1); border: 1px solid var(--accent); color: var(--accent); display: block; }
    .status-box.error { background: rgba(255, 77, 79, 0.1); border: 1px solid var(--red); color: var(--red); display: block; }
    
    /* Notebook Preview Visualizer */
    .notebook-viewer {
      background: #FFFFFF;
      color: #1A1A1A;
      border-radius: 12px;
      padding: 30px 40px;
      min-height: 600px;
      position: relative;
      background-image: linear-gradient(#E3EEF9 1px, transparent 1px);
      background-size: 100% 24px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.6);
      border-left: 2px solid #FFB4B4;
    }
    .notebook-header {
      border-bottom: 2px solid #00A8CC;
      padding-bottom: 8px;
      margin-bottom: 16px;
      color: #007791;
      font-weight: bold;
      font-size: 14px;
      display: flex;
      justify-content: space-between;
    }
    .note-h1 { font-size: 22px; color: #007791; font-weight: 800; margin-bottom: 6px; }
    .note-h2 { font-size: 14px; color: #555; font-style: italic; margin-bottom: 16px; }
    .box {
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 14px;
      font-size: 13px;
    }
    .box-blue { background: #E6F7FF; border: 1.5px solid #1890FF; }
    .box-amber { background: #FFF7E6; border: 1.5px solid #FFA940; }
    .box-green { background: #F6FFED; border: 1.5px solid #52C41A; }
    .box-red { background: #FFF1F0; border: 1.5px solid #FF4D4F; }
    .box-yellow { background: #FEFFE6; border: 1.5px solid #FAAD14; }
    .bullets { margin-left: 18px; margin-bottom: 14px; font-size: 13px; }
    .bullets li { margin-bottom: 6px; }
    .table-container table { width: 100%; border-collapse: collapse; margin-bottom: 14px; font-size: 12px; }
    .table-container th, .table-container td { border: 1px solid #ADC6FF; padding: 6px 10px; text-align: left; }
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
        <h1 style="font-size: 22px; font-weight: 800;">✍️ MPSC AI • Handwritten Notes Generator</h1>
        <p style="font-size: 12px; color: var(--text-muted);">Browser Prototype Validation • ChatGPT Grounded Notes & Ruled Notebook Layout</p>
      </div>
      <div class="badge">PROTOTYPE ONLY</div>
    </header>

    <div class="grid">
      <!-- Control Panel -->
      <div>
        <div class="card">
          <h2>📁 १. फाईल अपलोड (PDF / TXT)</h2>
          <label>मराठी इतिहास / भूगोल / राज्यशास्त्र पुस्तक किंवा नोट्स निवडा:</label>
          <input type="file" id="fileInput" accept=".pdf,.txt">
          <button id="uploadBtn" onclick="uploadFile()">📤 Upload & Extract Chapters</button>
          <div id="uploadStatus" class="status-box"></div>
        </div>

        <div class="card" id="generationCard" style="display:none;">
          <h2>⚙️ २. प्रकरण व आज्ञा (Chapter & Instruction)</h2>
          <label>अध्याय / प्रकरण निवडा:</label>
          <select id="chapterSelect"></select>

          <label>वापरकर्त्याची विशेष आज्ञा (किंवा डीफॉल्ट वापरा):</label>
          <textarea id="instructionInput" rows="3" placeholder="उदा. या chapter मधून महत्त्वाचे मुद्दे, तारखा, आणि MPSC साठी points बनव."></textarea>
          
          <div class="quick-chips">
            <span class="chip" onclick="setPrompt('या अध्यायाचे MPSC साठी पूर्ण handwritten notes बनव.')">📝 Full Notes</span>
            <span class="chip" onclick="setPrompt('फक्त MPSC परीक्षेसाठी अति-महत्त्वाचे मुद्दे व ट्रिक्स दे.')">🎯 MPSC Points</span>
            <span class="chip" onclick="setPrompt('या प्रकरणातील सर्व महत्त्वाच्या तारखा व कालक्रम तक्ता तयार कर.')">📅 Dates & Timeline</span>
            <span class="chip" onclick="setPrompt('२ पानांची Quick Revision Sheet तयार कर.')">⚡ Revision Sheet</span>
          </div>

          <button id="generateBtn" onclick="generateNotes()">✨ Generate Handwritten Notes</button>
          <div id="genStatus" class="status-box"></div>
        </div>

        <div class="card" id="downloadCard" style="display:none;">
          <h2>📥 ३. PDF डाउनलोड करा</h2>
          <button onclick="downloadPDF()" style="background:#00E676; color:#000;">📄 Download Ruled Notebook PDF</button>
          <button class="btn-secondary" onclick="generateNotes()">🔄 Regenerate Notes</button>
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
              <div style="font-size: 48px; margin-bottom: 12px;">📝</div>
              <h3>कोणतीही फाईल निवडलेली नाही</h3>
              <p style="font-size: 13px; margin-top: 6px;">डावीकडे PDF किंवा TXT अपलोड करून 'Generate' वर क्लिक करा.<br/>त्यानंतर येथे अस्सल रुल्ड नोटबुक शैलीतील हस्तलिखित नोट्स दिसतील.</p>
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
      status.innerText = 'फाईल वाचत आहे व प्रकरणे शोधत आहे...';
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
        select.innerHTML = '<option value="0">📚 संपूर्ण पुस्तक / फाईल (Full Book)</option>';
        data.chapters.forEach(ch => {
          const opt = document.createElement('option');
          opt.value = ch.id;
          opt.innerText = `${ch.title}`;
          select.appendChild(opt);
        });

        document.getElementById('generationCard').style.display = 'block';
      } catch (err) {
        status.className = 'status-box error';
        status.innerText = `त्रुटी: ${err.message}`;
      } finally {
        btn.disabled = false;
      }
    }

    async function generateNotes() {
      if (!currentDocId) return;

      const chapterId = parseInt(document.getElementById('chapterSelect').value) || 0;
      const instruction = document.getElementById('instructionInput').value;
      const status = document.getElementById('genStatus');
      const btn = document.getElementById('generateBtn');

      status.className = 'status-box loading';
      status.innerText = 'ChatGPT द्वारे हस्तलिखित नोट्स तयार होत आहेत (RAG Grounded)...';
      btn.disabled = true;

      try {
        const resp = await fetch('/prototype/notes/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            doc_id: currentDocId,
            chapter_id: chapterId,
            custom_instruction: instruction
          })
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || 'Generation failed');

        status.className = 'status-box success';
        status.innerText = `Notes यशस्वीपणे तयार झाल्या (${data.page_count} Pages PDF)!`;

        document.getElementById('downloadCard').style.display = 'block';
        document.getElementById('pdfActionBtns').style.display = 'block';
        document.getElementById('openPdfLink').href = data.pdf_url;

        renderNotesPreview(data.structured_note, data.chapter_title);
      } catch (err) {
        status.className = 'status-box error';
        status.innerText = `त्रुटी: ${err.message}`;
      } finally {
        btn.disabled = false;
      }
    }

    function renderNotesPreview(note, chapterTitle) {
      document.getElementById('emptyState').style.display = 'none';
      const render = document.getElementById('notesRender');
      render.style.display = 'block';

      let html = `
        <div class="notebook-header">
          <span>MPSC AI • Handwritten Revision Notes</span>
          <span>पृष्ठ १ / २</span>
        </div>
        <div class="note-h1">✍️ ${note.heading_mr || chapterTitle}</div>
        <div class="note-h2">${note.subheading_mr || 'MPSC विशेष अभ्यास नोट्स'}</div>
      `;

      if (note.short_definition_mr) {
        html += `
          <div class="box box-blue">
            <b>📌 व्याख्या / प्रस्तावना:</b><br/>
            ${note.short_definition_mr}
          </div>
        `;
      }

      if (note.key_points && note.key_points.length > 0) {
        html += `<div style="font-weight:bold; color:#007791; margin: 10px 0 4px 0;">📝 मुख्य मुद्दे:</div><ul class="bullets">`;
        note.key_points.forEach(p => { html += `<li>${p}</li>`; });
        html += `</ul>`;
      }

      if (note.important_dates && note.important_dates.length > 0) {
        html += `
          <div class="box box-amber">
            <b>📅 महत्त्वाच्या तारखा व कालक्रम:</b><br/>
            ${note.important_dates.join('<br/>')}
          </div>
        `;
      }

      if (note.important_personalities && note.important_personalities.length > 0) {
        html += `
          <div class="box box-green">
            <b>👤 महत्त्वाच्या व्यक्ती व कार्य:</b><br/>
            ${note.important_personalities.join('<br/>')}
          </div>
        `;
      }

      if (note.memory_tricks && note.memory_tricks.length > 0) {
        html += `
          <div class="box box-yellow">
            <b>💡 लक्षात ठेवण्याची ट्रिक:</b><br/>
            ${note.memory_tricks.join('<br/>')}
          </div>
        `;
      }

      if (note.table && note.table.headers && note.table.rows) {
        html += `
          <div class="table-container">
            <div style="font-weight:bold; color:#007791; margin-bottom:4px;">📊 ${note.table.title_mr || 'तुलनात्मक तक्ता'}:</div>
            <table>
              <thead><tr>${note.table.headers.map(h => `<th>${h}</th>`).join('')}</tr></thead>
              <tbody>
                ${note.table.rows.map(row => `<tr>${row.map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}
              </tbody>
            </table>
          </div>
        `;
      }

      if (note.exam_points && note.exam_points.length > 0) {
        html += `
          <div class="box box-amber">
            <b>🎯 MPSC परीक्षेसाठी अति-महत्त्वाचे:</b><br/>
            ${note.exam_points.join('<br/>')}
          </div>
        `;
      }

      if (note.quick_revision_box && note.quick_revision_box.length > 0) {
        html += `
          <div class="box box-yellow">
            <b>⚡ Quick Revision (उजळणी):</b><br/>
            ${note.quick_revision_box.join('<br/>')}
          </div>
        `;
      }

      if (note.common_mistakes && note.common_mistakes.length > 0) {
        html += `
          <div class="box box-red">
            <b>⚠️ संभ्रम व सामान्य चुका टाळा:</b><br/>
            ${note.common_mistakes.join('<br/>')}
          </div>
        `;
      }

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
