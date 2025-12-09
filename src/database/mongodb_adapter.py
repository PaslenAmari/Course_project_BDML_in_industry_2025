# src/database/mongodb_adapter.py
import logging
from typing import Optional, Dict
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

class LanguageLearningDB:
    """MongoDB adapter for language learning system"""

    def __init__(self, database_url: str = "mongodb://localhost:27017"):
        try:
            self.client = MongoClient(database_url, serverSelectionTimeoutMS=5000)
            self.db = self.client["language_learning"]
            logger.info("MongoDB connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")

    def get_student(self, student_id: str) -> Optional[Dict]:
        """Get student profile"""
        try:
            return self.db.students.find_one({"_id": student_id})
        except Exception as e:
            logger.error(f"Error reading student {student_id}: {e}")
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
        
    def get_student_vocabulary(
        self,
        student_id: str,
        limit: int = 20,
    ) -> list[dict]:
        """
        Retrieve a student's personal vocabulary items from MongoDB.

        Args:
            student_id: Unique student identifier.
            limit: Maximum number of vocabulary items to return.

        Returns:
            List of vocabulary documents sorted by recency.
            Each item typically contains:
            - word: target language word or phrase
            - translation: student's L1 translation
            - example: example sentence
            - proficiency: estimated mastery score
            - last_reviewed_at: timestamp of last review
        """
        try:
            cursor = (
                self.db.vocabulary
                .find({"student_id": student_id})
                .sort("last_reviewed_at", -1)
                .limit(limit)
            )
            return list(cursor)
        except Exception as exc:
            logger.error(f"Error retrieving vocabulary for {student_id}: {exc}")
            return []

    def get_student_errors(
        self,
        student_id: str,
        limit: int = 10,
    ) -> list:
        """
        Retrieve recent errors/mistakes made by the student.

        Args:
            student_id: Student identifier.
            limit: Maximum number of error records to return.

        Returns:
            List of error documents sorted by most recent first.
            Each error typically contains:
            - student_id: who made the error
            - error_type: type of error (grammar, vocabulary, pronunciation, etc.)
            - context: lesson or exercise where error occurred
            - correction: what the correct answer should be
            - created_at: when the error was recorded
        """
        try:
            cursor = (
                self.db.student_errors
                .find({"student_id": student_id})
                .sort("created_at", -1)
                .limit(limit)
            )
            return list(cursor)
        except Exception as e:
            logger.error(f"Error retrieving errors for {student_id}: {e}")
            return []
    def save_lesson_session(self, lesson_data: Dict) -> str:
        """
        Save a completed lesson session to the database.

        Args:
            lesson_data: Dictionary containing lesson information:
            - student_id: unique student identifier
            - topic: lesson topic (e.g., "Present Simple Tense")
            - outline: list of lesson steps/sections
            - selected_tools: list of tools used (vocabulary_search, generate_exercise, etc.)
            - difficulty_level: proficiency level (1-5)
            - phase: lesson phase (new_content, review, practice)
            - has_review: boolean indicating if review materials were included
            - duration_minutes: estimated lesson duration
            - exercise: exercise data (optional)
            - dialogue: dialogue data (optional)

        Returns:
            Lesson session ID (MongoDB ObjectId as string) if successful, empty string otherwise.
        """
        try:
            lesson_data["created_at"] = datetime.utcnow()
            result = self.db.lesson_sessions.insert_one(lesson_data)
            logger.info(f"Lesson session saved for {lesson_data.get('student_id')}: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving lesson session: {e}")
            return ""



    def save_assessment_result(self, assessment_data: Dict) -> str:
        """Save assessment/quiz results."""
        try:
            profile["_id"] = profile.get("student_id") or profile["_id"]
            profile.setdefault("created_at", datetime.utcnow())
            profile["updated_at"] = datetime.utcnow()

            self.db.students.update_one(
                {"_id": profile["_id"]},
                {"$set": profile},
                upsert=True
            )
            logger.info(f"Student {profile['_id']} created/updated")
        except Exception as e:
            logger.error(f"Error creating student: {e}")

    def get_curriculum(self, student_id: str, language: Optional[str] = None) -> Optional[Dict]:
        try:
            query = {"student_id": student_id}
            if language:
                query["language"] = language
            return self.db.curriculums.find_one(query)
        except Exception:
            return None

    def save_curriculum(self, student_id: str, curriculum: Dict):
        try:
            curriculum["student_id"] = student_id
            language = curriculum.get("language")
            
            curriculum["updated_at"] = datetime.utcnow().isoformat()
            
            query = {"student_id": student_id}
            if language:
                query["language"] = language
                
            self.db.curriculums.update_one(
                query,
                {"$set": curriculum},
                upsert=True
            )
            logger.info(f"Curriculum saved for {student_id} (Language: {language})")
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

    def get_student_chat_history(self, student_id: str, limit: int = 10):
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

    def get_random_student_id(self) -> Optional[str]:
        """Get a random student ID from the database."""
        try:
            pipeline = [{"$sample": {"size": 1}}]
            result = list(self.db.students.aggregate(pipeline))
            if result:
                return result[0].get("student_id")
            return None
        except Exception as e:
            logger.error(f"Error fetching random student: {e}")
            return None
