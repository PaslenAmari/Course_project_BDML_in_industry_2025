import sys
import json
import logging
from pathlib import Path

# Setup path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO)

from src.agents.unified_teacher_agent import UnifiedTeacherAgent

def main():
    agent = UnifiedTeacherAgent()
    
    print("--- 1. Testing Exercise Alignment ---")
    
    # Setup Real Data
    student_id = "test_student_real_db"
    
    # 1. Create Student
    agent.db.create_student({
        "student_id": student_id,
        "name": "Test Student",
        "current_level": 1,
        "target_language": "English"
    })
    
    # 2. Save Curriculum
    syllabus = [
        {"week": 1, "topics": ["Greetings"]},
        {"week": 2, "topics": ["Numbers"]}
    ]
    agent.db.save_curriculum(student_id, {"topics_by_week": syllabus})
    
    # 3. Save Chat History
    agent.db.save_chat_interaction(student_id, "How are you?", "I is fine.")
    agent.db.save_chat_interaction(student_id, "What is this?", "It is a cat.")

    ex = {"task": "Say hello", "difficulty": "A1"}
    print(agent.align_exercise(student_id, ex))

    print("\n--- 2. Testing Chat Evaluation ---")
    print(f"Evaluating student: {student_id}")
    print(agent.evaluate_chat(student_id))

    print("\n--- 3. Testing Content Generation ---")
    req = {"week": 1, "type": "multiple_choice", "difficulty": "A1"}
    print(agent.generate_content(student_id, req))

if __name__ == "__main__":
    main()
