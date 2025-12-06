# src/database/mongodb_adapter.py
import logging
from typing import Optional, Dict
from datetime import datetime
from pymongo import MongoClient

logger = logging.getLogger(__name__)

class LanguageLearningDB:
    """MongoDB adapter для системы изучения языков"""

    def __init__(self, database_url: str = "mongodb://localhost:27017"):
        try:
            self.client = MongoClient(database_url, serverSelectionTimeoutMS=5000)
            self.db = self.client["language_learning"]
            logger.info("MongoDB подключён успешно")
        except Exception as e:
            logger.error(f"Не удалось подключиться к MongoDB: {e}")

    def get_student(self, student_id: str) -> Optional[Dict]:
        """Получить профиль студента"""
        try:
            return self.db.students.find_one({"_id": student_id})
        except Exception as e:
            logger.error(f"Ошибка чтения студента {student_id}: {e}")
            return None

    def create_student(self, profile: Dict):
        """Создать или обновить студента"""
        try:
            profile["_id"] = profile.get("student_id") or profile["_id"]
            profile.setdefault("created_at", datetime.utcnow())
            profile["updated_at"] = datetime.utcnow()

            self.db.students.update_one(
                {"_id": profile["_id"]},
                {"$set": profile},
                upsert=True
            )
            logger.info(f"Студент {profile['_id']} создан/обновлён")
        except Exception as e:
            logger.error(f"Ошибка создания студента: {e}")

    def get_curriculum(self, student_id: str) -> Optional[Dict]:
        try:
            return self.db.curriculums.find_one({"student_id": student_id})
        except Exception:
            return None

    def save_curriculum(self, student_id: str, curriculum: Dict):
        try:
            curriculum["student_id"] = student_id
            curriculum["updated_at"] = datetime.utcnow().isoformat()
            self.db.curriculums.update_one(
                {"student_id": student_id},
                {"$set": curriculum},
                upsert=True
            )
            logger.info(f"Учебный план сохранён для {student_id}")
        except Exception as e:
            logger.error(f"Ошибка сохранения плана: {e}")
