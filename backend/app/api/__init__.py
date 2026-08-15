from app.api.books import router as books_router
from app.api.chat import router as chat_router
from app.api.teacher import router as teacher_router
from app.api.tests import router as tests_router
from app.api.revision import router as revision_router
from app.api.progress import router as progress_router
from app.api.voice import router as voice_router
from app.api.settings import router as settings_router
from app.api.endpoints.current_affairs import router as current_affairs_router
from app.api.endpoints.mj_voice import router as mj_router
from app.api.endpoints.sync import router as sync_router
from app.api.endpoints.notes import router as notes_router
from app.api.endpoints.gemini_live_ws import router as gemini_live_ws_router
from app.api.endpoints.rag import router as rag_router

__all__ = [
    "books_router",
    "chat_router",
    "teacher_router",
    "tests_router",
    "revision_router",
    "progress_router",
    "voice_router",
    "settings_router",
    "current_affairs_router",
    "mj_router",
    "sync_router",
    "notes_router",
    "gemini_live_ws_router",
    "rag_router"
]
