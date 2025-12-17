
"""Test Chroma vector database"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.chroma_db import ChromaVectorDB

def test_chroma():
    print("Testing Chroma...")
    
    chroma = ChromaVectorDB("./chroma_data")
    
    
    print("\nAdding test materials...")
    chroma.add_material(
        "greeting_01",
        "Formal greetings: Good morning, Good afternoon. Informal: Hi, Hey.",
        "Greetings",
        {"level": 1}
    )
    
    chroma.add_material(
        "business_01",
        "Business meetings start with agenda. Use 'I propose', 'I agree'.",
        "Business",
        {"level": 3}
    )
    
    
    print("\nSearching materials...")
    results = chroma.search_materials("greeting", limit=5)
    for r in results:
        print(f"- {r['id']}: relevance={r['relevance']:.2f}")
    
    
    print(f"\nTotal materials: {chroma.get_collection_size('lesson_materials')}")
    
    print("\nChroma test passed!")

if __name__ == "__main__":
    test_chroma()
