import sys
import json
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent.parent))

# scripts/show_all_students.py
from src.agents.curriculum_planner_agent import CurriculumPlannerAgent
from src.database.mongodb_adapter import LanguageLearningDB
import time

# Инициализируем
planner = CurriculumPlannerAgent(database_url="mongodb://localhost:27017")
db = LanguageLearningDB()

# Список учеников для добавления
students_to_create = [
    {
        "student_id": "emil_english",
        "name": "Emil",
        "target_language": "English",
        "current_level": 3,  # B1
        "goals": "Reach C1 and speak fluently in tech interviews",
        "learning_style": "visual + speaking"
    },
    {
        "student_id": "maria_spanish",
        "name": "Maria",
        "target_language": "Spanish",
        "current_level": 1,  # A1
        "goals": "Pass DELE A2 in 6 months",
        "learning_style": "grammar first"
    },
    {
        "student_id": "alex_english",
        "name": "Alex",
        "target_language": "English",
        "current_level": 4,  # B2
        "goals": "Business English + IELTS 7.5",
        "learning_style": "real-life situations"
    },
    {
        "student_id": "sofia_spanish",
        "name": "Sofía",
        "target_language": "Spanish",
        "current_level": 2,  # A2
        "goals": "Travel and live in Spain",
        "learning_style": "conversational"
    }
]

print("Создаём/обновляем студентов и генерируем планы...\n")
for student in students_to_create:
    sid = student["student_id"]
    print(f"Обрабатываем: {student['name']} ({student['target_language']})...")

    # Создаём студента в базе (если ещё нет)
    db.create_student(student.copy())

    # Генерируем план (force_regenerate=True — всегда свежий)
    result = planner.plan_curriculum(sid, force_regenerate=True)

    print(f"   Готово! Неделя {result['next_week']}: {', '.join(result['next_topics'])}")
    time.sleep(0.5)  # чтобы не спамить

print("\n" + "="*100)
print("ВСЕ СТУДЕНТЫ И ИХ УЧЕБНЫЕ ПЛАНЫ")
print("="*100)

# Получаем всех студентов
all_students = list(db.db.students.find({}))
all_curriculums = {c["student_id"]: c for c in db.db.curriculums.find({})}

for student in all_students:
    sid = student["_id"]
    curriculum = all_curriculums.get(sid, {})
    topics = curriculum.get("topics_by_week", [])

    print(f"\nСтудент: {student.get('name', 'Без имени')} | ID: {sid}")
    print(f"Язык: {student.get('target_language')} | Уровень: {student.get('current_level', '?')}/6")
    print(f"Цель: {student.get('goals', '-')}")
    print(f"Стиль обучения: {student.get('learning_style', '-')}")
    print(f"План: {curriculum.get('level_from', '?')} to {curriculum.get('level_to', '?')} | {len(topics)} недель")

    if topics:
        print("   Первые 5 недель:")
        for w in topics[:24]:
            print(f"     Week {w['week']:2d} → {', '.join(w['topics'])}")
        # if len(topics) > 5:
        #     print(f"     ... и ещё {len(topics)-5} недель до Week {topics[-1]['week']}")
    else:
        print("   План ещё не создан")

print("\n" + "="*100)
print("Готово! Все данные выведены.")