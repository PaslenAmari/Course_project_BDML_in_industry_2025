# """
# Assessor Agent.

# Responsible for:
# - Generating quizzes based on a topic and student level.
# - Evaluating student answers.
# - Providing feedback and scoring.
# - Saving assessment results to the database.
# """

# import logging
# import json
# from typing import Dict, List, Optional, Any

# from src.agents.base_agent import BaseAgent
# from src.database.chroma_db import ChromaVectorDB

# try:
#     from src.database.mongodb_adapter import LanguageLearningDB
# except ImportError:
#     # Fallback if MongoDB not available
#     class LanguageLearningDB:
#         def __init__(self, *args, **kwargs):
#             logger.warning("MongoDB adapter not available")
#         def get_student(self, student_id):
#             return {"student_id": student_id, "current_level": 2}
#         def save_assessment_result(self, data):
#             logger.info(f"Would save assessment: {data}")
#             return "mock_id"

# try:
#     from src.agents.language_tools import LanguageTools
# except ImportError:
#     class LanguageTools:
#         def __init__(self, llm):
#             self.llm = llm


# logger = logging.getLogger(__name__)


# class AssessorAgent(BaseAgent):
#     """
#     Agent that assesses student knowledge by creating and evaluating quizzes.
#     """

#     def __init__(self, database_url: str):
#         """
#         Initialize the Assessor Agent.

#         Args:
#             database_url: MongoDB connection string.
#         """
#         super().__init__()
#         self.db = LanguageLearningDB(database_url)
#         self.tools = LanguageTools(self.llm)
#         logger.info("AssessorAgent initialized")

#     def generate_quiz(
#         self,
#         student_id: str,
#         topic: str,
#         num_questions: int = 5,
#     ) -> Optional[Dict[str, Any]]:
#         """
#         Generates a quiz for a given topic and student level.

#         Args:
#             student_id: The student's identifier.
#             topic: The topic for the quiz.
#             num_questions: The number of questions to generate.

#         Returns:
#             A dictionary representing the quiz, or None on failure.
#         """
#         try:
#             student_profile = self.db.get_student(student_id)
#             if not student_profile:
#                 logger.error(f"Cannot generate quiz: Student {student_id} not found.")
#                 return None

#             student_level = student_profile.get("current_level", 2)

#             prompt = f"""
#             You are an expert language test creator.
#             Generate a quiz with {num_questions} questions for a language learner.

#             Student Profile:
#             - Language Level: {student_level}/5 (A1-C1)
#             - Topic: {topic}

#             Instructions:
#             - Create varied questions (multiple choice, fill-in-the-blank, short answer).
#             - Ensure questions are relevant to the topic and appropriate for the student's level.
#             - Provide clear correct answers and plausible distractors for multiple-choice questions.

#             Return the response as a single JSON object with the following structure:
#             {{
#               "quiz_id": "quiz_{topic.replace(' ', '_').lower()}",
#               "topic": "{topic}",
#               "difficulty_level": {student_level},
#               "questions": [
#                 {{
#                   "question_id": 1,
#                   "type": "multiple_choice",
#                   "text": "Which sentence is grammatically correct?",
#                   "options": ["A) He go to school.", "B) He goes to school.", "C) He is go to school."],
#                   "correct_answer": "B"
#                 }},
#                 {{
#                   "question_id": 2,
#                   "type": "fill_in_the_blank",
#                   "text": "She is interested ___ learning new languages.",
#                   "correct_answer": "in"
#                 }}
#               ]
#             }}
#             """

#             response = self.llm.invoke(prompt)
#             content = response.content

#             # Extract JSON from the response
#             start = content.find("{")
#             end = content.rfind("}") + 1
#             if start != -1 and end != -1:
#                 quiz_data = json.loads(content[start:end])
#                 logger.info(f"Generated quiz with {len(quiz_data.get('questions', []))} questions for topic '{topic}'.")
#                 return quiz_data
#             else:
#                 logger.error("Failed to parse JSON from LLM response for quiz generation.")
#                 return None

#         except Exception as exc:
#             logger.error(f"Error generating quiz: {exc}", exc_info=True)
#             return None

#     def evaluate_answers(
#         self,
#         student_id: str,
#         quiz_data: Dict[str, Any],
#         student_answers: Dict[int, str],
#     ) -> Dict[str, Any]:
#         """
#         Evaluates the student's answers, calculates a score, and provides feedback.

#         Args:
#             student_id: The student's identifier.
#             quiz_data: The quiz data dictionary generated by `generate_quiz`.
#             student_answers: A dictionary mapping question_id to the student's answer.

#         Returns:
#             A dictionary with the evaluation results.
#         """
#         correct_count = 0
#         total_questions = 0
#         evaluation_details = []

#         try:
#             questions = quiz_data.get("questions", [])
#             total_questions = len(questions)

#             for question in questions:
#                 q_id = question["question_id"]
#                 correct_answer = question["correct_answer"]
#                 student_answer = student_answers.get(q_id)

#                 is_correct = (
#                     student_answer is not None and
#                     str(student_answer).strip().lower() == str(correct_answer).strip().lower()
#                 )

#                 if is_correct:
#                     correct_count += 1

#                 evaluation_details.append({
#                     "question_id": q_id,
#                     "question_text": question["text"],
#                     "student_answer": student_answer,
#                     "correct_answer": correct_answer,
#                     "is_correct": is_correct,
#                 })

#             score = (correct_count / total_questions) * 100 if total_questions > 0 else 0

#             # Generate qualitative feedback with LLM
#             feedback_prompt = f"""
#             A language learner has just completed a quiz on the topic "{quiz_data.get('topic')}".
#             Here are their results:
#             {json.dumps(evaluation_details, indent=2)}

#             Score: {score:.2f}%

#             Provide brief, encouraging, and constructive feedback for the student.
#             If they made mistakes, gently explain the core concept they might be missing.
#             Keep the feedback concise (2-3 sentences).
#             """
#             feedback_response = self.llm.invoke(feedback_prompt)
#             feedback_text = feedback_response.content

#             result = {
#                 "student_id": student_id,
#                 "quiz_id": quiz_data.get("quiz_id"),
#                 "topic": quiz_data.get("topic"),
#                 "score": score,
#                 "correct_count": correct_count,
#                 "total_questions": total_questions,
#                 "feedback": feedback_text,
#                 "details": evaluation_details,
#             }

#             # Save the result to the database
#             self.db.save_assessment_result(result)
#             logger.info(f"Assessment for student {student_id} on topic '{result['topic']}' saved with score {score:.2f}%.")

#             return result

#         except Exception as exc:
#             logger.error(f"Error evaluating answers: {exc}", exc_info=True)
#             return {
#                 "error": "An error occurred during evaluation.",
#                 "details": str(exc),
#             }

