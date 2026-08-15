import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from app.schemas.pydantic_models import TTSRequest, TTSResponse, STTResponse, MJVoiceProfileResponse
from app.services.speech.stt_service import stt_service
from app.services.voice_service import voice_service
from app.config import settings
from app.utils.logger import logger

router = APIRouter(tags=["Voice & Audio"])

@router.get("/voice/profile", response_model=MJVoiceProfileResponse)
async def get_voice_profile():
    """
    Returns active authorized voice profile metadata.
    """
    return voice_service.get_voice_profile()

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
    Generates Marathi speech audio from text using the single authorized MJ voice.
    """
    res = await voice_service.generate_voice(
        text=request.text,
        emotion=request.emotion or "neutral",
        speed=request.speed
    )

    if not res.get("audio_url"):
        raise HTTPException(status_code=500, detail="ऑडिओ तयार करता आला नाही.")

    return TTSResponse(
        audio_url=res["audio_url"],
        duration_seconds=res["duration_seconds"],
        emotion=request.emotion or "neutral",
        voice_profile_id=res["voice_profile_id"],
        speech_text=res["normalized_text"]
    )

@router.get("/voice/audio/{filename}")
async def serve_audio_file(filename: str):
    """
    Serves the generated MP3 file for in-app playback with audio streaming support.
    """
    # Sanitize filename
    safe_name = Path(filename).name
    file_path = Path(settings.AUDIO_CACHE_PATH) / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="ऑडिओ फाईल सापडली नाही.")

    return FileResponse(
        path=str(file_path),
        media_type="audio/mpeg",
        filename=safe_name,
        headers={"Accept-Ranges": "bytes"}
    )
