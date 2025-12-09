"""Minimal test for Assessor Agent"""
import sys
import json
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.agents.assessor_agent import AssessorAgent
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import config


def run_test():
    print("Initializing AssessorAgent...")
    agent = AssessorAgent(database_url=config.MONGODB_URL)

    student_id = "student_001"
    topic = "Present Simple Tense"

    # 1. Generate Quiz
    print(f"\n1. Generating quiz for topic: '{topic}'")
    quiz = agent.generate_quiz(student_id=student_id, topic=topic, num_questions=3)

    if not quiz:
        print("Failed to generate quiz. Exiting.")
        return

    print("Quiz generated successfully:")
    print(json.dumps(quiz, indent=2))

    # 2. Simulate Student Answers (hardcoded for test)
    print("\n2. Simulating student answers...")
    # Let's assume the student gets one wrong
    student_answers = {
        1: "B",  # Correct
        2: "on", # Incorrect, should be "in"
        3: "I am play football." # Example, may need adjustment based on generated question
    }
    
    # Dynamically set answers based on generated quiz for a more robust test
    # For simplicity, we'll use a mix. Let's assume question 1 and 2 are predictable.
    if quiz['questions'][0]['question_id'] == 1:
        student_answers[1] = quiz['questions'][0]['correct_answer']
    if quiz['questions'][1]['question_id'] == 2:
        student_answers[2] = "at" # Deliberately wrong
    

    print("Student answers:", student_answers)

    # 3. Evaluate Answers
    print("\n3. Evaluating answers...")
    evaluation = agent.evaluate_answers(
        student_id=student_id,
        quiz_data=quiz,
        student_answers=student_answers
    )

    print("\nEvaluation complete:")
    print(json.dumps(evaluation, indent=2, ensure_ascii=False, default=str))

    print("\nAssessorAgent test finished!")

if __name__ == "__main__":
    run_test()





# connection test
# print(">>> test_assessor.py START")

# import sys
# from pathlib import Path

# ROOT = Path(__file__).resolve().parent.parent
# sys.path.insert(0, str(ROOT))

# print(">>> sys.path ok")

# try:
#     import config
#     print(">>> config imported")
# except Exception as e:
#     print("!!! config import error:", e)

# try:
#     from src.agents.assessor_agent import AssessorAgent
#     print(">>> AssessorAgent imported")
# except Exception as e:
#     print("!!! AssessorAgent import error:", e)

# def run_test():
#     print(">>> run_test() called")
#     try:
#         agent = AssessorAgent(database_url="mongodb://localhost:27017")
#         print(">>> AssessorAgent instance created:", agent)
#     except Exception as e:
#         print("!!! Error creating AssessorAgent:", e)

# if __name__ == "__main__":
#     print(">>> __main__ section")
#     run_test()

# print(">>> test_assessor.py END")
