import sys
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent.parent))


from src.agents.curriculum_planner_agent import CurriculumPlannerAgent
from src.database.mongodb_adapter import LanguageLearningDB
import time


planner = CurriculumPlannerAgent(database_url="mongodb://localhost:27017")
db = LanguageLearningDB()


students_to_create = [
    {
        "student_id": "emil_english",
        "name": "Emil",
        "target_language": "English",
        "current_level": 3,  
        "goals": "Reach C1 and speak fluently in tech interviews",
        "learning_style": "visual + speaking"
    },
    {
        "student_id": "maria_spanish",
        "name": "Maria",
        "target_language": "Spanish",
        "current_level": 1,  
        "goals": "Pass DELE A2 in 6 months",
        "learning_style": "grammar first"
    },
    {
        "student_id": "alex_english",
        "name": "Alex",
        "target_language": "English",
        "current_level": 4,  
        "goals": "Business English + IELTS 7.5",
        "learning_style": "real-life situations"
    },
    {
        "student_id": "sofia_spanish",
        "name": "Sofía",
        "target_language": "Spanish",
        "current_level": 2,  
        "goals": "Travel and live in Spain",
        "learning_style": "conversational"
    }
]

print("Create/update students and generate plans...\n")
for student in students_to_create:
    sid = student["student_id"]
    print(f"Processing: {student['name']} ({student['target_language']})...")

    
    db.create_student(student.copy())

    
    result = planner.plan_curriculum(sid, force_regenerate=True)

    print(f"   Done! Week {result['next_week']}: {', '.join(result['next_topics'])}")
    time.sleep(0.5)  

print("\n" + "="*100)
print("ALL STUDENTS AND THEIR CURRICULUMS")
print("="*100)


all_students = list(db.db.students.find({}))
all_curriculums = {c["student_id"]: c for c in db.db.curriculums.find({})}

for student in all_students:
    sid = student["_id"]
    curriculum = all_curriculums.get(sid, {})
    topics = curriculum.get("topics_by_week", [])

    print(f"\nStudent: {student.get('name', 'No name')} | ID: {sid}")
    print(f"Language: {student.get('target_language')} | Level: {student.get('current_level', '?')}/6")
    print(f"Goal: {student.get('goals', '-')}")
    print(f"Style: {student.get('learning_style', '-')}")
    print(f"Plan: {curriculum.get('level_from', '?')} to {curriculum.get('level_to', '?')} | {len(topics)} weeks")

    if topics:
        print("   First 5 weeks:")
        for w in topics[:24]:
            print(f"     Week {w['week']:2d} → {', '.join(w['topics'])}")
        
        
    else:
        print("   The plan has not yet been created.")

print("\n" + "="*100)
print("Done! All data is displayed..")
