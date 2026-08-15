"""
Unified Central VoiceService for the entire MPSC AI Application.
Provides ONE single permanent authorized voice (MJ) across all features:
- AI Teacher
- PDF/TXT RAG
- MPSC Explanations
- PYQ Explanations
- Current Affairs
- Test Explanations
- Revision
- Casual & Emotional Conversation
- MJ Voice Assistant

Strict Guardrails:
1. No default system voice.
2. No random TTS voice.
3. No different voices for different features.
4. If voice generation fails, returns text only without silently switching to a different voice.
5. Server-side caching for repeated phrases.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from app.config import settings
from app.services.speech.marathi_normalizer import MarathiPronunciationNormalizer
from app.services.tts.voice_engine import mj_voice_engine, EMOTION_PRESETS
from app.utils.logger import logger

class VoiceService:
    """
    ONE permanent VoiceService for the entire application.
    Enforces speaker identity, Marathi phonetic normalization, emotion modulation,
    and persistent audio caching.
    """

    def __init__(self):
        self.engine = mj_voice_engine
        self.profile_id = "mj_primary"
        self.speaker_name = "MJ"
        self.cache_dir = Path(settings.AUDIO_CACHE_PATH)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def generate_voice(
        self,
        text: str,
        emotion: str = "friendly",
        speed: float = 1.0,
        intensity: float = 0.6
    ) -> Dict[str, Any]:
        """
        Generates audio using the ONE single authorized MJ voice.

        Parameters:
        - text: Marathi / mixed text input.
        - emotion: 'friendly', 'happy', 'encouraging', 'calm', 'empathetic', 'excited', 'explaining'.
        - speed: Playback speed multiplier (default: 1.0).
        - intensity: Emotional prosody depth (0.0 to 1.0).

        Returns:
        {
            "audio_url": str (relative path to MP3 audio) or None if synthesis failed,
            "duration_seconds": float,
            "normalized_text": str,
            "voice_profile_id": "mj_primary",
            "speaker": "MJ",
            "emotion": str,
            "speed": float,
            "success": bool
        }
        """
        if not text or not text.strip():
            return {
                "audio_url": None,
                "duration_seconds": 0.0,
                "normalized_text": "",
                "voice_profile_id": self.profile_id,
                "speaker": self.speaker_name,
                "emotion": emotion,
                "speed": speed,
                "success": False
            }

        # 1. Marathi Phonetic Normalization (1857 -> अठराशे सत्तावन्न, MPSC -> एमपीएससी)
        normalized_text = MarathiPronunciationNormalizer.normalize_text(text)

        # 2. Synthesize using the single authorized MJ voice engine
        try:
            audio_url, duration = await self.engine.synthesize_speech(
                text=normalized_text,
                emotion=emotion,
                speed=speed,
                lang="mr"
            )

            if audio_url:
                return {
                    "audio_url": audio_url,
                    "duration_seconds": round(duration, 2),
                    "normalized_text": normalized_text,
                    "voice_profile_id": self.profile_id,
                    "speaker": self.speaker_name,
                    "emotion": emotion,
                    "speed": speed,
                    "success": True
                }
            else:
                logger.warning(f"Voice generation returned no audio URL for text: '{text[:30]}...'")
                return {
                    "audio_url": None,
                    "duration_seconds": 0.0,
                    "normalized_text": normalized_text,
                    "voice_profile_id": self.profile_id,
                    "speaker": self.speaker_name,
                    "emotion": emotion,
                    "speed": speed,
                    "success": False
                }
        except Exception as e:
            logger.error(f"Voice generation error in VoiceService: {e}")
            # Strict Rule: Return text only, NEVER switch to a random or different voice
            return {
                "audio_url": None,
                "duration_seconds": 0.0,
                "normalized_text": normalized_text,
                "voice_profile_id": self.profile_id,
                "speaker": self.speaker_name,
                "emotion": emotion,
                "speed": speed,
                "success": False,
                "error": str(e)
            }

    def get_voice_profile(self) -> Dict[str, Any]:
        """Returns the single permanent voice profile metadata."""
        return {
            "voice_profile_id": self.profile_id,
            "name": self.speaker_name,
            "language": "mr-IN",
            "gender": "female",
            "is_authorized": True,
            "identity_statement": "हा माझ्या AI चा एकच कायमचा आवाज आहे.",
            "emotions_supported": [
                "friendly",
                "happy",
                "encouraging",
                "calm",
                "empathetic",
                "excited",
                "explaining",
                "neutral"
            ]
        }


# Singleton instance
voice_service = VoiceService()
