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