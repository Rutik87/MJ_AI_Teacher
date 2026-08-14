# MPSC AI — "तुमचा वैयक्तिक MPSC शिक्षक"
> **A Production-Grade Futuristic AI Study Assistant for MPSC Aspirants**

---

## 🌟 Overview

**MPSC AI** is a dark, futuristic AI study companion designed specifically for Maharashtra Public Service Commission (MPSC) exams. It allows students to store all their reference books (PDFs) in one place and provides a Marathi-speaking AI teacher that answers questions, generates custom practice tests, analyzes PYQs (Previous Year Questions), and tracks study progress—with zero required paid subscriptions.

---

## 🎨 15-Screen Design Architecture (Master Reference Board)

1. **Splash Screen**: Glowing Neon Neural Brain Hologram + `MPSC AI` + `तुमचा वैयक्तिक MPSC शिक्षक` + Gradient loading progress capsule.
2. **Home Dashboard**: `शुभ प्रभात, Rutik!` + `तुमची तयारी 68%` ring gauge + `पुढे सुरू ठेवा` card + 6 Quick Action tiles (माझी पुस्तके, AI शिक्षक, चाचणी, Revision, PYQ, Progress).
3. **AI Teacher (Chat)**: Dual-tone Marathi chat bubbles, Sources card with exact page citations (`महाराष्ट्राचा इतिहास - पृ. 124`), audio speaker play button, voice mic, and send button.
4. **My Books (माझी पुस्तके)**: Search bar, subject filters, colored book cards with progress bars (`भारतीय राज्यघटना 72%`, `महाराष्ट्राचा इतिहास 100%`), and floating `+ PDF जोडा` button.
5. **PDF Reader**: Clean AMOLED reader mode (`124 / 512`), Marathi constitutional text, and bottom toolbar (सूची, शोध, Bookmarks, AI ला विचारा).
6. **Subjects (विषय)**: 14 High-tech neon tiles (इतिहास, भूगोल, राज्यशास्त्र, अर्थशास्त्र, महाराष्ट्र विशेष, सामान्य विज्ञान, पर्यावरण, चालू घडामोडी, गणित, बुद्धिमत्ता, PYQ संच, Notes, इतर).
7. **AI Test Setup**: Custom test generator with subject, topic, question count (`20`), difficulty, and `चाचणी सुरू करा`.
8. **MCQ Screen**: Interactive examination interface with `⏱️ 14:32` timer, `7 / 20` progress, green neon selected glow, and previous/skip/next controls.
9. **Result Screen**: Large circular score gauge (`16 / 20` • `80%`), performance breakdown (योग्य: 16, चूक: 4), and weak topics analysis.
10. **PYQ Screen**: Past exam papers list (2023, 2022, 2021, 2020 पूर्व परीक्षा) with `+ AI विश्लेषण`.
11. **Revision Hub**: Spaced repetition dashboard with `आजचे Revision` (12 विषय बाकी), Weak Topics (8), Bookmarks (24), and Due Revision (5).
12. **Progress Analytics**: Weekly study time (`12h 45m`) with interactive neon sparkline chart and subject-wise completion bars.
13. **Profile Screen**: `(R) Rutik - MPSC Aspirant`, Streak (12), Total Tests (24), Daily Study Goal (73%), and Target (`MPSC राज्यसेवा 2025`).
14. **Settings**: Marathi language, detailed AI style, TTS voice switch, 1.0x speed, Dark Mode, Storage (12.4 GB), and Local AI options.
15. **Side Drawer**: Neon Brain header with instant navigation to all 15 screens.

---

## 🛠️ Technology Stack

- **Frontend**: Flutter 3.x, Dart, Google Fonts (Poppins, Noto Sans Devanagari), Provider, FL Chart, synthesized WebAudio sound engine.
- **Backend**: Python 3.10+, FastAPI, Uvicorn, SQLite, PyPDF2, PDFPlumber, ChromaDB local vector store.
- **AI & RAG**: Provider abstraction supporting local models (Ollama, local HuggingFace embeddings) and cloud APIs (Gemini/Groq) without forced paid subscriptions.
- **Audio & Haptics**: In-memory debounced PCM WAV click/bubble pop synthesized audio triggers.

---

## 🚀 Running Locally

### 1. Backend (FastAPI)
```bash
python run_backend.py
```
*Runs on `http://0.0.0.0:8000`*

### 2. Frontend (Flutter Web / Mobile Server)
```bash
cd frontend
flutter run -d web-server --web-hostname 0.0.0.0 --web-port 3000
```
*Live on `http://localhost:3000` or on your mobile Wi-Fi at `http://192.168.0.119:3000`*

### 3. Running Unit & Widget Tests
```bash
cd frontend
flutter test
```

---

## 📱 Building Android APK

```bash
cd frontend
flutter build apk --release
```
The output APK will be generated at `frontend/build/app/outputs/flutter-apk/app-release.apk`.
