"""
MongoDB adapter for language learning system.
Replaces PostgreSQL/SQLAlchemy version.
Compatible with existing agents and schemas.
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)


class LanguageLearningDB:
    """MongoDB adapter for language learning system"""
    
    def __init__(self, database_url: str = "mongodb://localhost:27017"):
        """Initialize MongoDB connection."""
        try:
            self.client = MongoClient(database_url, serverSelectionTimeoutMS=5000)
            self.db = self.client["language_learning"]
            
            # Check connection (lazy)
            # self.client.admin.command('ping') # Uncomment if MongoDB is running
            
            logger.info("MongoDB connection established")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            # Don't raise here to allow mock testing without real DB
            # raise

    def get_student(self, student_id: str) -> Optional[Dict]:
        """Get student profile from database."""
        try:
            student = self.db.students.find_one({"_id": student_id})
            if not student:
                return None
            return student
        except Exception:
            return None

    def create_student(self, student_data: Dict) -> bool:
        """Create a new student profile."""
        try:
            student_data["created_at"] = datetime.utcnow()
            # Ensure unique ID if not provided, or rely on caller
            if "student_id" not in student_data:
                # Simple generation or let mongo handle _id, but we use student_id as key often
                # For now assume caller provides it as per seed script
                 pass
            
            # Use student_id as _id or index? 
            # get_student uses _id: student_id. So we should probably set _id to student_id
            if "student_id" in student_data:
                student_data["_id"] = student_data["student_id"]
            
            self.db.students.insert_one(student_data)
            return True
        except DuplicateKeyError:
            logger.warning(f"Student {student_data.get('student_id')} already exists.")
            return False
        except Exception as e:
            logger.error(f"Error creating student: {e}")
            return False

    def save_assessment_result(self, assessment_data: Dict) -> str:
        """Save assessment/quiz results."""
        try:
            assessment_data["completed_at"] = datetime.utcnow()
            result = self.db.assessment_results.insert_one(assessment_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving assessment: {e}")
            return ""
            
    def get_curriculum(self, student_id: str) -> Optional[Dict]:
        """Получить текущий учебный план студента."""
        try:
            doc = self.db.learning_plans.find_one({"student_id": student_id})
            return doc
        except Exception as e:
            logger.error(f"Error getting curriculum for {student_id}: {e}")
            return None

    def save_curriculum(self, student_id: str, curriculum: Dict) -> bool:
        """
        Сохранить или обновить учебный план для студента.
        """
        try:
            curriculum["student_id"] = student_id
            curriculum["updated_at"] = datetime.utcnow()
            self.db.learning_plans.update_one(
                {"student_id": student_id},
                {"$set": curriculum},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"Error saving curriculum for {student_id}: {e}")
            return False

    def save_chat_interaction(self, student_id: str, question: str, answer: str) -> bool:
        """Save a single chat Q&A pair."""
        try:
            doc = {
                "student_id": student_id,
                "question": question,
                "answer": answer,
                "created_at": datetime.utcnow()
            }
            self.db.chat_interactions.insert_one(doc)
            return True
        except Exception as e:
            logger.error(f"Error saving chat interaction: {e}")
            return False

    def get_student_chat_history(self, student_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Get recent chat history for a student.
        Returns list of {"question": "...", "answer": "..."}
        """
        try:
            cursor = self.db.chat_interactions.find(
                {"student_id": student_id}
            ).sort("created_at", -1).limit(limit)
            
            history = []
            for doc in cursor:
                history.append({
                    "question": doc.get("question", ""),
                    "answer": doc.get("answer", "")
                })
            return history
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []

    def save_chat_evaluation(self, evaluation_data: Dict) -> bool:
        """
        Save the evaluation result of a chat session.
        """
        try:
            evaluation_data["created_at"] = datetime.utcnow()
            self.db.chat_evaluations.insert_one(evaluation_data)
            return True
        except Exception as e:
            logger.error(f"Error saving chat evaluation: {e}")
            return False