import sys
from pathlib import Path
import pandas as pd
import chromadb

# Ensure UTF-8 output handling on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import COLLECTION_NAME, CHROMA_DIR

def inspect():
    print("\n" + "=" * 60)
    print("           CHROMADB DATABASE INSPECTION REPORT           ")
    print("=" * 60)
    print(f"Database Directory : {CHROMA_DIR}")
    print(f"Collection Name    : {COLLECTION_NAME}")
    
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"\n[ERROR] Unable to connect to collection '{COLLECTION_NAME}': {e}")
        return

    total_vectors = collection.count()
    print(f"Total Stored Vectors: {total_vectors}")
    
    if total_vectors == 0:
        print("\n[WARNING] Database collection is empty. Run build_database.py first.")
        return

    # Fetch sample record to inspect schema and embedding dimension
    sample = collection.peek(limit=1)
    
    print("\n--- SAMPLE VECTOR METADATA ---")
    if sample and sample.get('metadatas') and len(sample['metadatas']) > 0:
        sample_meta = sample['metadatas'][0]
        for k, v in sample_meta.items():
            print(f"  {k:16}: {v}")
    
    print("\n--- SAMPLE CHUNK TEXT ---")
    if sample and sample.get('documents') and len(sample['documents']) > 0:
        sample_text = sample['documents'][0]
        preview = sample_text[:300] + "..." if len(sample_text) > 300 else sample_text
        print(f"  ID: {sample['ids'][0]}")
        print(f"  Length: {len(sample_text)} characters")
        print(f"  Content:\n{preview}")

    # Fetch all metadatas to compute comprehensive distribution stats
    print("\n--- DATASET DISTRIBUTION & STATISTICS ---")
    all_records = collection.get(include=['metadatas'])
    metadatas = all_records.get('metadatas', [])
    
    if metadatas:
        df_meta = pd.DataFrame(metadatas)
        unique_docs = df_meta['doc_id'].nunique() if 'doc_id' in df_meta.columns else 0
        unique_files = df_meta['file_name'].nunique() if 'file_name' in df_meta.columns else 0
        
        print(f"Unique Documents (doc_id)    : {unique_docs}")
        print(f"Unique Files (file_name)     : {unique_files}")
        print(f"Total Chunks Indexed         : {len(df_meta)}")
        
        if 'folder_category' in df_meta.columns:
            print("\nFolder Category Distribution:")
            cat_counts = df_meta['folder_category'].value_counts()
            for cat, count in cat_counts.items():
                percentage = (count / len(df_meta)) * 100
                print(f"  - {cat:25}: {count:5d} chunks ({percentage:5.1f}%)")
                
        if 'page_number' in df_meta.columns:
            print(f"\nPage Number Range: {df_meta['page_number'].min()} to {df_meta['page_number'].max()}")
            
    print("\n" + "=" * 60)
    print("Database inspection complete and verified.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    inspect()
