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
    def align_exercise(self, syllabus: List[Dict[str, Any]], exercise: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes the exercise and syllabus to find the best match.
        """
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
Determine where this exercise fits into the syllabus.

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
    def evaluate_chat(self, student_id: str) -> Dict[str, Any]:
        """
        Evaluates Q&A pairs from a chat session.
        Fetches student answers from the database.
        """
        chat_history = self.db.get_student_chat_history(student_id)
        
        if not chat_history:
            logger.warning(f"No chat history found for student {student_id}")
            return {"error": "No chat history found"}
        if self.llm is None:
            logger.warning("No LLM, returning mock evaluation.")
            result = {
                "overall_score": 85,
                "detailed_feedback": "MOCK: Good job! Your grammar is solid, but watch out for tenses. I like how you used vocabulary X.",
                "corrections": [],
                "follow_up_questions": [
                    "Can you tell me more about ...?",
                    "What would you say if ...?"
                ]
            }
        else:
            prompt = f"""
You are an expert, encouraging, and detailed language tutor.
Evaluate the following student answers deeply.

Chat History:
{json.dumps(chat_history, indent=2, ensure_ascii=False)}

Instructions:
1. Analyze grammatical accuracy, vocabulary, and context relevance.
2. Provide DETAILED feedback explaining the rules behind any errors.
3. Mention specific specific praise for good usage.
4. Generate 2-3 FOLLOW-UP QUESTIONS to test the student's understanding of these topics or to continue the conversation naturally.

Return JSON:
{{
  "overall_score": (0-100),
  "detailed_feedback": "Comprehensive explanation of performance...",
  "corrections": [
    {{
       "index": (int),
       "is_correct": (bool),
       "correction": (string or null),
       "explanation": (string)
    }}
  ],
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
    def generate_content(self, syllabus: List[Dict[str, Any]], request_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a question/exercise based on the syllabus.
        """
        target_week = request_params.get("week")
        week_data = next((w for w in syllabus if w.get("week") == target_week), None)
        
        if not week_data:
            return {"error": f"Week {target_week} not found in syllabus"}
            
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
