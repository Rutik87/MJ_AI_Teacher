import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
BOOKS_DIR = DATA_DIR / "books"
EXTRACTED_DIR = DATA_DIR / "extracted_text"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
DB_DIR = DATA_DIR / "database"
AUDIO_DIR = DATA_DIR / "audio_cache"

# Ensure directories exist
for folder in [DATA_DIR, BOOKS_DIR, EXTRACTED_DIR, EMBEDDINGS_DIR, DB_DIR, AUDIO_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "MPSC AI Study Assistant"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SUPABASE_CA_CERT_PATH: str = "/app/certs/supabase-ca.crt"
    
    # Storage Paths
    DATA_PATH: str = str(DATA_DIR)
    BOOKS_PATH: str = str(BOOKS_DIR)
    EXTRACTED_PATH: str = str(EXTRACTED_DIR)
    EMBEDDINGS_PATH: str = str(EMBEDDINGS_DIR)
    DATABASE_PATH: str = str(DB_DIR / "mpsc_study.db")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DB_DIR / 'mpsc_study.db'}")
    SYNC_DATABASE_URL: str = os.getenv("SYNC_DATABASE_URL", f"sqlite:///{DB_DIR / 'mpsc_study.db'}")
    AUDIO_CACHE_PATH: str = str(AUDIO_DIR)
    
    # AI & RAG Configuration
    AI_PROVIDER: str = "openrouter"  # openrouter, gemini, local, auto
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openrouter/free"
    GEMINI_API_KEY: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = "openrouter/free"
    AI_TEMPERATURE: float = 0.2
    
    # Embeddings
    EMBEDDING_PROVIDER: str = "auto"  # auto, marathi_sentence, gemini, openai, local_tfidf
    EMBEDDING_MODEL: str = "paraphrase-multilingual-MiniLM-L12-v2"
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100
    TOP_K_RESULTS: int = 5
    
    # Speech & Voice
    STT_PROVIDER: str = "modular_marathi"
    TTS_PROVIDER: str = "gtts"  # gtts, edge_tts, custom
    TTS_DEFAULT_LANG: str = "mr"  # Marathi
    
    # Security
    MAX_UPLOAD_SIZE_MB: int = 150
    ALLOWED_EXTENSIONS: list[str] = [".pdf"]

    model_config = {"env_file": ".env", "extra": "allow"}

settings = Settings()
