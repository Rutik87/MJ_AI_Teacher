import hashlib
from pathlib import Path
from typing import Optional
from app.config import settings
from app.services.tts.voice_provider import StandardMarathiVoiceProvider, FutureVoiceProvider
from app.utils.logger import logger

class TTSService:
    """
    Manages TTS generation, caching, and audio file serving.
    """

    def __init__(self):
        self.provider = StandardMarathiVoiceProvider()
        self.cache_dir = Path(settings.AUDIO_CACHE_PATH)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def set_provider(self, provider_name: str):
        if provider_name == "future_voice":
            self.provider = FutureVoiceProvider()
        else:
            self.provider = StandardMarathiVoiceProvider()

    async def generate_speech_file(self, text: str, lang: str = "mr", speed: float = 1.0) -> Optional[str]:
        """
        Synthesizes Marathi text to an MP3 file and returns relative API URL path.
        """
        if not text.strip():
            return None

        # Create unique hash for text + speed + lang
        content_hash = hashlib.md5(f"{text[:500]}_{speed}_{lang}".encode("utf-8")).hexdigest()
        filename = f"audio_{content_hash}.mp3"
        file_path = self.cache_dir / filename

        # Return cached audio if already generated
        if file_path.exists() and file_path.stat().st_size > 500:
            return f"/api/voice/audio/{filename}"

        success = await self.provider.synthesize(
            text=text,
            output_path=file_path,
            lang=lang,
            speed=speed
        )

        if success and file_path.exists():
            return f"/api/voice/audio/{filename}"

        return None

tts_service = TTSService()
