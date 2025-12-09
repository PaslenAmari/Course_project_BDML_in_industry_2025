import logging
import json
import os
from typing import Dict, Any, List

from src.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class TheoryAgent(BaseAgent):
    """
    Agent responsible specifically for generating theoretical content
    (lessons, grammar explanations, cultural notes) based on the syllabus.
    Uses ResearchAgent to find relevant materials if possible.
    """

    def __init__(self):
        super().__init__()
        self.research_agent = None
        try:
            from src.agents.research_agent import ResearchAgent
            self.research_agent = ResearchAgent()
            logger.info("ResearchAgent linked to TheoryAgent successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize ResearchAgent for TheoryAgent: {e}. strictly using internal LLM knowledge.")

        logger.info("TheoryAgent initialized")

    def generate_theory(self, topic: str, week: int, level: str, language: str) -> Dict[str, Any]:
        """
        Generates a markdown-formatted theory lesson.
        """
        research_material = ""
        
        if self.research_agent:
            try:
                logger.info(f"Researching topic: {topic}")
                research_material = self.research_agent.run(language=language, topic=topic, level=str(level))
                logger.info("Research completed successfully.")
            except Exception as e:
                logger.error(f"ResearchAgent failed during run: {e}")
                research_material = ""

        if self.llm is None:
            logger.warning("No LLM, returning mock theory.")
            return {
                "type": "theory",
                "title": f"Mock Lesson: {topic}",
                "topic": topic,
                "content": f"## Introduction\nThis is a mock lesson about **{topic}** for Week {week}.\n\n## Rules\n1. Rule A\n2. Rule B",
                "key_points": ["Mock Point 1", "Mock Point 2"]
            }

        context_block = ""
        if research_material:
            context_block = f"""
Additional Research Material (Use this to enrich the lesson):
---
{research_material}
---
"""

        prompt = f"""
You are an expert language teacher specializing in creating clear, engaging educational content.

Task: Create a theoretical lesson for a student interacting with a language learning app.

Context:
- Target Language: {language}
- Student Level: {level} (CEFR)
- Current Week: {week}
- Main Topic: {topic}
{context_block}

Requirements:
1. **Title**: Catchy and relevant.
2. **Content**: 
   - Use Markdown formatting.
   - Explain the concept clearly (grammar, vocabulary, or culture).
   - Provide examples in {language} with English translations.
   - Keep it concise but comprehensive enough for {level} level.
   - If research material is provided, strictly use it to verify facts or provide examples, but structure it as a clean lesson.
3. **Key Takeaways**: A list of 2-4 crucial points to remember.

Return strictly valid JSON in this format:
{{
  "type": "theory",
  "title": "Lesson Title",
  "topic": "{topic}",
  "content": "Markdown string here...",
  "key_points": ["Point 1", "Point 2", "Point 3"]
}}
"""
        try:
            response = self.llm.invoke(prompt).content
            clean_res = response.strip()
            
            if "```json" in clean_res:
                clean_res = clean_res.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_res:
                clean_res = clean_res.split("```")[1].split("```")[0].strip()
            
            start = clean_res.find("{")
            end = clean_res.rfind("}") + 1
            if start != -1 and end != 0:
                clean_res = clean_res[start:end]
            
            return json.loads(clean_res)

        except Exception as e:
            logger.error(f"Error generating theory: {e}")
            return {
                "type": "theory",
                "error": str(e),
                "title": "Error generating lesson",
                "content": "Please try again.",
                "key_points": []
            }
