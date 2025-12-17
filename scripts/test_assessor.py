"""Minimal test for Assessor Agent"""
import sys
import json
from pathlib import Path


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

    
    print(f"\n1. Generating quiz for topic: '{topic}'")
    quiz = agent.generate_quiz(student_id=student_id, topic=topic, num_questions=3)

    if not quiz:
        print("Failed to generate quiz. Exiting.")
        return

    print("Quiz generated successfully:")
    print(json.dumps(quiz, indent=2))

    
    print("\n2. Simulating student answers...")
    
    student_answers = {
        1: "B",  
        2: "on", 
        3: "I am play football." 
    }
    
    
    
    if quiz['questions'][0]['question_id'] == 1:
        student_answers[1] = quiz['questions'][0]['correct_answer']
    if quiz['questions'][1]['question_id'] == 2:
        student_answers[2] = "at" 
    

    print("Student answers:", student_answers)

    
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









































