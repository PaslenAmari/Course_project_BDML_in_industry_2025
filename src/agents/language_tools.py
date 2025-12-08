# language_tools.py
"""
Language-specific tools for agents.

Provides utilities for:
- Dynamic tool selection based on student profile
- Exercise generation
- Dialogue generation
- Vocabulary search
"""

import logging
import asyncio
import json
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class LanguageTools:
    """
    Collection of tools for language learning agents.
    """

    def __init__(self, llm):
        """
        Initialize tools with LLM client.
        
        Args:
            llm: LangChain LLM client
        """
        self.llm = llm
        logger.info("LanguageTools initialized")

    def select_tools_dynamically(
        self,
        level: int,
        topic: str,
        student_errors: Optional[List[str]] = None,
        lesson_phase: str = "practice",
    ) -> List[str]:
        """
        Select appropriate tools based on student profile.

        Args:
            level: Student proficiency level (1-5)
            topic: Lesson topic
            student_errors: List of error types (optional)
            lesson_phase: Current lesson phase

        Returns:
            List of tool names to use
        """
        tools = []

        # Base tools for all levels
        tools.append("vocabulary_search")

        # Level-based tool selection
        if level <= 2:
            tools.append("generate_exercise")
        elif level <= 3:
            tools.append("generate_exercise")
            tools.append("dialogue_generation")
        else:
            tools.append("dialogue_generation")
            tools.append("grammar_explanation")

        # Error-based tool selection
        if student_errors:
            if "grammar" in student_errors:
                tools.append("grammar_explanation")
            if "pronunciation" in student_errors:
                tools.append("pronunciation_guide")

        # Phase-based tool selection
        if lesson_phase == "review":
            tools.append("spaced_repetition")
        elif lesson_phase == "practice":
            tools.append("interactive_practice")

        logger.info(f"Selected tools for level {level}: {tools}")
        return list(set(tools))  # Remove duplicates

    async def generate_exercise(
        self,
        topic: str,
        exercise_type: str,
        level: int,
        count: int = 1,
    ) -> Dict:
        """
        Generate one or more exercises asynchronously.
        If count > 1, returns {"exercises": [list of exercises]}.
        If count == 1, returns the single exercise dict.
        """
        try:
            import uuid
            
            if count > 1:
                prompt = f"""
                Generate {count} {exercise_type} exercises for learning {topic}.
                
                Level: {level}/5 (1=Beginner, 5=Advanced)
                
                Return as JSON with a key "exercises" containing a list of {count} exercise objects.
                Each object must follow this structure:
                {{
                "exercise_id": "ex_<unique_id>",
                "type": "{exercise_type}",
                "task": "The main instruction (e.g., 'Fill in the blank', 'Find the mistake')",
                "content": "The specific sentence, word, or dialogue snippet to analyze/modify. THIS IS MANDATORY.",
                "instructions": "Additional usage details",
                "difficulty": {level},
                "correct_answer": "Correct Answer",
                "options": ["Option A", "Option B", "Option C", "Option D"], 
                "explanation": "Why this is correct"
                }}
                
                Make sure 'options' are provided if it is a multiple choice question.
                Make sure 'content' contains the actual text the student needs to read or work on.
                """
            else:
                prompt = f"""
                Generate a {exercise_type} exercise for learning {topic}.
                
                Level: {level}/5 (1=Beginner, 5=Advanced)
                
                Return as JSON:
                {{
                "exercise_id": "ex_{uuid.uuid4().hex[:8]}",
                "type": "{exercise_type}",
                "task": "The main instruction",
                "content": "The specific sentence/text to analyze",
                "instructions": "Detailed instructions",
                "difficulty": {level},
                "example": "An example if applicable",
                "correct_answer": "The correct answer",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "explanation": "Why this is correct"
                }}
                """
            
            response = self.llm.invoke(prompt)
            content = response.content
            
            start = content.find("{")
            end = content.rfind("}") + 1
            
            if start >= 0 and end > start:
                data = json.loads(content[start:end])
                
                # If we requested 1 but got a wrapper (edge case), handle it
                if count == 1 and "exercises" in data and isinstance(data["exercises"], list):
                     if len(data["exercises"]) > 0:
                        return data["exercises"][0]
                
                return data
            else:
                return {"error": "JSON parsing failed"}
        
        except Exception as exc:
            return {"error": str(exc)}

    


    def generate_dialogue(
        self,
        topic: str,
        situation: str,
        level: int,
    ) -> Dict:
        """
        Generate a dialogue for practice.

        Args:
            topic: Dialogue topic
            situation: The scenario/situation
            level: Difficulty level

        Returns:
            Dialogue data dictionary
        """
        try:
            prompt = f"""
            Generate a realistic dialogue for {situation}.
            
            Topic: {topic}
            Level: {level}/5
            
            Return as JSON:
            {{
              "dialogue_id": "dial_123",
              "topic": "{topic}",
              "situation": "{situation}",
              "level": {level},
              "lines": [
                {{"speaker": "Person A", "text": "First line", "translation": "Translation"}},
                {{"speaker": "Person B", "text": "Response", "translation": "Translation"}}
              ],
              "key_phrases": ["phrase 1", "phrase 2"],
              "cultural_notes": "Any cultural context"
            }}
            """

            response = self.llm.invoke(prompt)
            content = response.content

            start = content.find("{")
            end = content.rfind("}") + 1

            if start >= 0 and end > start:
                dialogue = json.loads(content[start:end])
                logger.info(f"Generated dialogue for topic '{topic}'")
                return dialogue
            else:
                logger.warning("Could not extract JSON from dialogue generation")
                return {"error": "JSON parsing failed"}

        except Exception as exc:
            logger.error(f"Error generating dialogue: {exc}")
            return {"error": str(exc)}

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
        

        




