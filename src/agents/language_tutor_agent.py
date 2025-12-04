# language_tutor_agent.py
"""
Language Tutor Agent.

Uses:
- MongoDB as long-term storage (via LanguageLearningDB)
- Chroma as vector database (via ChromaVectorDB)
- LangGraph for multi-step workflow
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

from langgraph.graph import StateGraph, START, END

from src.agents.base_agent import BaseAgent
from src.agents.language_tools import LanguageTools
from src.database.mongodb_adapter import LanguageLearningDB
from src.database.chroma_db import ChromaVectorDB

logger = logging.getLogger(__name__)


class LanguageTutorAgent(BaseAgent):
    """
    Language Learning Tutor with dynamic tool selection.

    Steps:
    1. Analyze student profile
    2. Retrieve learning materials
    3. Decide if review is needed
    4. Select tools for this lesson
    5. Plan lesson structure
    6. Generate content (exercise, dialogue)
    7. Save lesson session to database
    """

    def __init__(
        self,
        # database_url: str,
        # vector_path: str,
        database_url: str = "mongodb://localhost:27017",
        vector_path: str = "./chroma_data"
    ):
        """
        Initialize Tutor Agent.

        Args:
            database_url: MongoDB connection string
            vector_path: Path to Chroma persistent directory
        """
        super().__init__()

        self.db = LanguageLearningDB(database_url)
        self.vector_store = ChromaVectorDB(vector_path)
        self.tools = LanguageTools(self.llm)
        self.graph = self._build_graph()

        logger.info("LanguageTutorAgent initialized")

    def _build_graph(self):
        """
        Build LangGraph state machine for lesson creation.
        """
        graph = StateGraph(dict)

        graph.add_node("analyze_student", self._analyze_student)
        graph.add_node("retrieve_context", self._retrieve_context)
        graph.add_node("check_review_needs", self._check_review_needs)
        graph.add_node("select_tools", self._select_tools)
        graph.add_node("plan_lesson", self._plan_lesson)
        graph.add_node("generate_content", self._generate_content)
        graph.add_node("save_lesson", self._save_lesson)

        graph.add_edge(START, "analyze_student")
        graph.add_edge("analyze_student", "retrieve_context")
        graph.add_edge("retrieve_context", "check_review_needs")
        graph.add_edge("check_review_needs", "select_tools")
        graph.add_edge("select_tools", "plan_lesson")
        graph.add_edge("plan_lesson", "generate_content")
        graph.add_edge("generate_content", "save_lesson")
        graph.add_edge("save_lesson", END)

        return graph.compile()

    def _analyze_student(self, state: dict) -> dict:
        """
        Phase 1: Load student profile, vocabulary, and error history.
        """
        try:
            student_id = state.get("student_id")

            profile = self.db.get_student(student_id)
            if not profile:
                logger.error(f"Student {student_id} not found")
                state["student_profile"] = {}
                return state

            state["student_profile"] = profile

            vocabulary = self.db.get_student_vocabulary(
                student_id=student_id,
                limit=5,
            )
            state["personal_vocabulary"] = vocabulary

            errors = self.db.get_student_errors(
                student_id=student_id,
                limit=5,
            )
            state["errors_history"] = errors

            logger.info(
                f"Student analyzed: {profile.get('name')} (level {profile.get('current_level')})"
            )
            state["step"] = "analyzed"

        except Exception as exc:
            logger.error(f"Error analyzing student: {exc}")
            state["student_profile"] = {}

        return state

    def _retrieve_context(self, state: dict) -> dict:
        """
        Phase 2: Retrieve current and review materials from vector database.
        """
        try:
            topic = state.get("topic")
            profile = state.get("student_profile", {})
            level = profile.get("current_level", 3)

            current_materials = self.vector_store.search_materials(
                query=f"Language lesson {topic}",
                topic=topic,
                limit=5,
            )
            state["current_content"] = current_materials

            review_materials = self.vector_store.search_materials(
                query=f"Review materials related to {topic}",
                limit=3,
            )
            state["review_materials"] = review_materials

            logger.info(
                f"Retrieved {len(current_materials)} materials for topic '{topic}'"
            )
            state["step"] = "retrieved"

        except Exception as exc:
            logger.error(f"Error retrieving context: {exc}")
            state["current_content"] = []
            state["review_materials"] = []

        return state

    def _check_review_needs(self, state: dict) -> dict:
        """
        Phase 3: Decide if the lesson should focus on review.
        """
        try:
            errors = state.get("errors_history", [])

            if errors:
                state["phase"] = "review"
                state["review_topics"] = errors[:3]
                logger.info(
                    f"Review phase enabled (found {len(errors)} recent errors)"
                )
            else:
                state["phase"] = "new_content"

            state["step"] = "checked_review"

        except Exception as exc:
            logger.error(f"Error checking review needs: {exc}")
            state["phase"] = "new_content"

        return state

    def _select_tools(self, state: dict) -> dict:
        """
        Phase 4: Select tools based on student level, errors, and phase.
        """
        try:
            profile = state.get("student_profile", {})
            errors = state.get("errors_history", [])
            phase = state.get("phase", "practice")
            topic = state.get("topic")

            selected_tools = self.tools.select_tools_dynamically(
                level=profile.get("current_level", 3),
                topic=topic,
                student_errors=[e.get("error_type") for e in errors],
                lesson_phase=phase,
            )

            state["selected_tools"] = selected_tools

            logger.info(f"Selected tools: {selected_tools}")
            state["step"] = "tools_selected"

        except Exception as exc:
            logger.error(f"Error selecting tools: {exc}")
            state["selected_tools"] = ["vocabulary_search", "generate_exercise"]

        return state

    def _plan_lesson(self, state: dict) -> dict:
        """
        Phase 5: Ask LLM to plan lesson structure.
        """
        try:
            profile = state.get("student_profile", {})
            selected_tools = state.get("selected_tools", [])
            phase = state.get("phase", "practice")
            topic = state.get("topic")

            prompt = f"""
            You are an expert language teacher.

            Student profile:
            - Name: {profile.get('name')}
            - Level: {profile.get('current_level')}/5
            - Target language: {profile.get('target_language')}
            - Learning style: {profile.get('learning_style')}

            Lesson request:
            - Topic: {topic}
            - Phase: {phase}
            - Available tools: {', '.join(selected_tools)}

            Design a lesson with four parts:
            1. Warmup (5 minutes)
            2. New content or review (15 minutes)
            3. Practice exercises (20 minutes)
            4. Consolidation and summary (10 minutes)

            Return response in JSON:
            {{
              "outline": ["Warmup: ...", "New content: ...", "Practice: ...", "Review: ..."],
              "estimated_total_minutes": 50
            }}
            """

            response = self.llm.invoke(prompt)
            content = response.content

            start = content.find("{")
            end = content.rfind("}") + 1

            if start >= 0 and end > start:
                lesson_plan = json.loads(content[start:end])
            else:
                lesson_plan = {
                    "outline": [
                        "Warmup",
                        "New content",
                        "Practice",
                        "Review",
                    ],
                    "estimated_total_minutes": 50,
                }

            state["lesson_plan"] = lesson_plan
            state["outline"] = state.get("outline") or lesson_plan.get(
                "outline", []
            )

            logger.info(
                f"Lesson planned for topic '{topic}', duration "
                f"{lesson_plan.get('estimated_total_minutes', 50)} minutes"
            )
            state["step"] = "lesson_planned"

        except Exception as exc:
            logger.error(f"Error planning lesson: {exc}")
            state["lesson_plan"] = {}

        return state

    def _generate_content(self, state: dict) -> dict:
        """
        Phase 6: Generate exercise and dialogue using tools.
        """
        try:
            profile = state.get("student_profile", {})
            selected_tools = state.get("selected_tools", [])
            topic = state.get("topic")
            level = profile.get("current_level", 3)

            content_pieces: Dict[str, Dict] = {}

            if "generate_exercise" in selected_tools:
                exercise = asyncio.run(
                    self.tools.generate_exercise(
                        topic=topic,
                        exercise_type="vocabulary",
                        level=level,
                    )
                )
                content_pieces["exercise"] = exercise

            if "dialogue_generation" in selected_tools:
                dialogue = self.tools.generate_dialogue(
                    topic=topic,
                    situation=f"Discussing {topic}",
                    level=level,
                )
                content_pieces["dialogue"] = dialogue

            state["exercise"] = content_pieces.get("exercise")
            state["dialogue"] = content_pieces.get("dialogue")

            logger.info(
                f"Generated content pieces: {list(content_pieces.keys())}"
            )
            state["step"] = "content_generated"

        except Exception as exc:
            logger.error(f"Error generating content: {exc}")

        return state

    def _save_lesson(self, state: dict) -> dict:
        """
        Phase 7: Save lesson session to MongoDB.
        """
        try:
            lesson_data = {
                "student_id": state.get("student_id"),
                "topic": state.get("topic"),
                "outline": state.get("outline", []),
                "selected_tools": state.get("selected_tools", []),
                "difficulty_level": state.get("student_profile", {}).get(
                    "current_level"
                ),
                "phase": state.get("phase", "new_content"),
                "has_review": len(state.get("review_materials", [])) > 0,
                "duration_minutes": state.get("lesson_plan", {}).get(
                    "estimated_total_minutes", 50
                ),
                "created_at": datetime.utcnow(),
            }

            lesson_id = self.db.save_lesson_session(lesson_data)
            state["lesson_id"] = lesson_id

            logger.info(f"Lesson saved with id={lesson_id}")
            state["step"] = "completed"

        except Exception as exc:
            logger.error(f"Error saving lesson: {exc}")

        return state

    def teach(
        self,
        student_id: str,
        topic: str,
        outline: Optional[List[str]] = None,
    ) -> Dict:
        """
        Main public method: create personalized lesson.

        Args:
            student_id: Student identifier
            topic: Lesson topic
            outline: Optional custom outline

        Returns:
            Dictionary with lesson data (for API or CLI)
        """
        initial_state = {
            "student_id": student_id,
            "topic": topic,
            "outline": outline,
            "difficulty_level": 3,
            "student_profile": {},
            "personal_vocabulary": [],
            "errors_history": [],
            "current_content": [],
            "review_materials": [],
            "lesson_plan": {},
            "selected_tools": [],
            "exercise": None,
            "dialogue": None,
            "phase": "practice",
            "step": "start",
        }

        result = self.graph.invoke(initial_state)

        return {
            "lesson_id": result.get("lesson_id", ""),
            "topic": topic,
            "outline": result.get("outline", []),
            "exercise": result.get("exercise"),
            "dialogue": result.get("dialogue"),
            "vocabulary": result.get("personal_vocabulary", []),
            "selected_tools": result.get("selected_tools", []),
            "review_materials": result.get("review_materials", []),
            "lesson_metadata": {
                "phase": result.get("phase", "new_content"),
                "has_review": len(result.get("review_materials", [])) > 0,
                "duration_minutes": result.get("lesson_plan", {}).get(
                    "estimated_total_minutes", 50
                ),
            },
        }
