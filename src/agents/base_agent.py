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


# class BaseAgent:
#     """Base class for all agents in the language learning system."""

#     def __init__(self):
#         """Initialize base agent with LLM client from env config."""
#         try:
#             self.llm = get_llm()
#             logger.info("BaseAgent LLM initialized via get_llm()")
#         except Exception as exc:
#             logger.error(f"Failed to initialize LLM: {exc}")
#             raise

#         def invoke_llm(self, prompt: str) -> str:
#             if self.llm is None:
#                 # MOCK-ответ
#                 return "MOCK_LLM_RESPONSE"
#             resp = self.llm.invoke(prompt)
#             return resp.content

class BaseAgent:
    def __init__(self, *args, **kwargs):
        self.llm = get_llm()  # может вернуть None в mock-режиме
        if self.llm is None:
            logger.warning("BaseAgent initialized in MOCK mode (no real LLM).")
        else:
            logger.info("BaseAgent initialized with real LLM client.")

    def invoke_llm(self, prompt: str) -> str:
        """Единая точка вызова LLM с поддержкой mock-режима."""
        if self.llm is None:
            logger.warning("invoke_llm in MOCK mode, returning dummy JSON.")
            # безопасный дефолт, чтобы json.loads не падал
            return '{"outline": ["Warmup", "Content", "Practice", "Review"], "estimated_total_minutes": 50}'
        resp = self.llm.invoke(prompt)
        return resp.content