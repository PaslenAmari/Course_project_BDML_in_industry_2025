
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from src.database.chroma_db import ChromaVectorDB
    print("Initializing ChromaVectorDB...")
    db = ChromaVectorDB()
    print("Running health check...")
    if db.health_check():
        print("SUCCESS: ChromaDB is working correctly.")
    else:
        print("FAILURE: Health check returned False.")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
