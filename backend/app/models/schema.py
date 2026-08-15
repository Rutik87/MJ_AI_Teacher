import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    OCR_PROCESSING = "ocr_processing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    COMPLETED = "completed"
    FAILED = "failed"

class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuestionType(str, enum.Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    PYQ = "pyq"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, default="mpsc_aspirant")
    display_name = Column(String(150), default="MPSC Aspirant")
    target_exam = Column(String(100), default="MPSC Rajyaseva / Combine")
    preferred_language = Column(String(20), default="mr")  # Marathi default
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    study_sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")
    tests = relationship("Test", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    revision_items = relationship("RevisionItem", back_populates="user", cascade="all, delete-orphan")
    progress_records = relationship("Progress", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    voice_settings = relationship("VoiceSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    books = relationship("Book", back_populates="user", cascade="all, delete-orphan")

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name_mr = Column(String(100), nullable=False, unique=True, index=True)  # e.g., 'महाराष्ट्राचा इतिहास'
    name_en = Column(String(100), nullable=False, index=True)  # e.g., 'Maharashtra History'
    icon = Column(String(50), default="book")
    color = Column(String(30), default="#FF6B35")
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    books = relationship("Book", back_populates="subject_rel")
    chunks = relationship("DocumentChunk", back_populates="subject_rel")
    questions = relationship("Question", back_populates="subject_rel")

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, default=1, index=True)
    title = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    subject_name = Column(String(100), default="General")
    total_pages = Column(Integer, default=0)
    file_size_bytes = Column(Integer, default=0)
    is_scanned = Column(Boolean, default=False)
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING, index=True)
    status_message = Column(String(255), default="Uploaded, waiting for processing...")
    progress_percent = Column(Float, default=0.0)
    current_page_processing = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    checksum = Column(String(64), index=True, nullable=True)  # SHA-256 for duplicate detection
    storage_path = Column(String(500), nullable=True)  # Path in Supabase Storage bucket
    source_type = Column(String(20), default="pdf")  # 'pdf' or 'txt'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_indexed(self) -> bool:
        return self.status == ProcessingStatus.COMPLETED

    # Relationships
    user = relationship("User", back_populates="books")
    subject_rel = relationship("Subject", back_populates="books")
    chapters = relationship("Chapter", back_populates="book", cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="book", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="book", cascade="all, delete-orphan")

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    title = Column(String(255), nullable=False)
    start_page = Column(Integer, default=1)
    end_page = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("Book", back_populates="chapters")
    chunks = relationship("DocumentChunk", back_populates="chapter_rel")

class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    page_number = Column(Integer, nullable=False, index=True)
    extracted_text = Column(Text, default="")
    has_images = Column(Boolean, default=False)
    is_ocr = Column(Boolean, default=False)
    char_count = Column(Integer, default=0)

    book = relationship("Book", back_populates="pages")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True, index=True)
    chunk_uuid = Column(String(64), unique=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    book_title = Column(String(255), default="")
    subject_name = Column(String(100), default="")
    chapter_title = Column(String(255), default="")
    page_number = Column(Integer, nullable=False, index=True)
    chunk_index = Column(Integer, default=0)
    text_content = Column(Text, nullable=False)
    char_count = Column(Integer, default=0)
    embedding_id = Column(String(100), nullable=True)  # ChromaDB ID or vector ID
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("Book", back_populates="chunks")
    subject_rel = relationship("Subject", back_populates="chunks")
    chapter_rel = relationship("Chapter", back_populates="chunks")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    subject_name = Column(String(100), default="")
    topic_name = Column(String(150), default="")
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_option = Column(String(5), nullable=False)  # 'A', 'B', 'C', 'D'
    explanation_mr = Column(Text, default="")
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM)
    is_pyq = Column(Boolean, default=False)
    pyq_year = Column(Integer, nullable=True)
    pyq_exam = Column(String(100), nullable=True)  # e.g., 'Rajyaseva Prelims 2022'
    source_book_name = Column(String(255), default="")
    source_page = Column(Integer, nullable=True)
    source_chapter = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    subject_rel = relationship("Subject", back_populates="questions")

class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    subject_name = Column(String(100), default="All Subjects")
    topic_name = Column(String(150), default="Comprehensive")
    total_questions = Column(Integer, default=10)
    duration_minutes = Column(Integer, default=15)
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.MEDIUM)
    is_completed = Column(Boolean, default=False)
    score = Column(Float, default=0.0)
    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    unattempted_count = Column(Integer, default=0)
    accuracy_percentage = Column(Float, default=0.0)
    time_taken_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="tests")
    test_questions = relationship("TestQuestion", back_populates="test", cascade="all, delete-orphan")
    user_answers = relationship("UserAnswer", back_populates="test", cascade="all, delete-orphan")

