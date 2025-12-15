import logging
import json
from typing import List, Dict, Any, Optional, Union

from src.agents.base_agent import BaseAgent
from src.database.mongodb_adapter import LanguageLearningDB
from src.models.schemas import (
    AlignmentResponse, 
    ChatEvaluationResponse, 
    ExerciseSchema, 
    TheorySchema
)

logger = logging.getLogger(__name__)

class UnifiedTeacherAgent(BaseAgent):
    """
    Unified Teacher Agent that handles:
    1. Exercise Alignment (align_exercise).
    2. Chat Evaluation (evaluate_chat).
    3. Content Generation (generate_content).
    """

    def __init__(self, database_url: str = "mongodb://localhost:27017"):
        super().__init__()
        self.db = LanguageLearningDB(database_url)
        logger.info("UnifiedTeacherAgent initialized")

    # =================================================================
    # 1. Exercise Alignment
    # =================================================================
    def align_exercise(self, student_id: Optional[str], exercise: Dict[str, Any]) -> Union[AlignmentResponse, Dict]:
        """
        Analyzes the exercise and the student's syllabus to find the best match.
        """
        if not student_id:
            student_id = self.db.get_random_student_id()
            if not student_id:
                return {"error": "Student ID not provided and no students found in database."}

        curriculum = self.db.get_curriculum(student_id)
        if not curriculum:
             return {"error": f"Curriculum not found for student {student_id}"}
        
        syllabus = curriculum.get("topics_by_week", [])

        if self.llm is None:
            logger.warning("No LLM, returning mock alignment.")
            return AlignmentResponse(
                week=4,
                topic="Present Simple",
                confidence_score=0.95,
                reasoning="MOCK: Matched verb forms to Present Simple."
            ).model_dump()

        prompt = f"""
You are an expert curriculum developer.
Determine where this exercise fits into the provided syllabus.

Syllabus:
{json.dumps(syllabus, indent=2, ensure_ascii=False)}

Exercise:
{json.dumps(exercise, indent=2, ensure_ascii=False)}

Return JSON matching this schema:
{{
  "week": (int),
  "topic": (string),
  "confidence_score": (float),
  "reasoning": (string)
}}
"""
        return self._invoke_and_parse(prompt, model_class=AlignmentResponse)

    # =================================================================
    # 2. Chat Evaluation
    # =================================================================
    def evaluate_chat(self, student_id: Optional[str] = None) -> Union[ChatEvaluationResponse, Dict]:
        """
        Evaluates Q&A pairs from a chat session.
        """
        if not student_id:
            student_id = self.db.get_random_student_id()
            if not student_id:
                return {"error": "Student ID not provided and no students found in database."}

        chat_history = self.db.get_student_chat_history(student_id)
        
        if not chat_history:
            logger.warning(f"No chat history found for student {student_id}")
            return {"error": "No chat history found"}

        if self.llm is None:
            logger.warning("No LLM, returning mock evaluation.")
            # Return mock data validating against schema
            try:
                return ChatEvaluationResponse(
                    overall_score=85,
                    detailed_feedback="MOCK: Good job!",
                    all_errors=[],
                    improvement_plan="Focus on...",
                    follow_up_questions=["Q1"]
                ).model_dump()
            except:
                return {"error": "Mock data creation failed"}

        prompt = f"""
You are an expert language tutor.
Evaluate the following student answers.

Chat History:
{json.dumps(chat_history, indent=2, ensure_ascii=False)}

Return JSON matching schema:
{{
  "overall_score": (0-100),
  "detailed_feedback": "string",
  "all_errors": [
    {{
       "question_index": (int),
       "student_answer": (string),
       "error_description": (string),
       "correction": (string),
       "rule_explanation": (string)
    }}
  ],
  "improvement_plan": "string",
  "follow_up_questions": ["string"]
}}
"""
        result = self._invoke_and_parse(prompt, model_class=ChatEvaluationResponse)
        
        # Save to DB if valid
        if isinstance(result, dict) and "overall_score" in result:
             eval_data = result.copy()
             eval_data["student_id"] = student_id
             self.db.save_chat_evaluation(eval_data)
             
        return result

    # =================================================================
    # 3. Content Generation
    # =================================================================
    def generate_content(self, student_id: Optional[str], request_params: Dict[str, Any]) -> Union[ExerciseSchema, TheorySchema, Dict]:
        """
        Generates a question/exercise or theory lesson.
        """
        if not student_id:
            student_id = self.db.get_random_student_id()
            if not student_id:
                return {"error": "Student ID not provided."}

        curriculum = self.db.get_curriculum(student_id)
        if not curriculum:
             return {"error": f"Curriculum not found for {student_id}"}
        
        syllabus = curriculum.get("topics_by_week", [])
        target_week = request_params.get("week")
        week_data = next((w for w in syllabus if w.get("week") == target_week), None)
        
        if not week_data:
            return {"error": f"Week {target_week} not found."}
            
        topics = week_data.get("topics", [])
        student_profile = self.db.get_student(student_id)
        target_lang = student_profile.get("target_language", "English") if student_profile else "English"

        if self.llm is None:
            return {"error": "No LLM available"}

        if request_params.get('type') == 'theory':
            prompt = f"""
Generate theory lesson.
Week: {target_week}, Topics: {topics}, Language: {target_lang}

Return JSON (TheorySchema):
{{
  "type": "theory",
  "topic": "string",
  "title": "string",
  "content": "markdown string",
  "key_points": ["string"]
}}
"""
            return self._invoke_and_parse(prompt, model_class=TheorySchema)
        else:
            prompt = f"""
Create practice exercise.
Week: {target_week}, Topics: {topics}, Type: {request_params.get('type')}, Language: {target_lang}

Return JSON (ExerciseSchema):
{{
  "exercise_id": "string",
  "type": "{request_params.get('type')}",
  "topic": "string",
  "task": "string",
  "question": "string",
  "options": ["string"] (optional),
  "correct_answer": "string",
  "explanation": "string",
  "difficulty": {request_params.get('difficulty', 1)}
}}
"""
            return self._invoke_and_parse(prompt, model_class=ExerciseSchema)

    # =================================================================
    # Helper
    # =================================================================
    def _invoke_and_parse(self, prompt: str, model_class=None) -> Any:
        try:
            response = self.llm.invoke(prompt).content
            clean_res = response.strip()
            
            if "```json" in clean_res:
                clean_res = clean_res.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_res:
                clean_res = clean_res.split("```")[1].split("```")[0].strip()
            
            # Heuristic for substring
            start = clean_res.find("{")
            end = clean_res.rfind("}") + 1
            if start != -1 and end != 0:
                clean_res = clean_res[start:end]
            
            data = json.loads(clean_res)
            
            # Validation
            if model_class:
                # Validate and return as dict (for compatibility) or object
                obj = model_class(**data)
                return obj.model_dump()
            
            return data
            
        except Exception as e:
            logger.error(f"LLM/Validation Error: {e}")
            return {"error": str(e)}
