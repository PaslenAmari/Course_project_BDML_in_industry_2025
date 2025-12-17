import logging
import json
from typing import Dict, Any, Optional

from src.agents.base_agent import BaseAgent
from src.database.mongodb_adapter import LanguageLearningDB

logger = logging.getLogger(__name__)

class AssessorAgent(BaseAgent):
    """
    Agent responsible for generating quizzes and evaluating student answers.
    """

    def __init__(self, database_url: str = None):
        super().__init__()
        self.db = LanguageLearningDB(database_url) if database_url else None
        logger.info("AssessorAgent initialized")

    def generate_quiz(self, student_id: str, topic: str, num_questions: int = 3) -> Dict[str, Any]:
        """
        Generates a quiz for the given topic.
        """
        logger.info(f"Generating quiz for {student_id} on topic: {topic}")        
        
        quiz = {
            "topic": topic,
            "questions": []
        }
        
        for i in range(1, num_questions + 1):
            quiz["questions"].append({
                "question_id": i,
                "question_text": f"Question {i} about {topic}",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A"
            })
            
        return quiz

    def evaluate_answers(self, student_id: str, quiz_data: Dict[str, Any], student_answers: Dict[int, str]) -> Dict[str, Any]:
        """
        Evaluates the student's answers against the quiz data.
        """
        logger.info(f"Evaluating answers for {student_id}")
        
        score = 0
        total = len(quiz_data.get("questions", []))
        feedback = []
        
        for question in quiz_data.get("questions", []):
            q_id = question["question_id"]
            correct = question["correct_answer"]
            student_ans = student_answers.get(q_id)
            
            is_correct = (student_ans == correct)
            if is_correct:
                score += 1
                feedback.append(f"Q{q_id}: Correct!")
            else:
                feedback.append(f"Q{q_id}: Incorrect. Correct was {correct}.")
                
        return {
            "student_id": student_id,
            "score": score,
            "total_questions": total,
            "percentage": (score / total) * 100 if total > 0 else 0,
            "feedback": feedback
        }
