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
#                 # MOCK_RESPONSE
#                 return "MOCK_LLM_RESPONSE"
#             resp = self.llm.invoke(prompt)
#             return resp.content

class BaseAgent:
    def __init__(self, *args, **kwargs):
        self.llm = get_llm()  # can return None in mock mode
        if self.llm is None:
            logger.warning("BaseAgent initialized in MOCK mode (no real LLM).")
        else:
            logger.info("BaseAgent initialized with real LLM client.")

    def invoke_llm(self, prompt: str) -> str:
        """Single entry point for LLM calls with mock mode support."""
        if self.llm is None:
            logger.warning("invoke_llm in MOCK mode, returning dummy JSON.")
            # safe default to avoid json.loads crash
            return '{"outline": ["Warmup", "Content", "Practice", "Review"], "estimated_total_minutes": 50}'
        resp = self.llm.invoke(prompt)
        return resp.content