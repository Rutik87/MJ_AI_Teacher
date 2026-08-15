import os
import re
import ssl
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, text
from app.config import settings
from app.utils.logger import logger

def _get_strict_production_ssl_context() -> tuple[any, str]:
    """
    Creates a strict, production-grade SSLContext for PostgreSQL / Supabase Connection Pooler.
    Requires the official Supabase Root CA certificate (downloaded from Supabase Dashboard).
    Enforces ssl.CERT_REQUIRED and check_hostname = True.
    """
    ca_path = getattr(settings, "SUPABASE_CA_CERT_PATH", "/app/certs/supabase-ca.crt")
    
    # Local development fallback path
    if not os.path.exists(ca_path):
        local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "certs", "supabase-ca.crt"))
        if os.path.exists(local_path):
            ca_path = local_path

    if os.path.exists(ca_path):
        try:
            ctx = ssl.create_default_context(cafile=ca_path)
            ctx.verify_mode = ssl.CERT_REQUIRED
            # Match pooler wildcard certificate (*.pooler.supabase.com)
            ctx.check_hostname = True
            logger.info(f"Loaded official Supabase CA certificate from [{ca_path}] with strict verify_mode=CERT_REQUIRED and check_hostname=True.")
            return ctx, f"Official Supabase CA ({os.path.basename(ca_path)}) - verify_mode=CERT_REQUIRED, check_hostname=True"
        except Exception as e:
            logger.error(f"Failed to load CA certificate from [{ca_path}]: {e}")
            raise RuntimeError(f"SSL CA certificate loading failed for [{ca_path}]: {e}") from e

    # If CA cert is missing in production, string 'require' enables TLS (libpq sslmode=require equivalent)
    logger.warning(f"CA certificate file not found at [{ca_path}]. Falling back to ssl='require'.")
    return "require", "ssl='require'"

def _normalize_async_pg_url(raw_url: str) -> tuple[str, dict]:
    """
    Normalizes PostgreSQL URL for asyncpg engine and applies ONE unified SSL configuration.
    Enforces statement_cache_size=0 for Supabase / PgBouncer / Supavisor pooler compatibility.
    Strips all conflicting SSL query parameters from the URL string.
    """
    url = raw_url.strip()
    connect_args = {}

    if url.startswith("sqlite"):
        return url, connect_args

    # Handle postgres / postgresql prefixes for asyncpg
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Supabase Connection Pooler (PgBouncer/Supavisor) REQUIRES statement_cache_size=0 for asyncpg
    connect_args["statement_cache_size"] = 0
    
    ssl_setting, ssl_desc = _get_strict_production_ssl_context()
    connect_args["ssl"] = ssl_setting
    logger.info(f"Applied SSL Configuration: {ssl_desc}")

    # Clean conflicting query params from URI string to avoid parameter duplication/conflict
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        query_params.pop("sslmode", None)
        query_params.pop("ssl", None)
        query_params.pop("statement_cache_size", None)
        
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

    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        query_params.pop("sslmode", None)
        query_params.pop("ssl", None)
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

    return url

# Normalize URLs - Guarantee sync engine uses PostgreSQL when DATABASE_URL is PostgreSQL
raw_sync_url = getattr(settings, "SYNC_DATABASE_URL", "")
if (not raw_sync_url or raw_sync_url.startswith("sqlite")) and not settings.DATABASE_URL.startswith("sqlite"):
    raw_sync_url = settings.DATABASE_URL

async_db_url, async_connect_args = _normalize_async_pg_url(settings.DATABASE_URL)
sync_db_url = _normalize_sync_pg_url(raw_sync_url)

# Async engine for FastAPI endpoints and vector persistence
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

# Sync engine for background workers
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
    try:
        # Import schema models to register with Base.metadata before create_all
        import app.models.schema
        from app.migrations import run_schema_migrations
        
        async with async_engine.begin() as conn:
            # 1. Create any missing tables
            await conn.run_sync(Base.metadata.create_all)
            # 2. Run idempotent column migrations for existing tables
            await run_schema_migrations(conn)
            
        logger.info("Database connection established, migrations applied, and all schemas initialized successfully.")
    except Exception as e:
        logger.error(f"CRITICAL: Database initialization failed: {e}")
        if settings.ENVIRONMENT.lower() == "production":
            raise RuntimeError(f"Production database initialization failed: {e}") from e

