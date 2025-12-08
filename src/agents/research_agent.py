import logging
import os

import numpy as np

from chromadb import PersistentClient
from langgraph.graph import END, START, StateGraph
from openai import OpenAI
from yandex_cloud_ml_sdk import YCloudML

from src.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


"""
Agent state params
Fields:
    language: str ("english", "espanion", "polish", ...)
    topic: str ("travel", "computer science", "food", ...)
    level: str ("a1", "b2", "c1", ...)
    reformatted_query: str
    db_results: list[str]
    final_text: str
"""


class ResearchAgent(BaseAgent):
    def __init__(self, chroma_collection_name: str = "language_books") -> None:
        super().__init__()
        self.chroma_collection = PersistentClient(
            path=os.environ.get("CHROMA_PATH"),
        ).get_or_create_collection(
            chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        self.client = OpenAI(
            api_key=os.environ.get("LITELLM_API_KEY"),
            base_url=os.environ.get("LITELLM_BASE_URL"),
        )
        self.model_name = os.environ.get("MODEL_NAME", "qwen3-32b")

        yandex_folder_id = os.environ.get("YANDEX_FOLDER_ID")
        sdk = YCloudML(
            folder_id=yandex_folder_id,
            auth=os.environ.get("YANDEX_API_KEY"),
        )
        self.doc_embedding_model = sdk.models.text_embeddings(f"emb://{yandex_folder_id}/text-search-doc/latest")


        # graph
        graph = StateGraph(dict)
        graph.add_node("reformat", self.reformat_query)
        graph.add_node("retrieval", self.retrieve_from_db)
        graph.add_node("synthesis", self.synthesize_output)

        # graph.set_entry_point("reformat")
        graph.add_edge(START, "reformat")
        graph.add_edge("reformat", "retrieval")
        graph.add_edge("retrieval", "synthesis")
        graph.add_edge("synthesis", END)

        self.app = graph.compile()

    def reformat_query(self, state: dict) -> dict:
        prompt = (
            "You are a query-optimizer. ",
            "User wants material on a topic. ",

            "Input:"
            f"- Language: {state['language']}\n",
            f"- Level: {state['level']}\n",
            f"- Topic: {state['topic']}\n",

            "Enchance the the query into a clean semantic-search query.\n",
            "Return only the query.\n",
        )

        state["reformatted_query"] = self.invoke_llm(prompt).strip()
        return state

    def retrieve_from_db(self, state: dict) -> dict:
        query = state["reformatted_query"]

        logger.info(f"Searching Chroma with: {query}")
        querry_embedding = np.array(self.doc_embedding_model.run(query))

        # NOTE: use metadata for better search. where={"language": "english"},
        results = self.chroma_collection.query(
            query_embeddings=querry_embedding,
            n_results=10,
        )
        text_results = "\n".join(results["documents"][0])
        state["db_results"] = text_results
        return state

    def synthesize_output(self, state: dict) -> dict:
        retrieved = "\n\n".join(state["db_results"])

        prompt = (
            "You are an educational content generator.",

            f"User level: {state['level']}\n",
            f"Language: {state['language']}\n",
            f"Topic: {state['topic']}\n",
            "Use the retrieved research data below to write **a coherent material text** ",
            "for a learner at the given language level.\n",
            "--- Retrieved Content ---\n"
            f"{retrieved}\n",
            "-------------------------\n\n",

            "Return:\n",
            "- Structured explanation\n",
            "- Examples\n",
            "- Short practice section\n",
            "- Vocabulary list\n",
        )

        state["final_text"] = self.invoke_llm(prompt).strip()
        return state

    def run(self, language: str, topic: str, level: str) -> str:
        initial = {
            "language": language,
            "topic": topic,
            "level": level,
        }

        final_state = self.app.invoke(initial)
        return final_state["final_text"]
