from app.api.books import router as books_router
from app.api.chat import router as chat_router
from app.api.settings import router as settings_router
from app.api.endpoints.rag import router as rag_router

__all__ = [
    "books_router",
    "chat_router",
    "settings_router",
    "rag_router"
]
