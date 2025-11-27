import os
from langchain_openai import ChatOpenAI


def get_llm():
    """
    Create LLM client using environment variables.
    
    - LITELLM_BASE_URL: e.g. http://a6k2.dgx:34000/v1
    - LITELLM_API_KEY: dummy or real key (если сервер его игнорирует — можно пустой)
    - MODEL_NAME: e.g. qwen2.5-32b
    """
    base_url = os.getenv("LITELLM_BASE_URL", "http://a6k2.dgx:34000/v1")
    api_key = os.getenv("LITELLM_API_KEY", "dummy-key")
    model = os.getenv("MODEL_NAME", "qwen2.5-32b")

    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=0.7,
    )
