# src/backend/main.py
"""
FastAPI backend for Language Learning Multi-Agent System
Provides REST API for all agents
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator, constr, Field
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from src.agents.curriculum_planner_agent import CurriculumPlannerAgent
from src.agents.theory_agent import TheoryAgent
from src.agents.unified_teacher_agent import UnifiedTeacherAgent
from src.agents.language_tutor_agent import LanguageTutorAgent
from src.database.mongodb_adapter import LanguageLearningDB
from src.database.chroma_db import ChromaVectorDB

# ============================================================================
# LOGGING & SETUP
# ============================================================================

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Language Learning Multi-Agent System",
    description="AI-powered language learning platform with semantic search and personalized curriculum",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS для фронтэнда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# PYDANTIC MODELS (Validation + Safety)
# ============================================================================

class StudentProfile(BaseModel):
    """Student profile for creation/update"""
    student_id: constr(min_length=1, max_length=100)
    name: constr(min_length=1, max_length=200)
    target_language: str
    current_level: int = Field(..., ge=1, le=6)
    target_level: int = Field(..., ge=1, le=6)
    learning_style: Optional[str] = "general"
    goals: Optional[str] = None
    
    @validator('student_id')
    def validate_student_id(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("student_id must be alphanumeric with underscores/hyphens")
        return v
    
    @validator('target_language')
    def validate_language(cls, v):
        allowed = ["English", "Spanish", "French", "German", "Chinese", "Japanese"]
        if v not in allowed:
            raise ValueError(f"Language must be one of {allowed}")
        return v


class CurriculumRequest(BaseModel):
    """Request to generate curriculum"""
    student_id: constr(min_length=1, max_length=100)
    weeks: int = Field(24, ge=4, le=52)
    force_regenerate: bool = False
    
    @validator('student_id')
    def validate_student_id(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Invalid student_id")
        return v


class TheoryRequest(BaseModel):
    """Request to generate theory"""
    topic: constr(min_length=1, max_length=500)
    week: int = Field(..., ge=1, le=52)
    level: str = Field(..., pattern=r'^[A-C][12]$')  # A1, A2, B1, B2, C1, C2
    language: str
    
    @validator('topic')
    def validate_topic(cls, v):
        dangerous = ["exec(", "eval(", "import ", "__import"]
        if any(x.lower() in v.lower() for x in dangerous):
            raise ValueError("Invalid topic: contains dangerous patterns")
        return v


class ContentRequest(BaseModel):
    """Request to generate content"""
    student_id: constr(min_length=1, max_length=100)
    week: int = Field(..., ge=1, le=52)
    type: str = Field(..., regex='^(theory|multiple_choice|fill_in_the_blank|open_question)$')
    difficulty: int = Field(..., ge=1, le=6)


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    mongodb_connected: bool
    chroma_healthy: bool


# ============================================================================
# GLOBAL AGENTS (lazy initialization)
# ============================================================================

_planner = None
_theory_agent = None
_unified_teacher = None
_tutor = None
_db = None
_chroma = None


def get_planner():
    global _planner
    if _planner is None:
        _planner = CurriculumPlannerAgent(database_url="mongodb://localhost:27017")
    return _planner


def get_theory():
    global _theory_agent
    if _theory_agent is None:
        _theory_agent = TheoryAgent()
    return _theory_agent


def get_unified_teacher():
    global _unified_teacher
    if _unified_teacher is None:
        _unified_teacher = UnifiedTeacherAgent(database_url="mongodb://localhost:27017")
    return _unified_teacher


def get_tutor():
    global _tutor
    if _tutor is None:
        _tutor = LanguageTutorAgent()
    return _tutor


def get_db():
    global _db
    if _db is None:
        _db = LanguageLearningDB(database_url="mongodb://localhost:27017")
    return _db


def get_chroma():
    global _chroma
    if _chroma is None:
        _chroma = ChromaVectorDB(persist_dir="./chroma_data")
    return _chroma


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Check system health"""
    try:
        db = get_db()
        chroma = get_chroma()
        
        mongodb_ok = db.db is not None
        chroma_ok = chroma.health_check()
        
        return HealthCheck(
            status="healthy" if (mongodb_ok and chroma_ok) else "degraded",
            timestamp=datetime.utcnow(),
            mongodb_connected=mongodb_ok,
            chroma_healthy=chroma_ok
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


# ============================================================================
# STUDENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/students/create")
async def create_student(profile: StudentProfile):
    """Create a new student profile"""
    try:
        db = get_db()
        success = db.create_student(profile.model_dump())
        
        if success:
            return {
                "status": "success",
                "student_id": profile.student_id,
                "message": "Student profile created"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create student")
            
    except Exception as e:
        logger.error(f"Error creating student: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/students/{student_id}")
async def get_student(student_id: str):
    """Get student profile"""
    try:
        db = get_db()
        student = db.get_student(student_id)
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        return student
        
    except Exception as e:
        logger.error(f"Error getting student: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CURRICULUM ENDPOINTS
# ============================================================================

@app.post("/api/v1/curriculum/plan")
async def plan_curriculum(request: CurriculumRequest):
    """Generate personalized curriculum for student"""
    try:
        planner = get_planner()
        result = planner.plan_curriculum(
            student_id=request.student_id,
            total_weeks=request.weeks,
            force_regenerate=request.force_regenerate
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error planning curriculum: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/curriculum/{student_id}")
async def get_curriculum(student_id: str, language: Optional[str] = None):
    """Get curriculum for student"""
    try:
        db = get_db()
        curriculum = db.get_curriculum(student_id, language)
        
        if not curriculum:
            raise HTTPException(status_code=404, detail="Curriculum not found")
        
        return curriculum
        
    except Exception as e:
        logger.error(f"Error getting curriculum: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# THEORY ENDPOINTS
# ============================================================================

@app.post("/api/v1/theory/generate")
async def generate_theory(request: TheoryRequest):
    """Generate theory lesson for topic"""
    try:
        theory = get_theory()
        result = theory.generate_theory(
            topic=request.topic,
            week=request.week,
            level=request.level,
            language=request.language
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to generate theory"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating theory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONTENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/content/generate")
async def generate_content(request: ContentRequest):
    """Generate exercise/content for student"""
    try:
        teacher = get_unified_teacher()
        result = teacher.generate_content(
            student_id=request.student_id,
            request_params={
                "week": request.week,
                "type": request.type,
                "difficulty": request.difficulty
            }
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# VECTOR DATABASE ENDPOINTS
# ============================================================================

@app.get("/api/v1/materials/search")
async def search_materials(
    query: constr(min_length=1, max_length=500),
    level: Optional[int] = None,
    limit: int = 5
):
    """Search learning materials using semantic search"""
    try:
        chroma = get_chroma()
        results = chroma.search_materials(query=query, level=level, limit=limit)
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching materials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/errors/search")
async def search_errors(
    query: constr(min_length=1, max_length=500),
    limit: int = 5
):
    """Search error patterns"""
    try:
        chroma = get_chroma()
        results = chroma.search_error_patterns(query=query, limit=limit)
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching errors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch all exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    logger.info("Starting up Language Learning MAS...")
    try:
        get_db()
        get_chroma()
        get_planner()
        get_theory()
        logger.info("All agents initialized successfully")
    except Exception as e:
        logger.error(f"Startup failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Language Learning MAS...")


# ============================================================================
# ROOT
# ============================================================================

@app.get("/")
async def root():
    """API root with information"""
    return {
        "name": "Language Learning Multi-Agent System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "students": "/api/v1/students",
            "curriculum": "/api/v1/curriculum",
            "theory": "/api/v1/theory",
            "content": "/api/v1/content",
            "materials": "/api/v1/materials"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)