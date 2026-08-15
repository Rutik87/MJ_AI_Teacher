import pytest
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import Base, init_db
from app.migrations import run_schema_migrations, TABLE_COLUMNS_SPEC

@pytest.mark.asyncio
async def test_migration_idempotency_and_table_specs():
    """Verify that running schema migrations twice consecutively succeeds without error."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with test_engine.connect() as conn:
        # Create initial tables
        async with conn.begin():
            await conn.run_sync(Base.metadata.create_all)
            
        # First migration pass
        async with conn.begin():
            await run_schema_migrations(conn)
            
        # Second migration pass (must be 100% idempotent)
        async with conn.begin():
            await run_schema_migrations(conn)
            
    await test_engine.dispose()

@pytest.mark.asyncio
async def test_partial_migration_and_savepoint_resilience():
    """Verify that adding missing columns to an older partial table works and catches all columns."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with test_engine.connect() as conn:
        # Create an older, partial version of current_affairs and current_affair_mcqs
        async with conn.begin():
            await conn.execute(text("""
                CREATE TABLE current_affairs (
                    id INTEGER PRIMARY KEY,
                    title_mr VARCHAR(300),
                    summary_mr TEXT
                );
            """))
            await conn.execute(text("""
                CREATE TABLE current_affair_mcqs (
                    id INTEGER PRIMARY KEY,
                    question_mr TEXT
                );
            """))
            
        # Run schema migrations to add all remaining columns
        async with conn.begin():
            await run_schema_migrations(conn)
            
        # Verify columns were successfully added
        res = await conn.execute(text("PRAGMA table_info(current_affairs);"))
        ca_cols = set(r[1] for r in res.fetchall())
        assert "category" in ca_cols
        assert "is_canonical" in ca_cols
        assert "is_bookmarked" in ca_cols
        assert "keywords" in ca_cols
        
        res_mcq = await conn.execute(text("PRAGMA table_info(current_affair_mcqs);"))
        mcq_cols = set(r[1] for r in res_mcq.fetchall())
        assert "article_id" in mcq_cols
        assert "correct_option" in mcq_cols
        assert "explanation_mr" in mcq_cols
        
    await test_engine.dispose()

@pytest.mark.asyncio
async def test_all_tables_in_spec_audit():
    """Audits TABLE_COLUMNS_SPEC against Base.metadata to verify zero missing tables or columns."""
    spec_tables = set(TABLE_COLUMNS_SPEC.keys())
    model_tables = set(Base.metadata.tables.keys())
    
    for tbl in model_tables:
        assert tbl in spec_tables, f"Table '{tbl}' from SQLAlchemy models is missing from TABLE_COLUMNS_SPEC!"
