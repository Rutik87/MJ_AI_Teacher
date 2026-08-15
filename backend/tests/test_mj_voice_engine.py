import pytest
from app.services.tts.voice_engine import mj_voice_engine, EMOTION_PRESETS
from app.services.tts.tts_service import tts_service

@pytest.mark.asyncio
async def test_voice_profile_metadata():
    profile = mj_voice_engine.get_voice_profile()
    assert profile["voice_profile_id"] == "mj_primary"
    assert profile["name"] == "MJ"
    assert profile["gender"] == "female"
    assert profile["is_authorized"] is True
    assert "neutral" in profile["emotions_supported"]
    assert "encouraging" in profile["emotions_supported"]
    assert "friendly" in profile["emotions_supported"]
    assert "explaining" in profile["emotions_supported"]

@pytest.mark.asyncio
async def test_emotion_presets():
    for emotion_name in ["neutral", "friendly", "happy", "encouraging", "concerned", "excited", "calm", "empathetic", "explaining", "celebrating"]:
        assert emotion_name in EMOTION_PRESETS
        preset = EMOTION_PRESETS[emotion_name]
        assert "speed_multiplier" in preset
        assert "pitch" in preset
        assert "intensity" in preset

@pytest.mark.asyncio
async def test_voice_synthesis_and_caching():
    text = "नमस्कार! मी MJ, तुझी AI सोबती."
    
    # 1. Synthesize audio with encouraging emotion
    audio_url_1, duration_1 = await mj_voice_engine.synthesize_speech(
        text=text,
        emotion="encouraging",
        speed=1.0
    )
    assert audio_url_1 is not None
    assert audio_url_1.startswith("/api/voice/audio/")
    assert duration_1 > 0

    # 2. Second call should hit the cache immediately
    audio_url_2, duration_2 = await mj_voice_engine.synthesize_speech(
        text=text,
        emotion="encouraging",
        speed=1.0
    )
    assert audio_url_2 == audio_url_1

@pytest.mark.asyncio
async def test_tts_service_integration():
    url, duration, normalized = await tts_service.synthesize_with_metadata(
        text="1857 चा revolt simple Marathi madhye samjhav.",
        emotion="explaining"
    )
    assert url is not None
    assert "अठराशे सत्तावन्न" in normalized
    assert "रिव्होल्ट" in normalized
    assert "सिंपल" in normalized
