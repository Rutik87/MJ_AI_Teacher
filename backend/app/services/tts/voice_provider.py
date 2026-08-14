from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path
from gtts import gTTS
from app.utils.logger import logger

class BaseVoiceProvider(ABC):
    """
    Abstract base class for all TTS and voice generation providers.
    """
    @abstractmethod
    async def synthesize(self, text: str, output_path: Path, lang: str = "mr", speed: float = 1.0) -> bool:
        pass

class StandardMarathiVoiceProvider(BaseVoiceProvider):
    """
    Standard Marathi Text-to-Speech using gTTS.
    """
    async def synthesize(self, text: str, output_path: Path, lang: str = "mr", speed: float = 1.0) -> bool:
        try:
            # Clean text for TTS (remove markdown asterisks and URLs)
            import re
            clean_text = re.sub(r'[*#_`\[\]]', '', text)
            clean_text = re.sub(r'http\S+', '', clean_text)
            
            # gTTS supports slow=True for < 1.0 speed
            is_slow = speed < 0.9
            tts = gTTS(text=clean_text[:1000], lang=lang, slow=is_slow)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            tts.save(str(output_path))
            return True
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return False

class FutureVoiceProvider(BaseVoiceProvider):
    """
    Placeholder architecture for future custom/consented voice modules.
    Explicitly requires user consent and voice provider credentials before activation.
    (Voice cloning is NOT implemented in this version).
    """
    def __init__(self, requires_consent: bool = True):
        self.requires_consent = requires_consent
        self.is_active = False

    async def synthesize(self, text: str, output_path: Path, lang: str = "mr", speed: float = 1.0) -> bool:
        logger.info("FutureVoiceProvider invoked. Fallback to standard Marathi TTS.")
        standard_provider = StandardMarathiVoiceProvider()
        return await standard_provider.synthesize(text, output_path, lang, speed)
