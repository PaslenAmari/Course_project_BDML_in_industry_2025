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
    """Base class for all agents in the language learning system."""

    def __init__(self):
        """Initialize base agent with LLM client from env config."""
        try:
            self.llm = get_llm()
            logger.info("BaseAgent LLM initialized via get_llm()")
        except Exception as exc:
            logger.error(f"Failed to initialize LLM: {exc}")
            raise

    def invoke_llm(self, prompt: str) -> str:
        """Send a prompt to the LLM and get response."""
        response = self.llm.invoke(prompt)
        return response.content