class TestQuestion(Base):
    __tablename__ = "test_questions"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    order_number = Column(Integer, default=1)

    test = relationship("Test", back_populates="test_questions")
    question = relationship("Question")

class UserAnswer(Base):
    __tablename__ = "user_answers"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_option = Column(String(5), nullable=True)  # 'A', 'B', 'C', 'D' or None
    is_correct = Column(Boolean, default=False)
    time_spent_seconds = Column(Integer, default=0)

    test = relationship("Test", back_populates="user_answers")
    question = relationship("Question")

class Bookmark(Base):
    __tablename__ = "bookmarks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), default="Answer")  # Answer, Fact, Page, Question
    source_book = Column(String(255), default="")
    source_page = Column(Integer, nullable=True)
    subject_name = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookmarks")

class StudySession(Base):
    __tablename__ = "study_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_name = Column(String(100), default="General")
    topic_name = Column(String(150), default="")
    mode = Column(String(50), default="chat")  # chat, teacher, test, revision, pdf_reading
    duration_minutes = Column(Integer, default=0)
    questions_asked = Column(Integer, default=0)
    pages_read = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="study_sessions")

class RevisionItem(Base):
    __tablename__ = "revision_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    key_fact = Column(Text, nullable=False)
    subject_name = Column(String(100), default="General")
    topic_name = Column(String(150), default="")
    source_book = Column(String(255), default="")
    source_page = Column(Integer, nullable=True)
    repetition_count = Column(Integer, default=0)
    interval_days = Column(Integer, default=1)
    ease_factor = Column(Float, default=2.5)  # SuperMemo SM-2 parameter
    confidence_level = Column(Integer, default=1)  # 1 to 5
    correct_count = Column(Integer, default=0)
    incorrect_count = Column(Integer, default=0)
    last_reviewed = Column(DateTime, default=datetime.utcnow)
    next_review_due = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def is_due(self) -> bool:
        return datetime.utcnow() >= self.next_review_due

    user = relationship("User", back_populates="revision_items")

class Progress(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_name = Column(String(100), nullable=False, index=True)
    topic_name = Column(String(150), default="")
    total_questions_attempted = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)
    mastery_percentage = Column(Float, default=0.0)
    is_weak_area = Column(Boolean, default=False)
    recommended_action_mr = Column(Text, default="")
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="progress_records")

class VoiceSettings(Base):
    __tablename__ = "voice_settings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    tts_enabled = Column(Boolean, default=True)
    voice_speed = Column(Float, default=1.0)  # 0.75, 1.0, 1.25, 1.5
    voice_language = Column(String(20), default="mr-IN")
    stt_language = Column(String(20), default="mr-IN")
    tts_provider = Column(String(50), default="gtts")

    user = relationship("User", back_populates="voice_settings")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), default="नवीन चर्चा")
    mode = Column(String(50), default="general_chat")  # general_chat, teacher_mode, exam_mode, pyq_analysis
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    sender = Column(String(20), nullable=False)  # 'user' or 'ai'
    message = Column(Text, nullable=False)
    sources = Column(JSON, default=list)  # List of source objects: [{book_name, chapter, page_number, text_snippet}]
    mode = Column(String(50), default="general_chat")
    has_audio = Column(Boolean, default=False)
    audio_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    chat_session = relationship("ChatSession", back_populates="messages")

class CurrentAffair(Base):
    __tablename__ = "current_affairs"
    id = Column(Integer, primary_key=True, index=True)
    title_mr = Column(String(300), nullable=False, index=True)
    summary_mr = Column(Text, nullable=False)
    mpsc_relevance_mr = Column(Text, default="")
    important_facts = Column(JSON, default=list)  # List of string bullet points
    topic = Column(String(100), default="महाराष्ट्र", index=True)  # महाराष्ट्र, भारत, आंतरराष्ट्रीय, अर्थव्यवस्था, विज्ञान, पर्यावरण, क्रीडा, योजना
    source_name = Column(String(150), default="PIB / शासकीय वृत्त")
    source_url = Column(String(500), default="")
    published_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    verification_state = Column(String(50), default="verified")  # 'verified', 'cross_checked', 'developing', 'unverified'
    importance_score = Column(Integer, default=5)  # 1-5
    is_bookmarked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    mcqs = relationship("CurrentAffairMCQ", back_populates="article", cascade="all, delete-orphan")

class CurrentAffairMCQ(Base):
    __tablename__ = "current_affair_mcqs"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("current_affairs.id"), nullable=False)
    question_mr = Column(Text, nullable=False)
    option_a = Column(String(300), nullable=False)
    option_b = Column(String(300), nullable=False)
    option_c = Column(String(300), nullable=False)
    option_d = Column(String(300), nullable=False)
    correct_option = Column(String(5), nullable=False)  # 'A', 'B', 'C', 'D'
    explanation_mr = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("CurrentAffair", back_populates="mcqs")
