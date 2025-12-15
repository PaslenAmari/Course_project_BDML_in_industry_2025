from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.agents.unified_teacher_agent import UnifiedTeacherAgent
from src.agents.language_tools import LanguageTools
from src.models.schemas import (
    ExerciseSchema, 
    TheorySchema, 
    ChatEvaluationResponse
)
from langchain_community.llms import FakeListLLM 

app = FastAPI(
    title="Language Learning MAS API",
    description="Multi-Agent System for Personalized Language Learning",
    version="1.0.0"
)

# Initialize Agents
db_url = "mongodb://mongo:27017"
unified_agent = UnifiedTeacherAgent(database_url=db_url)

# Mock LLM for tools
mock_llm = FakeListLLM(responses=["Mock response"])
tools = LanguageTools(llm=mock_llm)

# --- Request Models ---

class GenerateContentRequest(BaseModel):
    student_id: Optional[str] = None
    week: int
    type: str = "multiple_choice"
    difficulty: int = 1

class ChatEvaluationRequest(BaseModel):
    student_id: str

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the Language Learning MAS API"}

@app.post("/generate/exercise", response_model=Union[ExerciseSchema, TheorySchema, Dict[str, Any]])
def generate_exercise_endpoint(request: GenerateContentRequest):
    """
    Generate an exercise or theory lesson aligned with the student's curriculum.
    """
    params = {
        "week": request.week,
        "type": request.type,
        "difficulty": request.difficulty
    }
    
    result = unified_agent.generate_content(
        student_id=request.student_id,
        request_params=params
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    return result

@app.post("/evaluate/chat", response_model=Union[ChatEvaluationResponse, Dict[str, Any]])
def evaluate_chat_endpoint(request: ChatEvaluationRequest):
    """
    Evaluate recent chat history for a student.
    """
    result = unified_agent.evaluate_chat(student_id=request.student_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
        
    return result

@app.get("/tools/select")
def select_tools_endpoint(level: int, topic: str, phase: str = "practice"):
    """
    Dynamically select tools based on context.
    """
    selected = tools.select_tools_dynamically(
        level=level,
        topic=topic,
        lesson_phase=phase
    )
    return {"selected_tools": selected}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
