# src/agents/curriculum_planner_agent.py
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

from src.agents.base_agent import BaseAgent
from src.database.mongodb_adapter import LanguageLearningDB

logger = logging.getLogger(__name__)


class CurriculumPlannerAgent(BaseAgent):
    """
    Curriculum Planner Agent
    Делает ровно одну вещь: создаёт и поддерживает долгосрочный учебный план (расписание тем на недели).
    Работает автономно, использует только LLM и MongoDB.
    """

    def __init__(self, database_url: str):
        super().__init__()  # → self.llm уже доступен
        self.db = LanguageLearningDB(database_url)
        logger.info("CurriculumPlannerAgent успешно инициализирован")

    def _get_fallback_curriculum(self, language: str = "English") -> Dict:
        """Запасной план на случай, если LLM не ответит"""
        topics = [
            ["Приветствия", "Представление"],
            ["Числа", "Время", "Дни недели"],
            ["Семья", "Описание людей"],
            ["Еда", "Ресторан", "Покупки"],
            ["Город", "Дорога", "Транспорт"],
            ["Работа", "Профессии", "Распорядок дня"],
            ["Путешествия", "Отель", "Аэропорт"],
            ["Прошедшее время", "Регулярные глаголы"],
            ["Будущее время", "Планы"],
            ["Привычки", "Частотные наречия"],
            ["Сравнения", "Прилагательные"],
            ["Условные предложения"],
        ]
        return {
            "total_weeks": 24,
            "language": language,
            "level_from": "A1",
            "level_to": "B2+",
            "generated_at": datetime.utcnow().isoformat(),
            "topics_by_week": [
                {"week": i + 1, "topics": topics[i % len(topics)]}
                for i in range(24)
            ]
        }

    def _generate_curriculum_with_llm(self, profile: Dict) -> Dict:
        """Генерация плана через LLM"""
        lang = profile.get("target_language", "English")
        level = profile.get("current_level", 1)
        goals = profile.get("goals", "Общее развитие")
        style = profile.get("learning_style", "смешанный")

        cefr = ["A1", "A2", "B1", "B2", "C1", "C2"][min(level - 1, 5)]

        prompt = f"""
Ты — эксперт по составлению учебных планов по иностранным языкам.

Студент изучает: {lang}
Текущий уровень: {cefr} (внутренний уровень {level}/6)
Цели: {goals}
Стиль обучения: {style}

Составь подробный план на 24 недели.
Каждая неделя — 1–2 логически связанные темы.

Ответь ТОЛЬКО валидным JSON, без пояснений:
{{
  "total_weeks": 24,
  "language": "{lang}",
  "level_from": "{cefr}",
  "level_to": "C1",
  "topics_by_week": [
    {{"week": 1, "topics": ["Приветствия", "Представление"]}},
    {{"week": 2, "topics": ["Числа до 100", "Время"]}},
    ...
  ]
}}
"""

        try:
            response = self.invoke_llm(prompt)
            # Убираем ```json и т.п.
            json_str = response.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("```", 2)[1]
                if json_str.lower().startswith("json"):
                    json_str = json_str[4:]
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"LLM не смог сгенерировать план: {e}. Используется fallback.")
            return self._get_fallback_curriculum(lang)

    def _find_next_week(self, curriculum: Dict) -> Dict:
        """Определяет, какая неделя следующая"""
        completed = curriculum.get("completed_weeks", 0)
        next_week_num = completed + 1

        for week in curriculum.get("topics_by_week", []):
            if week["week"] == next_week_num:
                return {
                    "week": next_week_num,
                    "topics": week["topics"],
                    "is_last": next_week_num >= curriculum.get("total_weeks", 24)
                }

        # Если план закончился
        return {
            "week": next_week_num,
            "topics": ["Итоговый проект", "Свободное общение"],
            "is_last": True
        }

    # =================================================================
    # Основной публичный метод
    # =================================================================
    def plan_curriculum(
        self,
        student_id: str,
        force_regenerate: bool = False
    ) -> Dict:
        """
        Создаёт или обновляет учебный план и возвращает следующую тему.
        """
        # 1. Загружаем профиль
        profile = self.db.get_student(student_id)
        if not profile:
            return {"error": "Студент не найден", "student_id": student_id}

        # 2. Проверяем, есть ли уже план
        existing = self.db.get_curriculum(student_id)

        if existing and not force_regenerate:
            curriculum = existing
            logger.info(f"Используется существующий план для {student_id}")
        else:
            logger.info(f"Генерируется новый учебный план для {student_id}")
            curriculum = self._generate_curriculum_with_llm(profile)
            curriculum["student_id"] = student_id
            curriculum["completed_weeks"] = 0
            curriculum["created_at"] = datetime.utcnow().isoformat()

        # 3. Определяем следующую неделю
        next_lesson = self._find_next_week(curriculum)

        # 4. Сохраняем (если обновляли)
        if not existing or force_regenerate:
            self.db.save_curriculum(student_id, curriculum)

        # 5. Возвращаем результат
        return {
            "student_id": student_id,
            "next_week": next_lesson["week"],
            "next_topics": next_lesson["topics"],
            "total_weeks": curriculum.get("total_weeks", 24),
            "completed_weeks": curriculum.get("completed_weeks", 0),
            "level_from": curriculum.get("level_from", "A1"),
            "level_to": curriculum.get("level_to", "C1"),
            "message": f"Неделя {next_lesson['week']}: {', '.join(next_lesson['topics'])}",
            "plan_is_new": not bool(existing) or force_regenerate
        }

    # Удобный алиас
    def get_next_topics(self, student_id: str) -> Dict:
        """Быстро получить только следующую тему (без пересоздания плана)"""
        return self.plan_curriculum(student_id, force_regenerate=False)
