from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.schema import User, VoiceSettings
from app.schemas.pydantic_models import SettingsDTO
from app.config import settings

router = APIRouter(tags=["Settings"])

@router.get("/settings", response_model=SettingsDTO)
async def get_settings(user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """
    Returns app and AI configuration parameters.
    """
    u_res = await db.execute(select(User).where(User.id == user_id))
    user = u_res.scalar_one_or_none()
    
    v_res = await db.execute(select(VoiceSettings).where(VoiceSettings.user_id == user_id))
    voice = v_res.scalar_one_or_none()

    return SettingsDTO(
        preferred_language=user.preferred_language if user else "mr",
        tts_enabled=voice.tts_enabled if voice else True,
        voice_speed=voice.voice_speed if voice else 1.0,
        theme_mode="dark",
        ai_provider=settings.AI_PROVIDER,
        ai_model=settings.AI_MODEL,
        ai_api_key_configured=bool(settings.AI_API_KEY)
    )

@router.post("/settings", response_model=SettingsDTO)
async def update_settings(data: SettingsDTO, user_id: int = 1, db: AsyncSession = Depends(get_db)):
    """
    Updates user settings.
    """
    u_res = await db.execute(select(User).where(User.id == user_id))
    user = u_res.scalar_one_or_none()
    if user:
        user.preferred_language = data.preferred_language

    v_res = await db.execute(select(VoiceSettings).where(VoiceSettings.user_id == user_id))
    voice = v_res.scalar_one_or_none()
    if not voice:
        voice = VoiceSettings(
            user_id=user_id,
            tts_enabled=data.tts_enabled,
            voice_speed=data.voice_speed
        )
        db.add(voice)
    else:
        voice.tts_enabled = data.tts_enabled
        voice.voice_speed = data.voice_speed

    await db.commit()

    return SettingsDTO(
        preferred_language=data.preferred_language,
        tts_enabled=data.tts_enabled,
        voice_speed=data.voice_speed,
        theme_mode=data.theme_mode,
        ai_provider=data.ai_provider,
        ai_model=data.ai_model,
        ai_api_key_configured=bool(settings.AI_API_KEY)
    )
