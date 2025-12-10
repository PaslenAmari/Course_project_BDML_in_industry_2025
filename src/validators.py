# src/validators.py
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from enum import Enum

class StudentProfile(BaseModel):
    student_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=2, max_length=100)
    target_language: str = Field(...)
    current_level: int = Field(..., ge=1, le=6)
    target_level: int = Field(..., ge=1, le=6)
    learning_style: str = Field(default="general")
    goals: str = Field(default="")
    
    @field_validator('target_level')
    @classmethod
    def validate_target_level(cls, v, info):
        if 'current_level' in info.data and v < info.data['current_level']:
            raise ValueError('Target level must be >= current level')
        return v

class TheoryResponse(BaseModel):
    type: str = "theory"
    title: str = Field(..., min_length=3)
    topic: str
    content: str = Field(..., min_length=10)
    key_points: List[str] = Field(default=[])

class ExerciseQuestion(BaseModel):
    question_id: int = Field(..., ge=1)
    type: str
    content: str
    task: str
    instructions: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: Optional[str] = ""
