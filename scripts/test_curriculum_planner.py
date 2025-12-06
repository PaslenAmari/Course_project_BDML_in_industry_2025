import sys
from pathlib import Path
import os
print("=== DEBUG .env ===")
print(f"LITELLM_API_KEY length: {len(os.getenv('LITELLM_API_KEY', ''))}")
print(f"LITELLM_API_KEY starts: {os.getenv('LITELLM_API_KEY', '')[:10] if os.getenv('LITELLM_API_KEY') else 'EMPTY'}")
print(f".env exists: {os.path.exists('.env')}")
print(f"Current dir: {os.getcwd()}")
print("==================")


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.agents.curriculum_planner import CurriculumPlannerAgent
from src.database.mongodb_adapter import LanguageLearningDB


def seed_student():
    """Создаём тестового студента, если его ещё нет."""
    db = LanguageLearningDB("mongodb://localhost:27017")
    student_id = "student_001"
    existing = db.get_student(student_id)
    if existing:
        print("Student already exists:", existing.get("name", ""))
        return student_id

    doc = {
        "_id": student_id,
        "student_id": student_id,
        "name": "Test Student",
        "email": "test@example.com",
        "native_language": "Russian",
        "target_language": "English",
        "current_level": 2,
        "learning_style": "visual",
        "goals": "Подготовка к поездке",
    }
    db.db.students.insert_one(doc)
    print("Seeded new student:", student_id)
    return student_id


def run_test():
    print("Testing CurriculumPlannerAgent...")

    student_id = seed_student()

    agent = CurriculumPlannerAgent(database_url="mongodb://localhost:27017")

    result = agent.plan_curriculum(student_id=student_id, force_regenerate=True)

    print("\nPlanner result:")
    for k, v in result.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    run_test()
