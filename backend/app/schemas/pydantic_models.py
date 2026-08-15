from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime

# --- Subject Schemas ---
class SubjectBase(BaseModel):
    name_mr: str
    name_en: str
    icon: str = "book"
    color: str = "#FF6B35"
    is_custom: bool = False

class SubjectCreate(SubjectBase):
    pass

class SubjectResponse(SubjectBase):
    id: int
    created_at: datetime
    book_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

# --- Book Schemas ---
class BookBase(BaseModel):
    title: str
    subject_name: Optional[str] = "General"

class BookResponse(BookBase):
    id: int
    original_filename: str
    subject_id: Optional[int] = None
    total_pages: int = 0
    file_size_bytes: int = 0
    is_scanned: bool = False
    status: str = "pending"
    status_message: str = ""
    progress_percent: float = 0.0
    current_page_processing: int = 0
    total_chunks: int = 0
    checksum: Optional[str] = None
    storage_path: Optional[str] = None
    is_indexed: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class BookStatusResponse(BaseModel):
    id: int
    title: str
    status: str
    status_message: str
    progress_percent: float
    current_page: int
    total_pages: int
    is_indexed: bool

class BookRenameRequest(BaseModel):
    title: str
    subject_name: Optional[str] = None

# --- Source Citation Schemas ---
class SourceCitation(BaseModel):
    book_id: int
    book_name: str
    subject_name: Optional[str] = ""
    chapter: Optional[str] = ""
    page_number: int
    text_snippet: str
    relevance_score: Optional[float] = 0.0

# --- Chat & Teacher Schemas ---
class ChatRequest(BaseModel):
    session_id: Optional[int] = None
    message: str
    mode: Optional[str] = "general_chat"  # general_chat, teacher_mode, exam_mode, pyq_analysis
    subject_id: Optional[int] = None
    book_id: Optional[int] = None
    stream: Optional[bool] = False

class ChatMessageResponse(BaseModel):
    id: int
    sender: str
    message: str
    sources: List[SourceCitation] = []
    mode: str
    has_audio: bool
    audio_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatSessionResponse(BaseModel):
    id: int
    title: str
    mode: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []

    model_config = ConfigDict(from_attributes=True)

class TeacherTopicRequest(BaseModel):
    topic: str
    subject: Optional[str] = "इतिहास"
    difficulty: Optional[str] = "medium"

# --- MCQ & Test Schemas ---
class MCQOption(BaseModel):
    key: str  # 'A', 'B', 'C', 'D'
    text: str

class MCQQuestion(BaseModel):
    id: Optional[int] = None
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    explanation_mr: str
    difficulty: str = "medium"
    topic_name: Optional[str] = ""
    subject_name: Optional[str] = ""
    source_book: Optional[str] = ""
    source_page: Optional[int] = None

class GenerateMCQRequest(BaseModel):
    subject_name: Optional[str] = "इतिहास"
    topic_name: Optional[str] = None
    book_id: Optional[int] = None
    count: int = Field(default=5, ge=1, le=50)
    difficulty: str = "medium"

class TestCreateRequest(BaseModel):
    title: str = "MPSC सराव चाचणी"
    subject_name: str = "इतिहास"
    topic_name: Optional[str] = "Comprehensive"
    count: int = 10
    difficulty: str = "medium"
    duration_minutes: int = 15

class UserAnswerSubmit(BaseModel):
    question_id: int
    selected_option: Optional[str] = None
    time_spent_seconds: int = 0

class TestSubmitRequest(BaseModel):
    test_id: int
    answers: List[UserAnswerSubmit]
    time_taken_seconds: int = 0

class QuestionResultResponse(BaseModel):
    question_id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    selected_option: Optional[str]
    correct_option: str
    is_correct: bool
    explanation_mr: str
    source_book: Optional[str]
    source_page: Optional[int]

class TestResultResponse(BaseModel):
    test_id: int
    title: str
    subject_name: str
    total_questions: int
    score: float
    correct_count: int
    wrong_count: int
    unattempted_count: int
    accuracy_percentage: float
    time_taken_seconds: int
    weak_areas: List[str] = []
    questions: List[QuestionResultResponse] = []

# --- PYQ Schemas ---
class PYQAnalysisRequest(BaseModel):
    subject_name: Optional[str] = "इतिहास"
    topic: Optional[str] = None

class PYQAnalysisResponse(BaseModel):
    topic: str
    subject_name: str
    frequency_count: int
    key_repeated_concepts: List[str]
    sample_questions: List[MCQQuestion]
    summary_mr: str

# --- Revision Schemas ---
class RevisionItemCreate(BaseModel):
    title: str
    key_fact: str
    subject_name: str = "इतिहास"
    topic_name: Optional[str] = ""
    source_book: Optional[str] = ""
    source_page: Optional[int] = None

class RevisionReviewSubmit(BaseModel):
    item_id: int
    rating: int = Field(ge=1, le=5)  # 1: complete blackout, 5: perfect recall

class RevisionItemResponse(BaseModel):
    id: int
    title: str
    key_fact: str
    subject_name: str
    topic_name: Optional[str]
    source_book: Optional[str]
    source_page: Optional[int]
    repetition_count: int
    interval_days: int
    confidence_level: int
    last_reviewed: datetime
    next_review_due: datetime
    is_due: bool = False

    model_config = ConfigDict(from_attributes=True)

class RevisionSummaryResponse(BaseModel):
    total_items: int
    due_today_count: int
    mastered_count: int
    due_items: List[RevisionItemResponse] = []

# --- Progress & Weak Area Schemas ---
class SubjectMastery(BaseModel):
    subject_name: str
    attempted: int
    correct: int
    mastery_percentage: float
    is_weak_area: bool
    recommendation_mr: str

class ProgressSummaryResponse(BaseModel):
    total_study_minutes: int = 0
    total_books_read: int = 0
    total_tests_taken: int = 0
    total_questions_solved: int = 0
    streak_days: int = 0
    preparation_percentage: float = 0.0
    overall_accuracy: float = 0.0
    total_bookmarks: int = 0
    due_revision_count: int = 0
    subjects_mastery: List[SubjectMastery] = []
    weak_areas: List[str] = []
    recent_activities: List[Dict[str, Any]] = []
    weekly_study_hours: List[float] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

# --- Voice & Audio Schemas ---
class TTSRequest(BaseModel):
    text: str
    speed: float = 1.0  # 0.75, 1.0, 1.25, 1.5
    lang: str = "mr"

class TTSResponse(BaseModel):
    audio_url: str
    duration_seconds: Optional[float] = 0.0

class STTResponse(BaseModel):
    text: str
    confidence: float
    language: str

# --- Settings Schemas ---
class SettingsDTO(BaseModel):
    preferred_language: str = "mr"
    tts_enabled: bool = True
    voice_speed: float = 1.0
    theme_mode: str = "dark"
    ai_provider: str = "auto"
    ai_model: str = "gemini-1.5-flash"
    ai_api_key_configured: bool = False
