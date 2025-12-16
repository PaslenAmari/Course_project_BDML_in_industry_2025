import os
import sys


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.chroma_db import ChromaVectorDB

def ingest_book(file_path):
    print(f"Reading {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        
    
    chunk_size = 1000
    overlap = 100
    
    chunks = []
    ids = []
    metadatas = []
    
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    
    safe_base = "".join(c if c.isalnum() else "_" for c in base_name).lower()
    
    print("Chunking text...")
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i : i + chunk_size]
        if len(chunk) < 50:  
            continue
            
        chunks.append(chunk)
        chunk_id = f"{safe_base}_part_{len(chunks)}"
        ids.append(chunk_id)
        
        metadatas.append({
            "source": os.path.basename(file_path),
            "chunk_index": len(chunks)
        })

    print(f"Created {len(chunks)} chunks.")
    
    print("Initializing Database...")
    db = ChromaVectorDB()
    
    print(f"Adding to 'textbooks' collection...")
    
    batch_size = 100
    total_added = 0
    
    for i in range(0, len(chunks), batch_size):
        batch_end = min(i + batch_size, len(chunks))
        
        db.textbooks.add(
            documents=chunks[i:batch_end],
            ids=ids[i:batch_end],
            metadatas=metadatas[i:batch_end]
        )
        total_added += (batch_end - i)
        print(f"Added batch {i} to {batch_end} (Total: {total_added})")
    
    print("Ingestion complete!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        
        file_path = sys.argv[1]
    else:
        
        file_path = os.path.join(os.path.dirname(__file__), "..", "data", "books", "Specific_English.txt")
    
    file_path = os.path.abspath(file_path)
    ingest_book(file_path)
