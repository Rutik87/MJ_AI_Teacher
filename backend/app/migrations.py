"""
Database Schema Migration & Validation Engine
Ensures that all columns in SQLAlchemy models exist in the underlying PostgreSQL (or SQLite) database.
Executes non-destructive, idempotent ALTER TABLE ADD COLUMN statements.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from app.utils.logger import logger

# Schema definition for all tables and their expected columns
# Format: table_name -> list of (column_name, pg_type, sqlite_type, default_clause)
TABLE_COLUMNS_SPEC = {
    "books": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT 1"),
        ("title", "VARCHAR(255) NOT NULL DEFAULT ''", "VARCHAR(255) NOT NULL DEFAULT ''", None),
        ("original_filename", "VARCHAR(255) NOT NULL DEFAULT ''", "VARCHAR(255) NOT NULL DEFAULT ''", None),
        ("file_path", "VARCHAR(500) NOT NULL DEFAULT ''", "VARCHAR(500) NOT NULL DEFAULT ''", None),
        ("subject_id", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'General'"),
        ("total_pages", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("file_size_bytes", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("is_scanned", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE"),
        ("status", "VARCHAR(50)", "VARCHAR(50)", "DEFAULT 'pending'"),
        ("status_message", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT 'Uploaded, waiting for processing...'"),
        ("progress_percent", "DOUBLE PRECISION", "FLOAT", "DEFAULT 0.0"),
        ("current_page_processing", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("total_chunks", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("checksum", "VARCHAR(64)", "VARCHAR(64)", "DEFAULT NULL"),
        ("storage_path", "VARCHAR(500)", "VARCHAR(500)", "DEFAULT NULL"),
        ("source_type", "VARCHAR(20)", "VARCHAR(20)", "DEFAULT 'pdf'"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "users": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None),
        ("username", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'mpsc_aspirant'"),
        ("display_name", "VARCHAR(150)", "VARCHAR(150)", "DEFAULT 'MPSC Aspirant'"),
        ("target_exam", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'MPSC Rajyaseva / Combine'"),
        ("preferred_language", "VARCHAR(20)", "VARCHAR(20)", "DEFAULT 'mr'"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "subjects": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None),
        ("name_mr", "VARCHAR(100)", "VARCHAR(100)", None),
        ("name_en", "VARCHAR(100)", "VARCHAR(100)", None),
        ("icon", "VARCHAR(50)", "VARCHAR(50)", "DEFAULT 'book'"),
        ("color", "VARCHAR(30)", "VARCHAR(30)", "DEFAULT '#FF6B35'"),
        ("is_custom", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "document_chunks": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None),
        ("chunk_uuid", "VARCHAR(64)", "VARCHAR(64)", "DEFAULT ''"),
        ("book_id", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("subject_id", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("chapter_id", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("book_title", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT ''"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT ''"),
        ("chapter_title", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT ''"),
        ("page_number", "INTEGER", "INTEGER", "DEFAULT 1"),
        ("chunk_index", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("text_content", "TEXT", "TEXT", "DEFAULT ''"),
        ("char_count", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("embedding_id", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT NULL"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "questions": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None),
        ("subject_id", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT ''"),
        ("topic_name", "VARCHAR(150)", "VARCHAR(150)", "DEFAULT ''"),
        ("question_text", "TEXT", "TEXT", "DEFAULT ''"),
        ("option_a", "TEXT", "TEXT", "DEFAULT ''"),
        ("option_b", "TEXT", "TEXT", "DEFAULT ''"),
        ("option_c", "TEXT", "TEXT", "DEFAULT ''"),
        ("option_d", "TEXT", "TEXT", "DEFAULT ''"),
        ("correct_option", "VARCHAR(5)", "VARCHAR(5)", "DEFAULT 'A'"),
        ("explanation_mr", "TEXT", "TEXT", "DEFAULT ''"),
        ("difficulty", "VARCHAR(50)", "VARCHAR(50)", "DEFAULT 'medium'"),
        ("is_pyq", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE"),
        ("pyq_year", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("pyq_exam", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT NULL"),
        ("source_book_name", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT ''"),
        ("source_page", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("source_chapter", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT ''"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "tests": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT 1"),
        ("title", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT 'MPSC Mock Test'"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'General'"),
        ("topic_name", "VARCHAR(200)", "VARCHAR(200)", "DEFAULT 'General'"),
        ("total_questions", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("score", "DOUBLE PRECISION", "FLOAT", "DEFAULT 0.0"),
        ("correct_count", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("wrong_count", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("unattempted_count", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("accuracy_percentage", "DOUBLE PRECISION", "FLOAT", "DEFAULT 0.0"),
        ("time_taken_seconds", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("is_completed", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
        ("completed_at", "TIMESTAMP", "DATETIME", "DEFAULT NULL"),
    ],
    "progress": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT 1"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'General'"),
        ("topic_name", "VARCHAR(200)", "VARCHAR(200)", "DEFAULT 'General'"),
        ("total_questions_attempted", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("total_correct", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("total_study_minutes", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("mastery_percentage", "DOUBLE PRECISION", "FLOAT", "DEFAULT 0.0"),
        ("is_weak_area", "BOOLEAN", "BOOLEAN", "DEFAULT FALSE"),
        ("recommended_action_mr", "TEXT", "TEXT", "DEFAULT NULL"),
        ("last_activity", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "study_sessions": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT 1"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'General'"),
        ("topic_name", "VARCHAR(200)", "VARCHAR(200)", "DEFAULT 'General'"),
        ("duration_minutes", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("notes", "TEXT", "TEXT", "DEFAULT NULL"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "bookmarks": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT 1"),
        ("question_id", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("chunk_id", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("book_id", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("title", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT ''"),
        ("content", "TEXT", "TEXT", "DEFAULT ''"),
        ("notes", "TEXT", "TEXT", "DEFAULT NULL"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'General'"),
        ("page_number", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "revision_items": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None),
        ("user_id", "INTEGER", "INTEGER", "DEFAULT 1"),
        ("question_id", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("chunk_id", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("title", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT ''"),
        ("key_fact", "TEXT", "TEXT", "DEFAULT ''"),
        ("subject_name", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'General'"),
        ("topic_name", "VARCHAR(200)", "VARCHAR(200)", "DEFAULT 'General'"),
        ("source_book", "VARCHAR(255)", "VARCHAR(255)", "DEFAULT NULL"),
        ("source_page", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("repetitions", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("interval_days", "INTEGER", "INTEGER", "DEFAULT 1"),
        ("ease_factor", "DOUBLE PRECISION", "FLOAT", "DEFAULT 2.5"),
        ("confidence_level", "INTEGER", "INTEGER", "DEFAULT 0"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
    ],
    "current_affairs": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None),
        ("title_mr", "VARCHAR(300) NOT NULL", "VARCHAR(300) NOT NULL", None),
        ("summary_mr", "TEXT NOT NULL", "TEXT NOT NULL", None),
        ("mpsc_relevance_mr", "TEXT", "TEXT", "DEFAULT ''"),
        ("important_facts", "JSON", "JSON", "DEFAULT '[]'"),
        ("topic", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'महाराष्ट्र'"),
        ("category", "VARCHAR(100)", "VARCHAR(100)", "DEFAULT 'महाराष्ट्र'"),
        ("keywords", "JSON", "JSON", "DEFAULT '[]'"),
        ("syllabus_topic", "VARCHAR(150)", "VARCHAR(150)", "DEFAULT ''"),
        ("source_name", "VARCHAR(150)", "VARCHAR(150)", "DEFAULT 'PIB / शासकीय वृत्त'"),
        ("source_url", "VARCHAR(500)", "VARCHAR(500)", "DEFAULT ''"),
        ("published_at", "TIMESTAMP", "DATETIME", "DEFAULT NULL"),
        ("updated_at", "TIMESTAMP", "DATETIME", "DEFAULT NULL"),
        ("verified_at", "TIMESTAMP", "DATETIME", "DEFAULT NULL"),
        ("verification_state", "VARCHAR(50)", "VARCHAR(50)", "DEFAULT 'verified'"),
        ("importance_score", "INTEGER", "INTEGER", "DEFAULT 5"),
        ("is_canonical", "BOOLEAN", "BOOLEAN", "DEFAULT 1"),
        ("duplicate_group_id", "VARCHAR(64)", "VARCHAR(64)", "DEFAULT NULL"),
        ("is_bookmarked", "BOOLEAN", "BOOLEAN", "DEFAULT 0"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT NULL"),
    ],
    "current_affair_mcqs": [
        ("id", "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY", None),
        ("article_id", "INTEGER", "INTEGER", "DEFAULT NULL"),
        ("question_mr", "TEXT NOT NULL", "TEXT NOT NULL", None),
        ("option_a", "VARCHAR(300) NOT NULL", "VARCHAR(300) NOT NULL", None),
        ("option_b", "VARCHAR(300) NOT NULL", "VARCHAR(300) NOT NULL", None),
        ("option_c", "VARCHAR(300) NOT NULL", "VARCHAR(300) NOT NULL", None),
        ("option_d", "VARCHAR(300) NOT NULL", "VARCHAR(300) NOT NULL", None),
        ("correct_option", "VARCHAR(5) NOT NULL", "VARCHAR(5) NOT NULL", "DEFAULT 'A'"),
        ("explanation_mr", "TEXT", "TEXT", "DEFAULT ''"),
        ("created_at", "TIMESTAMP", "DATETIME", "DEFAULT CURRENT_TIMESTAMP"),
    ],
}

async def run_schema_migrations(conn: AsyncConnection):
    """
    Executes idempotent, non-destructive schema migrations across all tables.
    Adds any missing columns to existing production tables without dropping or altering existing data.
    """
    dialect_name = conn.sync_connection.dialect.name.lower()
    is_postgres = "postgres" in dialect_name
    is_sqlite = "sqlite" in dialect_name
    
    logger.info(f"Running database schema migration check (Dialect: {dialect_name})...")

    # 1. Fetch existing tables
    if is_postgres:
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
        existing_tables = set(r[0] for r in res.fetchall())
    elif is_sqlite:
        res = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        existing_tables = set(r[0] for r in res.fetchall())
    else:
        existing_tables = set()

    for table_name, columns in TABLE_COLUMNS_SPEC.items():
        if table_name not in existing_tables:
            # Table will be created by Base.metadata.create_all
            continue

        # Fetch existing columns for this table
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

        for col_name, pg_type, sqlite_type, default_clause in columns:
            if col_name.lower() not in existing_cols:
                col_type = pg_type if is_postgres else sqlite_type
                default_str = f" {default_clause}" if default_clause else ""
                
                logger.info(f"Migrating table '{table_name}': Adding missing column '{col_name}' ({col_type}{default_str})...")
                
                try:
                    if is_postgres:
                        alter_stmt = text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_name} {col_type}{default_str};")
                    else:
                        alter_stmt = text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}{default_str};")
                    
                    await conn.execute(alter_stmt)
                    logger.info(f"Successfully added column '{col_name}' to table '{table_name}'.")
                except Exception as ex:
                    logger.warning(f"Note on adding column '{col_name}' to table '{table_name}': {ex}")

    # Ensure indexes for books
    if is_postgres:
        try:
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_books_checksum ON books (checksum);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_books_status ON books (status);"))
        except Exception as e:
            logger.debug(f"Index creation notice: {e}")

    logger.info("Database schema migrations completed successfully.")
