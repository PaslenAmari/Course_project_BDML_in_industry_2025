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
    
    syllabus = [
        {"week": 1, "topics": ["Greetings"]},
        {"week": 2, "topics": ["Numbers"]}
    ]

    print("--- 1. Testing Exercise Alignment ---")
    ex = {"task": "Say hello", "difficulty": "A1"}
    print(agent.align_exercise(syllabus, ex))

    print("\n--- 2. Testing Chat Evaluation ---")
    # Mocking DB response for test purposes
    agent.db.get_student_chat_history = lambda sid, limit=10: [{"question": "Hi?", "answer": "Hello!"}]
    
    student_id = "student_123"
    print(f"Evaluating student: {student_id}")
    print(agent.evaluate_chat(student_id))

    print("\n--- 3. Testing Content Generation ---")
    req = {"week": 1, "type": "multiple_choice", "difficulty": "A1"}
    print(agent.generate_content(syllabus, req))

if __name__ == "__main__":
    main()
