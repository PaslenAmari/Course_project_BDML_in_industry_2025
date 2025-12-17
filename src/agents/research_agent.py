import logging
import os

from langgraph.graph import END, START, StateGraph
from openai import OpenAI

from src.agents.base_agent import BaseAgent
from src.database.chroma_db import ChromaVectorDB

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
    def __init__(self) -> None:
        super().__init__()
        
        self.db = ChromaVectorDB()
        
        self.client = OpenAI(
            api_key=os.environ.get("LITELLM_API_KEY", "sk-mock-key"),
            base_url=os.environ.get("LITELLM_BASE_URL"),
        )
        self.model_name = os.environ.get("MODEL_NAME", "qwen3-32b")

        
        graph = StateGraph(dict)
        graph.add_node("reformat", self.reformat_query)
        graph.add_node("retrieval", self.retrieve_from_db)
        graph.add_node("synthesis", self.synthesize_output)

        graph.add_edge(START, "reformat")
        graph.add_edge("reformat", "retrieval")
        graph.add_edge("retrieval", "synthesis")
        graph.add_edge("synthesis", END)

        self.app = graph.compile()

    def reformat_query(self, state: dict) -> dict:
        
        
        q = f"{state['topic']} for {state['language']} learners level {state['level']}"
        state["reformatted_query"] = q
        return state

    def retrieve_from_db(self, state: dict) -> dict:
        query = state["reformatted_query"]
        logger.info(f"Searching Textbooks with: {query}")

        try:
            
            results = self.db.textbooks.query(
                query_texts=[query],
                n_results=5,
            )
            
            if results and results["documents"] and results["documents"][0]:
                text_results = "\n\n".join(results["documents"][0])
                state["db_results"] = text_results
                logger.info("Retrieved context from textbooks.")
            else:
                 state["db_results"] = "No specific textbook material found."
                 logger.info("No context found in textbooks.")
                 
        except Exception as e:
            logger.error(f"Error retrieving from textbooks: {e}")
            state["db_results"] = "Error retrieving textbook material."

        return state

    def synthesize_output(self, state: dict) -> dict:
        retrieved = state["db_results"]

        prompt = (
            "You are an educational content generator.",
            f"User level: {state['level']}\n",
            f"Language: {state['language']}\n",
            f"Topic: {state['topic']}\n",
            "Use the retrieved textbook material below to write **a coherent theoretical lesson**.",
            "If the retrieved material is relevant, base your explanation strictly on it.",
            "If it is not relevant, rely on your general knowledge but mention that no textbook source was found.\n",
            "--- Retrieved Textbook Content ---\n",
            f"{retrieved}\n",
            "-------------------------\n\n",
            "Return a markdown response with:\n",
            "- Title\n",
            "- Clear Explanation\n",
            "- Examples\n",
            "- Key Takeaways\n",
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
