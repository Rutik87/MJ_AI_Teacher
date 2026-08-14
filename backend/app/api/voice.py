import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from app.schemas.pydantic_models import TTSRequest, TTSResponse, STTResponse
from app.services.speech.stt_service import stt_service
from app.services.tts.tts_service import tts_service
from app.config import settings
from app.utils.logger import logger

router = APIRouter(tags=["Voice & Audio"])

@router.post("/voice/transcribe", response_model=STTResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("mr-IN")
):
    """
    Receives voice audio input and returns transcribed Marathi text.
    """
    contents = await file.read()
    resp = await stt_service.transcribe_audio(contents, filename=file.filename or "audio.wav")
    return resp

@router.post("/voice/speak", response_model=TTSResponse)
async def generate_speech(request: TTSRequest):
    """
    Generates Marathi speech audio from text with adjustable speed.
    """
    audio_rel_url = await tts_service.generate_speech_file(
        text=request.text,
        lang=request.lang or "mr",
        speed=request.speed
    )

    if not audio_rel_url:
        raise HTTPException(status_code=500, detail="ऑडिओ तयार करता आला नाही.")

    return TTSResponse(
        audio_url=audio_rel_url,
        duration_seconds=len(request.text) / 10.0
    )

@router.get("/voice/audio/{filename}")
async def serve_audio_file(filename: str):
    """
    Serves the generated MP3 file for in-app playback.
    """
    file_path = Path(settings.AUDIO_CACHE_PATH) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="ऑडिओ फाईल सापडली नाही.")

    return FileResponse(
        path=str(file_path),
        media_type="audio/mpeg",
        filename=filename
    )
