import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_NAME = os.getenv("MONGODB_NAME", "language_learning")

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://localhost:34000/v1")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "dummy-key")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3-32b")