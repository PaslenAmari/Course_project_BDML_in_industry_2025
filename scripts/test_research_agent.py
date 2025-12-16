import sys
import os
import logging


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


logging.basicConfig(level=logging.INFO)

from src.agents.research_agent import ResearchAgent

def test_agent():
    print("Initializing ResearchAgent...")
    try:
        agent = ResearchAgent()
        
        
        topic = "What is lexicology?" 
        language = "English"
        level = "B2"
        
        print(f"Running agent for topic: {topic}...")
        
        initial = {
            "language": language,
            "topic": topic,
            "level": level,
        }
        
        final_state = agent.app.invoke(initial)
        
        print("\n=== RETRIEVAL RESULTS ===")
        print(final_state.get("db_results", "No results found"))
        
        print("\n=== FINAL RESULT ===")
        print(final_state.get("final_text", "No text generated"))
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_agent()
