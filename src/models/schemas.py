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

class DialogueLine(BaseModel):
    speaker: str
    text: str
    translation: str

class DialogueSchema(BaseModel):
    """Generated dialogue"""
    dialogue_id: str
    topic: str
    situation: str
    level: int
    lines: List[DialogueLine]
    key_phrases: List[str]
    cultural_notes: Optional[str] = None



class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_IN_THE_BLANK = "fill_in_the_blank"
    OPEN_QUESTION = "open_question"
    THEORY = "theory"

class ExerciseSchema(BaseModel):
    """Generated exercise details"""
    exercise_id: Optional[str] = None
    type: QuestionType
    topic: str
    task: Optional[str] = None
    question: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: int = 1

class TheorySchema(BaseModel):
    """Generated theory lesson"""
    type: Literal["theory"] = "theory"
    topic: str
    title: str
    content: str
    key_points: List[str] = []

class AlignmentResponse(BaseModel):
    """Result of aligning content to curriculum"""
    week: int
    topic: str
    confidence_score: float
    reasoning: str

class ErrorDetail(BaseModel):
    """Detailed error analysis from chat"""
    question_index: Optional[int] = None
    student_answer: Optional[str] = None
    error_description: str
    correction: str
    rule_explanation: Optional[str] = None

class ChatEvaluationResponse(BaseModel):
    """Full chat evaluation result"""
    overall_score: int = Field(..., ge=0, le=100)
    detailed_feedback: str
    all_errors: List[ErrorDetail] = []
    improvement_plan: str
    follow_up_questions: List[str] = []

class LessonPlanResponse(BaseModel):
    """High-level lesson response"""
    lesson_id: str
    topic: str
    outline: List[str]
    content: Optional[str] = None
    exercise: Optional[ExerciseSchema] = None
    vocabulary: List[PersonalVocabularySchema] = []
    dialogue: Optional[Dict] = None
    selected_tools: List[str]
    review_materials: List[Dict] = []
    lesson_metadata: Dict = {}

