from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from app.config import settings
from app.services.tts.voice_engine import mj_voice_engine
from app.utils.logger import logger

class TTSService:
    """
    Unified TTS and Voice Management Service.
    Wraps mj_voice_engine for consistent single-voice synthesis across the entire app.
    """

    def __init__(self):
        self.engine = mj_voice_engine
        self.cache_dir = Path(settings.AUDIO_CACHE_PATH)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_voice_profile(self) -> Dict[str, Any]:
        return self.engine.get_voice_profile()

    async def generate_speech_file(
        self,
        text: str,
        lang: str = "mr",
        speed: float = 1.0,
        emotion: str = "neutral"
    ) -> Optional[str]:
        """
        Synthesizes text into speech using the single authorized MJ voice.
        Returns relative URL path to the generated MP3 audio file.
        """
        audio_url, _ = await self.engine.synthesize_speech(
            text=text,
            emotion=emotion,
            speed=speed,
            lang=lang
        )
        return audio_url

    async def synthesize_with_metadata(
        self,
        text: str,
        lang: str = "mr",
        speed: float = 1.0,
        emotion: str = "neutral"
    ) -> Tuple[Optional[str], float, str]:
        """
        Returns (audio_url, duration_seconds, normalized_speech_text).
        """
        normalized = self.engine.normalize_speech_text(text)
        audio_url, duration = await self.engine.synthesize_speech(
            text=text,
            emotion=emotion,
            speed=speed,
            lang=lang
        )
        return audio_url, duration, normalized


tts_service = TTSService()
