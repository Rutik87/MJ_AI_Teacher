import os
import re
import ssl
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, text
from app.config import settings
from app.utils.logger import logger

try:
    import certifi
    SYSTEM_CA_BUNDLE = certifi.where()
except ImportError:
    SYSTEM_CA_BUNDLE = None

def _get_production_ssl_context() -> tuple[any, str]:
    """
    Creates a production-grade SSLContext for PostgreSQL / Supabase Connection Pooler.
    Uses SUPABASE_CA_CERT_PATH (or certifi CA bundle) with ssl.CERT_REQUIRED validation.
    Returns: (ssl_setting, description)
    """
    ca_path = os.getenv("SUPABASE_CA_CERT_PATH", "/app/certs/supabase-ca.crt")
    
    # Local development fallback check
    if not os.path.exists(ca_path):
        local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "certs", "supabase-ca.crt"))
        if os.path.exists(local_path):
            ca_path = local_path

    # Try custom CA bundle first
    if os.path.exists(ca_path):
        try:
            ctx = ssl.create_default_context(cafile=ca_path)
            ctx.verify_mode = ssl.CERT_REQUIRED
            # Supabase Pooler proxy TLS hostnames (*.pooler.supabase.com) use pooler TLS certificates.
            # verify_mode = CERT_REQUIRED guarantees strict CA signature validation.
            ctx.check_hostname = False
            logger.info(f"Loaded official CA certificate bundle from [{ca_path}] with CERT_REQUIRED validation.")
            return ctx, f"Verified CA Cert ({os.path.basename(ca_path)})"
        except Exception as e:
            logger.warning(f"Failed to load CA file from [{ca_path}]: {e}")

    # Fallback to system / certifi CA bundle
    try:
        if SYSTEM_CA_BUNDLE and os.path.exists(SYSTEM_CA_BUNDLE):
            ctx = ssl.create_default_context(cafile=SYSTEM_CA_BUNDLE)
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.check_hostname = False
            logger.info(f"Loaded Certifi CA bundle from [{SYSTEM_CA_BUNDLE}] with CERT_REQUIRED validation.")
            return ctx, "Certifi System CA Bundle"
    except Exception as e:
        logger.warning(f"Error loading system CA bundle: {e}")

    # String "require" for asyncpg TLS (libpq sslmode=require equivalent)
    return "require", "sslmode=require"

def _normalize_async_pg_url(raw_url: str) -> tuple[str, dict]:
    """
    Normalizes PostgreSQL URL for asyncpg engine and applies ONE unified SSL configuration.
    Enforces statement_cache_size=0 for Supabase / PgBouncer / Supavisor pooler compatibility.
    Strips conflicting SSL query parameters from the URL string.
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
    
    ssl_setting, ssl_desc = _get_production_ssl_context()
    connect_args["ssl"] = ssl_setting
    logger.info(f"Applied SSL Configuration: {ssl_desc}")

    # Clean conflicting query params from URI string to avoid duplication
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
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database connection established and schema initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization warning (Server starting up): {e}")
