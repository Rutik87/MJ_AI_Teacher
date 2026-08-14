import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from app.config import settings
from app.utils.logger import logger

def _normalize_async_pg_url(raw_url: str) -> tuple[str, dict]:
    """
    Normalizes PostgreSQL URL for asyncpg engine and extracts SSL connect args.
    Cleans leading/trailing whitespace, newlines, and strips unsupported query parameters.
    """
    url = raw_url.strip()
    connect_args = {}

    if url.startswith("sqlite"):
        return url, connect_args

    # Handle postgres / postgresql prefixes
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Clean SSL query params for asyncpg compatibility
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # asyncpg handles SSL via connect_args or ssl parameter
        if "sslmode" in query_params:
            ssl_mode = query_params.pop("sslmode")[0]
            if ssl_mode in ["require", "verify-ca", "verify-full"]:
                connect_args["ssl"] = True
        
        new_query = urlencode(query_params, doseq=True)
        url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
    except Exception:
        pass

    return url, connect_args

def _normalize_sync_pg_url(raw_url: str) -> str:
    url = raw_url.strip()
    if url.startswith("sqlite"):
        return url

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

# Normalize URLs
async_db_url, async_connect_args = _normalize_async_pg_url(settings.DATABASE_URL)
sync_db_url = _normalize_sync_pg_url(settings.SYNC_DATABASE_URL)

# Async engine for FastAPI endpoints
async_engine = create_async_engine(
    async_db_url,
    connect_args=async_connect_args,
    echo=False,
    future=True,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Sync engine for background workers and sync queries
sync_engine = create_engine(
    sync_db_url,
    echo=False,
    future=True,
    pool_pre_ping=True
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

def get_sync_db():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()

def _mask_url_for_logs(url: str) -> str:
    try:
        parsed = urlparse(url)
        if parsed.password:
            masked_netloc = parsed.netloc.replace(f":{parsed.password}@", ":***@")
            return urlunparse((parsed.scheme, masked_netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
    except Exception:
        pass
    return "database_connection"

async def init_db():
    logger.info(f"Connecting to database [{_mask_url_for_logs(async_db_url)}]...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database connection established and schema initialized successfully.")
