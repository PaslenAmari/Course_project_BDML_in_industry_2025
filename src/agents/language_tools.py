
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

    async def generate_exercise(self, topic: str, exercisetype: str, level: int, count: int = 1):
        """Generate multiple exercises asynchronously."""
        exercises = []
        
        for i in range(count):
            try:
                import uuid
                prompt = f"""Create ONE practice exercise #{i+1} out of {count}.

    Topic: {topic}
    Type: {exercisetype}
    Level: {level}

    CRITICAL REQUIREMENTS:
    1. The "type" field MUST be EXACTLY: "{exercisetype}"
    2. The "instructions" field MUST contain clear, specific instructions (NEVER empty or null)
    3. Return ONLY valid JSON, no markdown, no extra text

    Return VALID JSON:
    {{
    "exercise_id": "unique_id_str",
    "type": "{exercisetype}",
    "topic": "{topic}",
    "task": "Clear task (e.g., 'Choose correct answer' or 'Fill in the blank')",
    "instructions": "REQUIRED: Specific clear instructions for this exercise",
    "question": "The question or prompt",
    "options": ["opt1", "opt2", "opt3", "opt4"] or null,
    "correct_answer": "Correct answer",
    "explanation": "Why this is correct",
    "difficulty": {level}
    }}"""
            
                response = self.llm.invoke(prompt)
                content = response.content
                data = self.parse_json(content)
                
                validated = ExerciseSchema(**data).model_dump()
                exercises.append(validated)
                
                logger.info(f"Generated exercise {i+1}/{count}")
                
            except Exception as exc:
                logger.error(f"Error generating exercise {i+1}: {exc}")
                continue
        
        if not exercises:
            raise ValueError(f"Failed to generate any exercises out of {count}")
        
        return exercises



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
            data = self.parse_json(response.content)
            
            validated = DialogueSchema(**data).model_dump()
            logger.info(f"Generated dialogue for topic '{topic}'")
            return validated

        except Exception as exc:
            logger.error(f"Error generating dialogue: {exc}")
            return {"error": str(exc)}

    
    def parse_json(self, text: str) -> Dict:
        start = text.find("{")
        end = text.rfind("}") + 1
        return json.loads(text[start:end])








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
        

        




