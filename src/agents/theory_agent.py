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
            from src.database.chroma_db import ChromaVectorDB
            
            self.research_agent = ResearchAgent()
            self.db = ChromaVectorDB(persist_dir="./chroma_data") 
            
            logger.info("ResearchAgent and ChromaDB linked to TheoryAgent.")
        except Exception as e:
            logger.warning(f"Could not initialize dependencies for TheoryAgent: {e}")
            self.db = None

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
            
            logger.warning("No LLM, forcing fallback.")
            
            
            return self._fallback_generation(topic, week, level, language, "No LLM available")

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
   - Provide examples in {language}. {'If ' + language + ' != "English", provide English translations.' if language != "English" else 'Do NOT provide translations if teaching English.'}
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
            
            result_json = json.loads(clean_res)
            
            
            if self.db and "content" in result_json:
                self._auto_save_to_db(result_json, topic, level, language)
            
            return result_json

        except Exception as e:
            logger.error(f"Error generating theory with LLM: {e}")
            return self._fallback_generation(topic, week, level, language, str(e))

    def _auto_save_to_db(self, result_json, topic, level, language):
        import uuid
        try:
            doc_id = str(uuid.uuid4())
            self.db.add_material(
                doc_id=doc_id,
                content=result_json["content"],
                topic=topic,
                metadata={
                    "level": level,
                    "language": language,
                    "type": "generated_theory",
                    "source": "TheoryAgent"
                }
            )
            logger.info(f"Auto-saved generated theory to ChromaDB: {doc_id}")
        except Exception as save_err:
            logger.error(f"Failed to auto-save to ChromaDB: {save_err}")

    def _fallback_generation(self, topic, week, level, language, error_msg):
        """
        Fallback sequence:
        1. Check ChromaDB (which now internally checks Yandex Disk if needed).
        2. Return error if all fail.
        """
        logger.info(f"Initiating fallback for topic: {topic}. Error was: {error_msg}")
        
        
        if self.db:
            try:
                
                results = self.db.search_materials(
                    query=topic,
                    limit=1
                )
                
                if results and results[0]:
                    best_match = results[0]
                    logger.info("Found fallback content (DB or Yandex Disk).")
                    
                    content = best_match.get("content", "")
                    source = best_match.get("metadata", {}).get("source", "db_cache")
                    
                    return {
                        "type": "theory",
                        "title": f"Lesson: {topic} ({source})",
                        "topic": topic,
                        "content": content,
                        "key_points": ["Content retrieved from backup storage."]
                    }
            except Exception as db_err:
                logger.error(f"Database/Fallback search failed: {db_err}")

        
        return {
            "type": "theory",
            "error": error_msg,
            "title": "Error generating lesson",
            "content": f"Could not generate lesson due to error: {error_msg}. \n\nFallback storage search returned no results.",
            "key_points": []
        }
