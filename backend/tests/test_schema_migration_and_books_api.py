import pytest
import hashlib
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text, select
from app.main import app
from app.database import AsyncSessionLocal, init_db, async_engine
from app.models.schema import Book, ProcessingStatus, Subject
from app.migrations import run_schema_migrations, TABLE_COLUMNS_SPEC

@pytest.mark.asyncio
async def test_schema_migration_adds_missing_columns():
    """
    Test that run_schema_migrations correctly inspects tables and adds any missing columns.
    """
    await init_db()

    async with async_engine.begin() as conn:
        # Run migrations
        await run_schema_migrations(conn)

    # Verify that all expected columns in TABLE_COLUMNS_SPEC['books'] now exist
    async with AsyncSessionLocal() as session:
        # Querying Book using ORM selects all columns defined on Book model
        res = await session.execute(select(Book).limit(5))
        books = res.scalars().all()
        # Successfully queried without UndefinedColumnError
        assert isinstance(books, list)

@pytest.mark.asyncio
async def test_get_books_endpoint_succeeds_after_migration():
    """
    Regression test: GET /api/books must return 200 OK without UndefinedColumnError
    """
    await init_db()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/books")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)

@pytest.mark.asyncio
async def test_books_upload_and_model_fields_integrity():
    """
    Verify Book record creation with all model fields (checksum, storage_path, progress_percent, etc.)
    """
    await init_db()
    async with AsyncSessionLocal() as session:
        # Create a test book with all columns
        test_checksum = hashlib.sha256(b"test pdf content for migration verification").hexdigest()
        
        book = Book(
            title="भारतीय संविधान व राज्यव्यवस्था",
            original_filename="constitution_test.pdf",
            file_path="/tmp/constitution_test.pdf",
            subject_name="राज्यशास्त्र",
            total_pages=50,
            file_size_bytes=10240,
            is_scanned=False,
            status=ProcessingStatus.COMPLETED,
            status_message="Indexing completed successfully",
            progress_percent=100.0,
            current_page_processing=50,
            total_chunks=15,
            checksum=test_checksum,
            storage_path="books/constitution_test.pdf"
        )
        session.add(book)
        await session.commit()
        await session.refresh(book)

        assert book.id is not None
        assert book.checksum == test_checksum
        assert book.storage_path == "books/constitution_test.pdf"
        assert book.progress_percent == 100.0
        assert book.total_chunks == 15
        assert book.is_indexed is True

        # Test API response serialization
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get("/api/books")
            assert res.status_code == 200
            books_json = res.json()
            matching = [b for b in books_json if b["id"] == book.id]
            assert len(matching) == 1
            b_data = matching[0]
            assert b_data["checksum"] == test_checksum
            assert b_data["storage_path"] == "books/constitution_test.pdf"
            assert b_data["progress_percent"] == 100.0

        # Cleanup
        await session.delete(book)
        await session.commit()
