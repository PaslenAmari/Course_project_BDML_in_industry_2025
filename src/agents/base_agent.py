"""
Base Agent class for all language learning agents.

Provides common functionality:
- LLM initialization and interaction
- Logging setup
- Error handling
"""

import logging
from src.utils.llm import get_llm

logger = logging.getLogger(__name__)





















class BaseAgent:
    def __init__(self, *args, **kwargs):
        self.llm = get_llm()  
        if self.llm is None:
            logger.warning("BaseAgent initialized in MOCK mode (no real LLM).")
        else:
            logger.info("BaseAgent initialized with real LLM client.")

    def invoke_llm(self, prompt: str) -> str:
        """Single entry point for LLM calls with mock mode support."""
        if self.llm is None:
            logger.warning("invoke_llm in MOCK mode, returning dummy JSON.")
            
            return '{"outline": ["Warmup", "Content", "Practice", "Review"], "estimated_total_minutes": 50}'
        resp = self.llm.invoke(prompt)
        return resp.content