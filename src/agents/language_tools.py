
"""
Language-specific tools for agents.

Provides utilities for:
- Dynamic tool selection based on student profile
- Exercise generation
- Dialogue generation
- Vocabulary search
"""

import json
import logging
import asyncio
from typing import List, Dict, Optional, Union

from src.models.schemas import ExerciseSchema, DialogueSchema

logger = logging.getLogger(__name__)

class LanguageTools:
    """
    Collection of tools for language learning agents.
    """

    def __init__(self, llm):
        """
        Initialize tools with LLM client.
        """
        self.llm = llm
        logger.info("LanguageTools initialized")

    def select_tools_dynamically(self, level, topic, student_errors=None, lesson_phase="practice"):
        
        
        
        pass 

    async def generate_exercise(
        self,
        topic: str,
        exercise_type: str,
        level: int,
        count: int = 1,
    ) -> Union[Dict, List[Dict]]:
        """
        Generate one or more exercises asynchronously.
        """
        try:
            import uuid
            
            prompt = f"""
Create practice exercise.
Topic: {topic}, Type: {exercise_type}, Level: {level}

Return JSON (ExerciseSchema):
{{
  "exercise_id": "string",
  "type": "{exercise_type}",
  "topic": "string",
  "task": "string",
  "question": "string",
  "options": ["string"] (optional),
  "correct_answer": "string",
  "explanation": "string",
  "difficulty": {level}
}}
"""
            
            
            response = self.llm.invoke(prompt)
            content = response.content
            
            
            data = self._parse_json(content)
            
            if count > 1:
                
                
                
                
                validated = ExerciseSchema(**data).model_dump()
                return [validated] 
            else:
                validated = ExerciseSchema(**data).model_dump()
                return validated
        
        except Exception as exc:
            logger.error(f"Error generating exercise: {exc}")
            return {"error": str(exc)}

    def generate_dialogue(
        self,
        topic: str,
        situation: str,
        level: int,
    ) -> Dict:
        """
        Generate a dialogue for practice.
        """
        try:
            prompt = f"""
Generate dialogue.
Topic: {topic}, Situation: {situation}, Level: {level}

Return JSON (DialogueSchema):
{{
  "dialogue_id": "string",
  "topic": "string",
  "situation": "string",
  "level": {level},
  "lines": [{{"speaker": "A", "text": "...", "translation": "..."}}],
  "key_phrases": ["..."],
  "cultural_notes": "..."
}}
"""
            response = self.llm.invoke(prompt)
            data = self._parse_json(response.content)
            
            validated = DialogueSchema(**data).model_dump()
            logger.info(f"Generated dialogue for topic '{topic}'")
            return validated

        except Exception as exc:
            logger.error(f"Error generating dialogue: {exc}")
            return {"error": str(exc)}

    def _parse_json(self, text: str) -> Dict:
        clean_res = text.strip()
        if "```json" in clean_res:
             clean_res = clean_res.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_res:
             clean_res = clean_res.split("```json")[1].split("```")[0].strip()
        
        start = clean_res.find("{")
        end = clean_res.rfind("}") + 1
        if start != -1 and end != 0:
             clean_res = clean_res[start:end]
        return json.loads(clean_res)

    def explain_grammar(
        self,
        rule: str,
        examples: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a grammar explanation.

        Args:
            rule: The grammar rule to explain
            examples: Optional list of examples

        Returns:
            Explanation text
        """
        try:
            examples_text = "\n".join(examples) if examples else "No examples provided"

            prompt = f"""
            Explain the following grammar rule in simple terms:
            
            Rule: {rule}
            Examples: {examples_text}
            
            Provide a clear, beginner-friendly explanation with examples.
            Keep it concise (3-4 sentences max).
            """

            response = self.llm.invoke(prompt)
            logger.info(f"Generated grammar explanation for rule: {rule}")
            return response.content

        except Exception as exc:
            logger.error(f"Error explaining grammar: {exc}")
            return "Error generating explanation"
        

        




