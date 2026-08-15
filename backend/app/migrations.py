"""
Database Schema Migration & Validation Engine (Production Grade)
Ensures all columns in SQLAlchemy models exist in the underlying PostgreSQL (or SQLite) database.
Executes non-destructive, idempotent ALTER TABLE ADD COLUMN statements with transaction safety.
"""

from typing import Dict, List, Tuple, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from app.utils.logger import logger

# Schema definition for all tables and their expected columns
# Format: table_name -> list of (col_name, pg_type, sqlite_type, pg_default, sqlite_default)
TABLE_COLUMNS_SPEC: Dict[str, List[Tuple[str, str, str, Optional[str], Optional[str]]]] = {
    "users": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("username", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'mpsc_aspirant'", "DEFAULT 'mpsc_aspirant'"),
        ("display_name", "VARCHAR(150)", "VARCHAR(150)", "DEFAULT 'MPSC Aspirant'", "DEFAULT 'MPSC Aspirant'"),
        ("target_exam", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'MPSC Rajyaseva / Combine'", "DEFAULT 'MPSC Rajyaseva / Combine'"),
        ("preferred_language", "VARCHAR(20)", "VARCHAR(20)", "DEFAULT 'mr'", "DEFAULT 'mr'"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "subjects": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("name_mr", "VARCHAR(100)", "VARCHAR(100)", None, None),
        ("name_en", "VARCHAR(100)", "VARCHAR(100)", None, None),
        ("icon", "VARCHAR(50)", "VARCHAR(50)", "DEFAULT 'book'", "DEFAULT 'book'"),
        ("color", "VARCHAR(30)", "VARCHAR(30)", "DEFAULT '#FF6B35'", "DEFAULT '#FF6B35'"),
        ("is_custom", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE", "DEFAULT 0"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "books": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT 1", "DEFAULT 1"),
        ("title", "VARCHAR(255) NOT NULL", "VARCHAR(255) NOT NULL", "DEFAULT ''", "DEFAULT ''"),
        ("original_filename", "VARCHAR(255) NOT NULL", "VARCHAR(255) NOT NULL", "DEFAULT ''", "DEFAULT ''"),
        ("file_path", "VARCHAR(500) NOT NULL", "VARCHAR(500) NOT NULL", "DEFAULT ''", "DEFAULT ''"),
        ("subject_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'General'", "DEFAULT 'General'"),
        ("total_pages", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("file_size_bytes", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("is_scanned", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE", "DEFAULT 0"),
        ("status", "VARCHAR(50)", "VARCHAR(50)", "DEFAULT 'pending'", "DEFAULT 'pending'"),
        ("status_message", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT 'Uploaded, waiting for processing...'", "DEFAULT 'Uploaded, waiting for processing...'"),
        ("progress_percent", "DOUBLE PRECISION", "FLOAT", "DEFAULT 0.0", "DEFAULT 0.0"),
        ("current_page_processing", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("total_chunks", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("checksum", "VARCHAR(64)", "VARCHAR(64)", "DEFAULT NULL", "DEFAULT NULL"),
        ("storage_path", "VARCHAR(500)", "VARCHAR(500)", "DEFAULT NULL", "DEFAULT NULL"),
        ("source_type", "VARCHAR(20)", "VARCHAR(20)", "DEFAULT 'pdf'", "DEFAULT 'pdf'"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "chapters": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("book_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("title", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT ''", "DEFAULT ''"),
        ("start_page", "INTEGER", "INTEGER", "DEFAULT 1", "DEFAULT 1"),
        ("end_page", "INTEGER", "INTEGER", "DEFAULT 1", "DEFAULT 1"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "pages": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("book_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("page_number", "INTEGER", "INTEGER", "DEFAULT 1", "DEFAULT 1"),
        ("extracted_text", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("has_images", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE", "DEFAULT 0"),
        ("is_ocr", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE", "DEFAULT 0"),
        ("char_count", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
    ],
    "document_chunks": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("chunk_uuid", "VARCHAR(64)", "VARCHAR(64)", "DEFAULT ''", "DEFAULT ''"),
        ("book_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("subject_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("chapter_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("book_title", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT ''", "DEFAULT ''"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT ''", "DEFAULT ''"),
        ("chapter_title", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT ''", "DEFAULT ''"),
        ("page_number", "INTEGER", "INTEGER", "DEFAULT 1", "DEFAULT 1"),
        ("chunk_index", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("text_content", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("char_count", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("embedding_id", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT NULL", "DEFAULT NULL"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "questions": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("subject_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT ''", "DEFAULT ''"),
        ("topic_name", "VARCHAR(150)", "VARCHAR(150)", "DEFAULT ''", "DEFAULT ''"),
        ("question_text", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("option_a", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("option_b", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("option_c", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("option_d", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("correct_option", "VARCHAR(5)", "VARCHAR(5)", "DEFAULT 'A'", "DEFAULT 'A'"),
        ("explanation_mr", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("difficulty", "VARCHAR(50)", "VARCHAR(50)", "DEFAULT 'medium'", "DEFAULT 'medium'"),
        ("is_pyq", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE", "DEFAULT 0"),
        ("pyq_year", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("pyq_exam", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT NULL", "DEFAULT NULL"),
        ("source_book_name", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT ''", "DEFAULT ''"),
        ("source_page", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("source_chapter", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT ''", "DEFAULT ''"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "tests": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT 1", "DEFAULT 1"),
        ("title", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT 'MPSC Mock Test'", "DEFAULT 'MPSC Mock Test'"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'General'", "DEFAULT 'General'"),
        ("topic_name", "VARCHAR(200)", "VARCHAR(200)", "DEFAULT 'General'", "DEFAULT 'General'"),
        ("total_questions", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("score", "DOUBLE PRECISION", "FLOAT", "DEFAULT 0.0", "DEFAULT 0.0"),
        ("correct_count", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("wrong_count", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("unattempted_count", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("accuracy_percentage", "DOUBLE PRECISION", "FLOAT", "DEFAULT 0.0", "DEFAULT 0.0"),
        ("time_taken_seconds", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("is_completed", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE", "DEFAULT 0"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
        ("completed_at", "TIMESTAMP", "DATETIME", "DEFAULT NULL", "DEFAULT NULL"),
    ],
    "test_questions": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("test_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("question_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("order_number", "INTEGER", "INTEGER", "DEFAULT 1", "DEFAULT 1"),
    ],
    "user_answers": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("test_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("question_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("selected_option", "VARCHAR(5)", "VARCHAR(5)", "DEFAULT NULL", "DEFAULT NULL"),
        ("is_correct", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE", "DEFAULT 0"),
        ("time_spent_seconds", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
    ],
    "progress": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT 1", "DEFAULT 1"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'General'", "DEFAULT 'General'"),
        ("topic_name", "VARCHAR(200)", "VARCHAR(200)", "DEFAULT 'General'", "DEFAULT 'General'"),
        ("total_questions_attempted", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("total_correct", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("total_study_minutes", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("mastery_percentage", "DOUBLE PRECISION", "FLOAT", "DEFAULT 0.0", "DEFAULT 0.0"),
        ("is_weak_area", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE", "DEFAULT 0"),
        ("recommended_action_mr", "TEXT", "TEXT", "DEFAULT NULL", "DEFAULT NULL"),
        ("last_activity", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "study_sessions": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT 1", "DEFAULT 1"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'General'", "DEFAULT 'General'"),
        ("topic_name", "VARCHAR(200)", "VARCHAR(200)", "DEFAULT 'General'", "DEFAULT 'General'"),
        ("duration_minutes", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("notes", "TEXT", "TEXT", "DEFAULT NULL", "DEFAULT NULL"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "bookmarks": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT 1", "DEFAULT 1"),
        ("question_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("chunk_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("book_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("title", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT ''", "DEFAULT ''"),
        ("content", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("notes", "TEXT", "TEXT", "DEFAULT NULL", "DEFAULT NULL"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'General'", "DEFAULT 'General'"),
        ("page_number", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "revision_items": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT 1", "DEFAULT 1"),
        ("question_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("chunk_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("title", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT ''", "DEFAULT ''"),
        ("key_fact", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'General'", "DEFAULT 'General'"),
        ("topic_name", "VARCHAR(200)", "VARCHAR(200)", "DEFAULT 'General'", "DEFAULT 'General'"),
        ("source_book", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT NULL", "DEFAULT NULL"),
        ("source_page", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("repetitions", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("interval_days", "INTEGER", "INTEGER", "DEFAULT 1", "DEFAULT 1"),
        ("ease_factor", "DOUBLE PRECISION", "FLOAT", "DEFAULT 2.5", "DEFAULT 2.5"),
        ("confidence_level", "INTEGER", "INTEGER", "DEFAULT 0", "DEFAULT 0"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "voice_settings": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("voice_type", "VARCHAR(50)", "VARCHAR(50)", "DEFAULT 'mj_primary'", "DEFAULT 'mj_primary'"),
        ("speech_speed", "DOUBLE PRECISION", "FLOAT", "DEFAULT 1.0", "DEFAULT 1.0"),
        ("pitch", "DOUBLE PRECISION", "FLOAT", "DEFAULT 1.0", "DEFAULT 1.0"),
        ("volume", "DOUBLE PRECISION", "FLOAT", "DEFAULT 1.0", "DEFAULT 1.0"),
        ("marathi_accent_mode", "VARCHAR(50)", "VARCHAR(50)", "DEFAULT 'standard_pune'", "DEFAULT 'standard_pune'"),
        ("is_enabled", "BOOLEAN", "BOOLEAN", "DEFAULT TRUE", "DEFAULT 1"),
        ("updated_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "chat_sessions": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("title", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT 'नवीन चर्चा'", "DEFAULT 'नवीन चर्चा'"),
        ("mode", "VARCHAR(50)", "VARCHAR(50)", "DEFAULT 'general_chat'", "DEFAULT 'general_chat'"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "chat_messages": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("session_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("sender", "VARCHAR(20)", "VARCHAR(20)", "DEFAULT 'user'", "DEFAULT 'user'"),
        ("message", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("sources", "JSON", "JSON", "DEFAULT '[]'::json", "DEFAULT '[]'"),
        ("mode", "VARCHAR(50)", "VARCHAR(50)", "DEFAULT 'general_chat'", "DEFAULT 'general_chat'"),
        ("has_audio", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE", "DEFAULT 0"),
        ("audio_url", "VARCHAR(500)", "VARCHAR(500)", "DEFAULT NULL", "DEFAULT NULL"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "current_affairs": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("title_mr", "VARCHAR(300)", "VARCHAR(300)", "DEFAULT ''", "DEFAULT ''"),
        ("summary_mr", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("mpsc_relevance_mr", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("important_facts", "JSON", "JSON", "DEFAULT '[]'::json", "DEFAULT '[]'"),
        ("topic", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'महाराष्ट्र'", "DEFAULT 'महाराष्ट्र'"),
        ("category", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'महाराष्ट्र'", "DEFAULT 'महाराष्ट्र'"),
        ("keywords", "JSON", "JSON", "DEFAULT '[]'::json", "DEFAULT '[]'"),
        ("syllabus_topic", "VARCHAR(150)", "VARCHAR(150)", "DEFAULT ''", "DEFAULT ''"),
        ("source_name", "VARCHAR(150)", "VARCHAR(150)", "DEFAULT 'PIB / शासकीय वृत्त'", "DEFAULT 'PIB / शासकीय वृत्त'"),
        ("source_url", "VARCHAR(500)", "VARCHAR(500)", "DEFAULT ''", "DEFAULT ''"),
        ("published_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
        ("verified_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
        ("verification_state", "VARCHAR(50)", "VARCHAR(50)", "DEFAULT 'verified'", "DEFAULT 'verified'"),
        ("importance_score", "INTEGER", "INTEGER", "DEFAULT 5", "DEFAULT 5"),
        ("is_canonical", "BOOLEAN", "BOOLEAN", "DEFAULT TRUE", "DEFAULT 1"),
        ("duplicate_group_id", "VARCHAR(64)", "VARCHAR(64)", "DEFAULT NULL", "DEFAULT NULL"),
        ("is_bookmarked", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE", "DEFAULT 0"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "current_affair_mcqs": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None, None),
        ("article_id", "INTEGER", "INTEGER", "DEFAULT NULL", "DEFAULT NULL"),
        ("question_mr", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("option_a", "VARCHAR(300)", "VARCHAR(300)", "DEFAULT ''", "DEFAULT ''"),
        ("option_b", "VARCHAR(300)", "VARCHAR(300)", "DEFAULT ''", "DEFAULT ''"),
        ("option_c", "VARCHAR(300)", "VARCHAR(300)", "DEFAULT ''", "DEFAULT ''"),
        ("option_d", "VARCHAR(300)", "VARCHAR(300)", "DEFAULT ''", "DEFAULT ''"),
        ("correct_option", "VARCHAR(5)", "VARCHAR(5)", "DEFAULT 'A'", "DEFAULT 'A'"),
        ("explanation_mr", "TEXT", "TEXT", "DEFAULT ''", "DEFAULT ''"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP"),
    ],
}

async def run_schema_migrations(conn: AsyncConnection):
    """
    Executes idempotent, non-destructive schema migrations across all tables.
    Uses SAVEPOINTS / isolated transaction blocks so any individual failure
    never leaves the connection in an aborted PostgreSQL transaction state.
    """
    dialect_name = conn.sync_connection.dialect.name.lower()
    is_postgres = "postgres" in dialect_name
    is_sqlite = "sqlite" in dialect_name
    
    logger.info(f"Starting schema migration & validation (Dialect: {dialect_name})...")

    # 1. Fetch existing tables safely
    try:
        if is_postgres:
            res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
            existing_tables = set(r[0].lower() for r in res.fetchall())
        elif is_sqlite:
            res = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            existing_tables = set(r[0].lower() for r in res.fetchall())
        else:
            existing_tables = set()
    except Exception as e:
        logger.error(f"Failed to query existing database tables: {e}")
        existing_tables = set()

    # 2. Iterate through each table specification
    for table_name, columns in TABLE_COLUMNS_SPEC.items():
        if table_name.lower() not in existing_tables:
            logger.debug(f"Table '{table_name}' does not exist yet (will be created by SQLAlchemy Base.metadata).")
            continue

        # Fetch existing columns for this table
        try:
            if is_postgres:
                col_res = await conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}';
                """))
                existing_cols = set(r[0].lower() for r in col_res.fetchall())
            elif is_sqlite:
                col_res = await conn.execute(text(f"PRAGMA table_info({table_name});"))
                existing_cols = set(r[1].lower() for r in col_res.fetchall())
            else:
                existing_cols = set()
        except Exception as col_err:
            logger.error(f"Failed to inspect columns for table '{table_name}': {col_err}")
            existing_cols = set()

        for col_name, pg_type, sqlite_type, pg_default, sqlite_default in columns:
            if col_name.lower() in existing_cols:
                continue

            col_type = pg_type if is_postgres else sqlite_type
            default_clause = pg_default if is_postgres else sqlite_default
            default_str = f" {default_clause}" if default_clause else ""

            if is_postgres:
                sql_stmt = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_name} {col_type}{default_str};"
            else:
                sql_stmt = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}{default_str};"

            logger.info(f"Migrating table '{table_name}': Executing [{sql_stmt}]...")

            # Execute with savepoint protection to prevent aborted transaction state
            try:
                if is_postgres:
                    # In PostgreSQL, use SAVEPOINT so any syntax or type error is safely contained
                    async with conn.begin_nested():
                        await conn.execute(text(sql_stmt))
                else:
                    await conn.execute(text(sql_stmt))
                logger.info(f"Successfully added column '{col_name}' to '{table_name}'.")
            except Exception as ex:
                logger.warning(f"Note on migration statement [{sql_stmt}]: {ex}")

    # 3. Ensure critical indexes for fast RAG and search
    if is_postgres:
        indexes = [
            "CREATE INDEX IF NOT EXISTS ix_books_checksum ON books (checksum);",
            "CREATE INDEX IF NOT EXISTS ix_books_status ON books (status);",
            "CREATE INDEX IF NOT EXISTS ix_current_affairs_category ON current_affairs (category);",
            "CREATE INDEX IF NOT EXISTS ix_current_affairs_published_at ON current_affairs (published_at);",
            "CREATE INDEX IF NOT EXISTS ix_document_chunks_book_id ON document_chunks (book_id);",
        ]
        for idx_sql in indexes:
            try:
                async with conn.begin_nested():
                    await conn.execute(text(idx_sql))
            except Exception as idx_ex:
                logger.debug(f"Index notice [{idx_sql}]: {idx_ex}")

    logger.info("Database schema migration check completed successfully.")
