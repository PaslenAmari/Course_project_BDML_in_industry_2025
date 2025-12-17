
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

import sys
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.base_agent import BaseAgent
from src.database.mongodb_adapter import LanguageLearningDB

logger = logging.getLogger(__name__)


class CurriculumPlannerAgent(BaseAgent):
    """
    Curriculum Planner Agent
    Create and maintain a long-term curriculum (a weekly schedule of topics).
    It operates autonomously, using only LLM and MongoDB.
    """

    def __init__(self, database_url: str):
        super().__init__()
        self.db = LanguageLearningDB(database_url)
        logger.info("CurriculumPlannerAgent successfully initialized")

    def _get_fallback_curriculum(self, language: str = "English", level_from: str = "A1", level_to: str = "B2") -> Dict:
        """Backup plan in case LLM doesn't respond"""
        topics = [
            ["Greetings", "Introduction"],
            ["Numbers", "Time", "Days of the week"],
            ["Family", "Description of People"],
            ["Food", "Restaurant", "Shopping"],
            ["City", "Road", "Transport"],
            ["Work", "Professions", "Daily Routine"],
            ["Travel", "Hotel", "Airport"],
            ["Past Tense", "Regular Verbs"],
            ["Future Tense", "Plans"],
            ["Habits", "Frequency Adverbs"],
            ["Comparisons", "Adjectives"],
            ["Conditional Sentences"],
        ]
        return {
            "total_weeks": 24,
            "language": language,
            "level_from": level_from,
            "level_to": level_to,
            "generated_at": datetime.utcnow().isoformat(),
            "topics_by_week": [
                {"week": i + 1, "topics": topics[i % len(topics)]}
                for i in range(24)
            ]
        }
    
   
    def _generate_curriculum_with_llm(self, profile: Dict, total_weeks: int = 24) -> Dict:
        """Generating the perfect plan for Qwen3-32B"""
        lang = profile.get("target_language", "English")
        level = profile.get("current_level", 1)
        target_lvl_int = profile.get("target_level", 5)
        
        cefr_scale = ["A1", "A2", "B1", "B2", "C1", "C2"]
        cefr_current = cefr_scale[min(level - 1, 5)]
        cefr_target = cefr_scale[min(target_lvl_int - 1, 5)]
        
        goals = profile.get("goals", "General English fluency")

        prompt = f"""You are the world's best language curriculum designer.

Student level: {cefr_current}
Target level: {cefr_target}
Goal: {goals}
Language: {lang}

Create a {total_weeks}-week course plan. Write names of topics only in English language. 1-2 topics per week.

ANSWER WITH NOTHING BUT THIS EXACT JSON — NO extra text, NO markdown, NO explanations:

{{
  "total_weeks": {total_weeks},
  "language": "{lang}",
  "level_from": "{cefr_current}",
  "level_to": "{cefr_target}",
  "topics_by_week": [
    {{"week": 1, "topics": ["Greetings & Introductions", "Alphabet & Pronunciation"]}},
    {{"week": 2, "topics": ["Numbers 1-100", "Telling Time", "Days & Months"]}},
    {{"week": 3, "topics": ["Family Members", "Possessive Adjectives"]}},
    {{"week": 4, "topics": ["Daily Routine", "Present Simple"]}},
    // ... and so on until week {total_weeks}. The above is just an example; you don't have to use these exact topics; use your level and goal as a guide.
  ]
}}"""

        try:
            response = self.llm.invoke(prompt)
            text = response.content.strip()

            
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON found")
            json_str = text[start:end]
            plan = json.loads(json_str)
            logger.info("LLM successfully generated the perfect plan!")
            return plan

        except Exception as e:
            logger.warning(f"LLM did not return valid JSON: {e}. Using fallback.")
            return self._get_fallback_curriculum(language=lang, level_from=cefr_current, level_to=cefr_target)

    def _find_next_week(self, curriculum: Dict) -> Dict:
        """Determines which week is next"""
        completed = curriculum.get("completed_weeks", 0)
        next_week_num = completed + 1

        for week in curriculum.get("topics_by_week", []):
            if week["week"] == next_week_num:
                return {
                    "week": next_week_num,
                    "topics": week["topics"],
                    "is_last": next_week_num >= curriculum.get("total_weeks", 24)
                }

        
        return {
            "week": next_week_num,
            "topics": ["Final Project", "Free Communication"],
            "is_last": True
        }

    
    
    
    def plan_curriculum(
        self,
        student_id: str,
        total_weeks : int=24,
        force_regenerate: bool = False
    ) -> Dict:
        """
        Creates or updates a syllabus and returns the next topic.
        """
        
        profile = self.db.get_student(student_id)
        if not profile:
            return {"error": "Student not found", "student_id": student_id}

        
        target_lang = profile.get("target_language", "English")
        existing = self.db.get_curriculum(student_id, language=target_lang)

        if existing and not force_regenerate:
            curriculum = existing
            logger.info(f"The existing plan is used for {student_id} ({target_lang})")
        else:
            logger.info(f"A new curriculum is being generated for {student_id} ({target_lang})")
            curriculum = self._generate_curriculum_with_llm(profile, total_weeks=total_weeks)
            curriculum["student_id"] = student_id
            curriculum["language"] = target_lang 
            curriculum["completed_weeks"] = 0
            curriculum["created_at"] = datetime.utcnow().isoformat()

        
        next_lesson = self._find_next_week(curriculum)

        
        if not existing or force_regenerate:
            self.db.save_curriculum(student_id, curriculum)

        
        return {
            "student_id": student_id,
            "next_week": next_lesson["week"],
            "next_topics": next_lesson["topics"],
            "total_weeks": curriculum.get("total_weeks", 24),
            "completed_weeks": curriculum.get("completed_weeks", 0),
            "level_from": curriculum.get("level_from", "A1"),
            "level_to": curriculum.get("level_to", "C1"),
            "message": f"Week {next_lesson['week']}: {', '.join(next_lesson['topics'])}",
            "plan_is_new": not bool(existing) or force_regenerate,
            "topics_by_week": curriculum.get("topics_by_week", [])
        }

    
    def get_next_topics(self, student_id: str) -> Dict:
        """Quickly get only the next topic (without re-creating the plan)"""
        return self.plan_curriculum(student_id, force_regenerate=False)
