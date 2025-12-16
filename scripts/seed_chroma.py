import sys
import os
import uuid


sys.path.append(os.getcwd())

from src.database.chroma_db import ChromaVectorDB

def seed_database():
    print("Initializing ChromaDB...")
    db = ChromaVectorDB(persist_dir="./chroma_data")
    
    initial_materials = [
        {
            "topic": "Present Simple",
            "content": """
# Present Simple Tense

The Present Simple is the most basic tense in English. We use it for:
1. **Habits and Routines**: "I wake up at 7 AM."
2. **General Truths**: "The sun rises in the east."
3. **Permanent Situations**: "She lives in New York."

**Structure:**
- Positive: Subject + Verb (s/es for he/she/it)
  - "I play tennis."
  - "He plays tennis."
- Negative: Subject + do/does not + Verb
  - "I do not play."
  - "He does not play."
- Question: Do/Does + Subject + Verb?
  - "Do you play?"
  - "Does he play?"
            """,
            "level": "A1",
            "language": "English"
        },
        {
            "topic": "Past Simple",
            "content": """
# Past Simple Tense

We use the Past Simple for finished actions in the past.

**Regular Verbs**: Add -ed
- Walk -> Walked
- Play -> Played

**Irregular Verbs** (Must be memorized):
- Go -> Went
- See -> Saw
- Buy -> Bought

**Time Markers**: yesterday, last week, in 2010, two days ago.

Example: "I went to the park yesterday."
            """,
            "level": "A2",
            "language": "English"
        },
        {
            "topic": "Greetings and Introductions",
            "content": """
# Greetings and Introductions

**Formal Greetings:**
- "Good morning / afternoon / evening."
- "How do you do?" (Very formal)

**Informal Greetings:**
- "Hi!", "Hello!"
- "How are you?" -> "I'm fine, thanks. And you?"
- "What's up?" (Very informal)

**Introductions:**
- "My name is..."
- "Nice to meet you."
            """,
            "level": "A1",
            "language": "English"
        },
        {
            "topic": "Present Continuous",
            "content": """
# Present Continuous

We use Present Continuous for actions happening **right now**.

**Structure**: Subject + am/is/are + Verb-ing

Examples:
- "I am reading a book now."
- "She is cooking dinner."
- "They are playing football."

**Spelling Rules**:
- run -> running (double consonant)
- write -> writing (drop 'e')
            """,
            "level": "A1",
            "language": "English"
        }
    ]

    print(f"Seeding {len(initial_materials)} materials...")

    for material in initial_materials:
        doc_id = str(uuid.uuid4())
        success = db.add_material(
            doc_id=doc_id,
            content=material["content"],
            topic=material["topic"],
            metadata={
                "level": material["level"],
                "language": material["language"],
                "type": "theory_base"
            }
        )
        if success:
            print(f"Added: {material['topic']}")
        else:
            print(f"Failed to add: {material['topic']}")

    count = db.get_collection_size("lesson_materials")
    print(f"\nTotal documents in DB: {count}")

if __name__ == "__main__":
    seed_database()
