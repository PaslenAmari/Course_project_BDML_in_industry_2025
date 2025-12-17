
import os
from langchain_openai import ChatOpenAI
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


SRC_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
ENV_PATH = os.path.join(SRC_DIR, ".env")
load_dotenv(ENV_PATH) 

def get_llm(mock: bool | None = None):
    api_key = os.getenv("LITELLM_API_KEY", "")
    base_url = os.getenv("LITELLM_BASE_URL", "http://a6k2.dgx:34000/v1")
    model = os.getenv("MODEL_NAME", "qwen3-32b")

    if mock is True or len(api_key) < 5:
        logger.warning("LLM running in MOCK mode (no real API calls).")
        return None

    logger.info(f"Loaded API key: '{api_key[:10]}...' (length: {len(api_key)})")

    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=0.7,
    )
print(f"LITELLM_API_KEY length: {len(os.getenv('LITELLM_API_KEY', ''))}")
