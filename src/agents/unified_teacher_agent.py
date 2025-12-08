import logging
import json
from typing import List, Dict, Any, Optional

from src.agents.base_agent import BaseAgent
from src.database.mongodb_adapter import LanguageLearningDB

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
    def align_exercise(self, student_id: Optional[str], exercise: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes the exercise and the student's syllabus to find the best match.
        Fetches syllabus from DB.
        If student_id is None, picks a random student.
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
            return {
                "week": 4,
                "topic": "Present Simple",
                "confidence_score": 0.95,
                "reasoning": "MOCK: Matched verb forms to Present Simple."
            }

        prompt = f"""
You are an expert curriculum developer.
Determine where this exercise fits into the provided syllabus.

Syllabus:
{json.dumps(syllabus, indent=2, ensure_ascii=False)}

Exercise:
{json.dumps(exercise, indent=2, ensure_ascii=False)}

Return JSON:
{{
  "week": (int),
  "topic": (string),
  "confidence_score": (float),
  "reasoning": (string)
}}
"""
        return self._invoke_and_parse(prompt)

    # =================================================================
    # 2. Chat Evaluation
    # =================================================================
    def evaluate_chat(self, student_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluates Q&A pairs from a chat session.
        Fetches student answers from the database.
        If student_id is None, picks a random student.
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
            result = {
                "overall_score": 85,
                "detailed_feedback": "MOCK: Good job! Your grammar is solid, but watch out for tenses. To improve, practice past simple forms.",
                "all_errors": [
                     {"question": "...", "error": "...", "correction": "..."}
                ],
                "improvement_plan": "Focus on irregular verbs.",
                "corrections": [],
                "follow_up_questions": [
                    "Can you tell me more about ...?",
                    "What would you say if ...?"
                ]
            }
        else:
            prompt = f"""
You are an expert, encouraging, but rigorous language tutor.
Evaluate the following student answers based on the provided Chat History.

Chat History:
{json.dumps(chat_history, indent=2, ensure_ascii=False)}

Instructions:
1. Identify **EVERY** error (grammatical, lexical, spelling).
2. For each error, explain **WHY** it is wrong and what the rule is.
3. Provide a section on **HOW TO IMPROVE** based on these specific mistakes (e.g., "Review Present Perfect", "Practice prepositions").
4. Be encouraging but honest about the score.

Return JSON:
{{
  "overall_score": (0-100),
  "detailed_feedback": "General summary of performance.",
  "all_errors": [
    {{
       "question_index": (int),
       "student_answer": (string),
       "error_description": (string),
       "correction": (string),
       "rule_explanation": (string)
    }}
  ],
  "improvement_plan": "Specific actionable advice...",
  "follow_up_questions": ["Question 1", "Question 2"]
}}
"""
            result = self._invoke_and_parse(prompt)
        
        # Save evaluation to DB
        result["student_id"] = student_id
        if "error" not in result:
             self.db.save_chat_evaluation(result)
             
        return result

    # =================================================================
    # 3. Content Generation
    # =================================================================
    def generate_content(self, student_id: Optional[str], request_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a question/exercise based on the student's syllabus.
        Fetches syllabus from DB using student_id.
        If student_id is None, picks a random student.
        """
        if not student_id:
            student_id = self.db.get_random_student_id()
            if not student_id:
                return {"error": "Student ID not provided and no students found in database."}

        curriculum = self.db.get_curriculum(student_id)
        if not curriculum:
             return {"error": f"Curriculum not found for student {student_id}"}
        
        syllabus = curriculum.get("topics_by_week", [])
        
        target_week = request_params.get("week")
        week_data = next((w for w in syllabus if w.get("week") == target_week), None)
        
        if not week_data:
            return {"error": f"Week {target_week} not found in student's syllabus"}
            
        topics = week_data.get("topics", [])
        
        if self.llm is None:
            logger.warning("No LLM, returning mock content.")
            return {
                "exercise_id": "mock_generated",
                "type": request_params.get("type", "multiple_choice"),
                "question": f"Mock question about {topics[0] if topics else 'General'}",
                "correct_answer": "A"
            }

        prompt = f"""
Create a practice question based on the syllabus.

Context:
- Week: {target_week}
- Topics: {', '.join(topics)}
- Type: {request_params.get('type')}
- Difficulty: {request_params.get('difficulty')}

Return JSON:
{{
  "exercise_id": "generated_id",
  "type": "{request_params.get('type')}",
  "topic": "Specific topic",
  "task": "Instructions",
  "question": "Question text",
  "options": ["A", "B", ...] (if applicable),
  "correct_answer": "Answer",
  "explanation": "Explanation"
}}
"""
        return self._invoke_and_parse(prompt)

    # =================================================================
    # Helper
    # =================================================================
    def _invoke_and_parse(self, prompt: str) -> Dict[str, Any]:
        try:
            response = self.llm.invoke(prompt).content
            clean_res = response.strip()
            
            # Simple markdown cleanup
            if "```json" in clean_res:
                clean_res = clean_res.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_res:
                clean_res = clean_res.split("```")[1].split("```")[0].strip()
            
            # Find bounds
            start = clean_res.find("{")
            end = clean_res.rfind("}") + 1
            if start != -1 and end != 0:
                clean_res = clean_res[start:end]
            
            return json.loads(clean_res)
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return {"error": str(e)}
