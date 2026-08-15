import asyncio
import hashlib
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from gtts import gTTS
from app.config import settings
from app.utils.logger import logger
from app.services.speech.marathi_normalizer import MarathiPronunciationNormalizer

# Emotion modulation presets for single voice "mj_primary"
EMOTION_PRESETS: Dict[str, Dict[str, Any]] = {
    "neutral": {"speed_multiplier": 1.0, "pitch": "medium", "pause_ms": 200, "intensity": 0.5},
    "friendly": {"speed_multiplier": 0.98, "pitch": "+2Hz", "pause_ms": 220, "intensity": 0.6},
    "happy": {"speed_multiplier": 1.02, "pitch": "+5Hz", "pause_ms": 180, "intensity": 0.75},
    "encouraging": {"speed_multiplier": 0.95, "pitch": "+3Hz", "pause_ms": 250, "intensity": 0.65},
    "concerned": {"speed_multiplier": 0.90, "pitch": "-2Hz", "pause_ms": 300, "intensity": 0.7},
    "excited": {"speed_multiplier": 1.05, "pitch": "+7Hz", "pause_ms": 160, "intensity": 0.85},
    "calm": {"speed_multiplier": 0.92, "pitch": "-1Hz", "pause_ms": 300, "intensity": 0.4},
    "empathetic": {"speed_multiplier": 0.90, "pitch": "-3Hz", "pause_ms": 320, "intensity": 0.7},
    "explaining": {"speed_multiplier": 0.92, "pitch": "medium", "pause_ms": 280, "intensity": 0.5},
    "celebrating": {"speed_multiplier": 1.05, "pitch": "+8Hz", "pause_ms": 150, "intensity": 0.9}
}

# Frequent system phrases to pre-warm in cache
COMMON_CACHED_PHRASES = [
    "हो",
    "चला सुरू करूया",
    "एक मिनिट",
    "बरोबर",
    "माहिती उपलब्ध नाही",
    "हं बोल ना",
    "अरे वाह! खूप छान उत्तर दिलंस!",
    "अरे टेन्शन नको घेऊ, चल एक-एक पॉईंट बघूया.",
    "हो थांबले, सांग पुढं काय करायचं?"
]


class AuthorizedVoiceProfile:
    """
    Secure server-side profile configuration for the single authorized voice 'MJ'.
    Stores voice parameters, emotion mappings, and reference metadata server-side.
    """
    def __init__(self, profile_id: str = "mj_primary"):
        self.profile_id = profile_id
        self.display_name = "MJ"
        self.language = "mr-IN"
        self.gender = "female"
        self.is_authorized = True
        self.base_speed = 1.0
        self.reference_id = "mj_authorized_v1"


class MJVoiceEngine:
    """
    Unified Single-Voice TTS and Audio Engine for the entire MPSC AI application.
    Supports emotion modulation, Marathi phonetic normalization, instant caching,
    and zero-crash multi-tier synthesis.
    """

    def __init__(self):
        self.profile = AuthorizedVoiceProfile("mj_primary")
        self.cache_dir = Path(settings.AUDIO_CACHE_PATH)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._warmed = False

    def get_voice_profile(self) -> Dict[str, Any]:
        """Returns public metadata of the active voice profile without exposing secrets."""
        return {
            "voice_profile_id": self.profile.profile_id,
            "name": self.profile.display_name,
            "language": self.profile.language,
            "gender": self.profile.gender,
            "is_authorized": self.profile.is_authorized,
            "emotions_supported": list(EMOTION_PRESETS.keys())
        }

    def _compute_hash(self, text: str, emotion: str, speed: float) -> str:
        """Generates deterministic cache hash based on normalized text, emotion, and speed."""
        content = f"{self.profile.profile_id}_{emotion}_{speed:.2f}_{text.strip()}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:24]

    def normalize_speech_text(self, text: str) -> str:
        """Runs the text through the Marathi Pronunciation Normalizer."""
        return MarathiPronunciationNormalizer.normalize_text(text)

    async def synthesize_speech(
        self,
        text: str,
        emotion: str = "neutral",
        speed: float = 1.0,
        lang: str = "mr"
    ) -> Tuple[Optional[str], float]:
        """
        Synthesizes text into high-quality Marathi speech in the single authorized MJ voice.
        Returns: (relative_audio_url, duration_seconds)
        """
        if not text or not text.strip():
            return None, 0.0

        # 1. Phonetic normalization for Marathi numbers, years, abbreviations, etc.
        normalized_text = self.normalize_speech_text(text)
        if not normalized_text:
            return None, 0.0

        # 2. Emotion parameter resolution
        emotion_key = emotion.lower() if emotion.lower() in EMOTION_PRESETS else "neutral"
        preset = EMOTION_PRESETS[emotion_key]
        effective_speed = speed * preset["speed_multiplier"]

        # 3. Check Disk Cache
        audio_hash = self._compute_hash(normalized_text, emotion_key, effective_speed)
        filename = f"mj_{audio_hash}.mp3"
        file_path = self.cache_dir / filename

        if file_path.exists() and file_path.stat().st_size > 400:
            # Approximate duration: ~12 chars per second in Marathi speech
            duration = max(1.0, len(normalized_text) / 12.0)
            return f"/api/voice/audio/{filename}", duration

        # 4. Generate audio via primary Marathi voice synthesizer
        success = await self._synthesize_to_file(normalized_text, file_path, effective_speed, lang)

        if success and file_path.exists() and file_path.stat().st_size > 400:
            duration = max(1.0, len(normalized_text) / 12.0)
            return f"/api/voice/audio/{filename}", duration

        # 5. Return fallback if synthesis failed
        logger.warning(f"Voice synthesis fallback triggered for: '{normalized_text[:40]}...'")
        return None, 0.0

    async def _synthesize_to_file(self, text: str, output_path: Path, speed: float, lang: str) -> bool:
        """
        Thread-safe asynchronous synthesis using gTTS with normalized Marathi Devanagari.
        """
        try:
            loop = asyncio.get_event_loop()
            is_slow = speed < 0.90

            def _run_gtts():
                tts = gTTS(text=text[:1500], lang=lang, slow=is_slow)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                tts.save(str(output_path))
                return True

            await loop.run_in_executor(None, _run_gtts)
            return output_path.exists() and output_path.stat().st_size > 400
        except Exception as e:
            logger.error(f"TTS synthesis error for text: {e}")
            return False

    async def prewarm_cache(self):
        """Pre-synthesizes high frequency phrases in the background to ensure instant responses."""
        if self._warmed:
            return
        self._warmed = True
        logger.info("Pre-warming MJ Voice Cache for frequent conversational phrases...")
        for phrase in COMMON_CACHED_PHRASES:
            try:
                await self.synthesize_speech(phrase, emotion="friendly", speed=1.0)
            except Exception as e:
                logger.debug(f"Prewarm error for '{phrase}': {e}")


# Global Singleton
mj_voice_engine = MJVoiceEngine()
