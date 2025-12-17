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


PROJECT_ROOT = Path(__file__).resolve().parent
LOGS_DIR = PROJECT_ROOT / "logs"
CHROMA_PERSIST_DIR = PROJECT_ROOT / "chroma_data"


LOGS_DIR.mkdir(exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(exist_ok=True)


MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")  
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "")
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "")


YANDEX_DISK_TOKEN = os.getenv("YANDEX_DISK_TOKEN", "")


MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "app.log"


API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_DEBUG = os.getenv("API_DEBUG", "False").lower() == "true"


if not LITELLM_API_KEY:
    import logging
    logging.warning("LITELLM_API_KEY not set. LLM features will fail.")
