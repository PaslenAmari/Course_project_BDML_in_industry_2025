"""
Configuration for Language Learning System.

Environment variables:
- LITELLM_API_KEY: API key for LLM (OpenAI, Claude, etc.)
- LITELLM_BASE_URL: Base URL for LLM API (optional)
- MONGODB_URL: MongoDB connection string
- CHROMA_PERSIST_DIR: Path for Chroma persistent storage
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
LOGS_DIR = PROJECT_ROOT / "logs"
CHROMA_PERSIST_DIR = PROJECT_ROOT / "chroma_data"

# Create directories if they don't exist
LOGS_DIR.mkdir(exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(exist_ok=True)

# LLM Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")  # Default to OpenAI
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "")
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "")

# Database Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "app.log"

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_DEBUG = os.getenv("API_DEBUG", "False").lower() == "true"

# Validation
if not LITELLM_API_KEY:
    import logging
    logging.warning("LITELLM_API_KEY not set. LLM features will fail.")
