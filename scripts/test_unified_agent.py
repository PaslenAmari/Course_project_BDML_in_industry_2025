import sys
import json
import logging
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO)

from src.agents.unified_teacher_agent import UnifiedTeacherAgent

def main():
    agent = UnifiedTeacherAgent()
    
    print("--- 1. Testing Exercise Alignment (Random Student) ---")
    ex = {"task": "Say hello", "difficulty": "A1"}
    
    print(agent.align_exercise(None, ex))

    print("\n--- 2. Testing Chat Evaluation (Random Student) ---")
    print(agent.evaluate_chat(None))

    print("\n--- 3. Testing Content Generation (Random Student) ---")
    req = {"week": 1, "type": "multiple_choice", "difficulty": "A1"}
    print(agent.generate_content(None, req))

if __name__ == "__main__":
    main()
