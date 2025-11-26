# src/models/schemas.py
"""
Pydantic schemas for language learning system.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from enum import Enum
from datetime import datetime


class LanguageLevel(str, Enum):
    """CEFR Levels"""
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class ExerciseType(str, Enum):
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"
    DIALOGUE = "dialogue"
    TRANSLATION = "translation"
    LISTENING = "listening"
    PRONUNCIATION = "pronunciation"


class LessonPhase(str, Enum):
    WARMUP = "warmup"
    NEW_CONTENT = "new_content"
    PRACTICE = "practice"
    REVIEW = "review"
    CONSOLIDATION = "consolidation"


class StudentProfileSchema(BaseModel):
    """Student profile returned from database"""
    student_id: str
    name: str
    email: Optional[str] = None
    native_language: str
    target_language: str
    current_level: int = 1  # 1-5 (maps to A1-C2)
    learning_style: Literal["visual", "auditory", "kinesthetic"] = "visual"
    learning_pace: Literal["slow", "moderate", "fast"] = "moderate"
    interests: List[str] = []
    created_at: Optional[datetime] = None


class PersonalVocabularySchema(BaseModel):
    """Student's vocabulary entry"""
    word: str
    translation: str
    language: str
    context: Optional[str] = None
    topic: str
    repetitions: int = 0
    strength: float = Field(0.5, ge=0.0, le=1.0)
    last_studied: Optional[datetime] = None


class StudentErrorSchema(BaseModel):
    """Tracked student error for targeted review"""
    error_type: Literal["grammar", "vocabulary", "pronunciation", "spelling"]
    original_text: str
    corrected_text: str
    explanation: str
    topic: str
    occurred_at: Optional[datetime] = None
    times_repeated: int = 0


class ExerciseSchema(BaseModel):
    """Generated exercise description"""
    exercise_id: str
    task: str
    instructions: str
    type: ExerciseType
    difficulty: int  # 1-5
    example: Optional[str] = None
    correct_answer: str
    hints: List[str] = []


class LanguageLessonRequest(BaseModel):
    """Request body for /api/tutor/lesson"""
    student_id: str
    topic: str
    outline: Optional[List[str]] = None
    include_review: bool = True
    include_errors: bool = True


class LanguageLessonResponse(BaseModel):
    """
    High-level lesson response used by API.
    This can wrap the raw dict returned by LanguageTutorAgent.
    """
    lesson_id: str
    topic: str
    outline: List[str]
    content: Optional[str] = None
    exercise: Optional[ExerciseSchema] = None
    vocabulary: List[PersonalVocabularySchema] = []
    dialogue: Optional[Dict] = None
    selected_tools: List[str]
    review_materials: List[Dict] = []
    lesson_metadata: Dict
