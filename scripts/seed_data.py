# seed_data.py
"""Seed database with initial data"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.chroma_db import ChromaVectorDB
from src.database.mongodb_adapter import LanguageLearningDB
import config

def seed():
    print("Seeding data...")
    
    # 1. Seed MongoDB (Student)
    mongo = LanguageLearningDB(config.MONGODB_URL)
    students = []
    for i in range(1, 11):
        students.append({
            "student_id": f"student_{i:03d}",
            "name": f"Student {i}",
            "current_level": (i % 3) + 1, # Levels 1, 2, 3
            "target_level": 5, # Target C1
            "target_language": "English", 
            "goals": "Reach C1 proficiency and improve business communication."
        })

    for s in students:
        mongo.create_student(s)
        print(f"Created student: {s['name']} ({s['student_id']})")
    
    # 2. Seed Chroma (Materials for RAG)
    chroma = ChromaVectorDB(config.CHROMA_PERSIST_DIR)
    
    materials = [
        {
            "id": "lesson_greetings",
            "content": "Formal greetings: 'Good morning', 'Good afternoon'. Informal: 'Hi', 'Hey'.",
            "topic": "Greetings",
            "metadata": {"level": 1}
        },
        {
            "id": "lesson_business",
            "content": "Business meetings start with an agenda. Use 'I propose', 'I agree'.",
            "topic": "Business",
            "metadata": {"level": 3}
        }
    ]
    
    for m in materials:
        chroma.add_material(m["id"], m["content"], m["topic"], m["metadata"])
        
    print("Done! Database populated.")

if __name__ == "__main__":
    seed()
