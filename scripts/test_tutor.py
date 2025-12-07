# test_tutor.py
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.agents.language_tutor_agent import LanguageTutorAgent


def run_test():
    print("Testing LanguageTutorAgent...")

    agent = LanguageTutorAgent()

    result = agent.teach(
        student_id="emil_english",
        topic="Present Simple Tense",
        outline=None,  # можно передать свой список шагов, если нужно
    )

    print("\nLesson result:")
    print("Lesson ID:", result.get("lesson_id"))
    print("Topic:", result.get("topic"))
    print("Outline:", result.get("outline"))
    print("Selected tools:", result.get("selected_tools"))
    print("Has exercise:", result.get("exercise") is not None)
    print("Has dialogue:", result.get("dialogue") is not None)


if __name__ == "__main__":
    run_test()

