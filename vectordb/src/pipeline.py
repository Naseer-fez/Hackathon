import logging
import os
import time
import pandas as pd
from pathlib import Path
from .config import DATASET_PATH, PROCESSED_DIR, BATCH_SIZE
from .load_data import load_dataset
from .clean_text import process_dataframe_text
from .chunk_text import create_chunks
from .embeddings import EmbeddingService
from .vector_store import VectorStore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def run_pipeline(source_csv_path: str = DATASET_PATH) -> dict:
    """
    Executes the complete document-to-vector pipeline:
    1. Load raw CSV data and validate structure
    2. Clean extracted text conservatively
    3. Save processed artifacts to data/processed/
    4. Chunk document pages preserving document-level metadata
    5. Generate sentence embeddings
    6. Upsert vectors into persistent ChromaDB
    """
    start_time = time.time()
    logger.info("=== Starting Document-to-Vector Pipeline ===")
    
    if not os.path.exists(source_csv_path):
        raise FileNotFoundError(f"Source dataset not found at: {source_csv_path}")
        
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # 1. Load Data
    logger.info("Loading CSV...")
    df = load_dataset(source_csv_path)
    total_raw_rows = len(df)
    total_unique_docs = df['doc_id'].nunique()
    logger.info(f"Rows loaded: {total_raw_rows} across {total_unique_docs} unique documents")
    
    # 2. Clean Text
    logger.info("Cleaning text...")
    df_cleaned = process_dataframe_text(df)
    valid_records = len(df_cleaned)
    logger.info(f"Valid records: {valid_records}")
    
    # Save cleaned documents to processed directory (preserving source data integrity)
    cleaned_file_path = PROCESSED_DIR / "cleaned_documents.csv"
    logger.info(f"Saving cleaned dataset to {cleaned_file_path}...")
    df_cleaned.to_csv(cleaned_file_path, index=False, encoding="utf-8")
    
    # 3. Create Chunks
    logger.info("Creating chunks...")
    chunks = create_chunks(df_cleaned)
    total_chunks = len(chunks)
    logger.info(f"Chunks created: {total_chunks}")
    
    # Save chunks dataframe for auditing/debugging
    chunks_df = pd.DataFrame(chunks)
    chunks_file_path = PROCESSED_DIR / "chunks.csv"
    logger.info(f"Saving chunks to {chunks_file_path}...")
    chunks_df.to_csv(chunks_file_path, index=False, encoding="utf-8")
    
    # Calculate average chunk length
    avg_chunk_chars = chunks_df['text'].str.len().mean() if not chunks_df.empty else 0
    avg_chunk_words = chunks_df['text'].apply(lambda x: len(x.split())).mean() if not chunks_df.empty else 0
    
    # 4. Initialize Embedding Model
    logger.info("Loading embedding model...")
    embedding_service = EmbeddingService()
    
    # 5. Initialize Vector Store and Ingest
    logger.info("Writing to Chroma...")
    vector_store = VectorStore()
    vector_store.store_chunks(chunks, embedding_service, batch_size=BATCH_SIZE)
    
    elapsed_time = time.time() - start_time
    logger.info(f"=== Pipeline completed successfully in {elapsed_time:.2f}s ===")
    
    summary = {
        "dataset_rows": total_raw_rows,
        "unique_documents": total_unique_docs,
        "valid_cleaned_rows": valid_records,
        "total_chunks": total_chunks,
        "vectors_stored": vector_store.collection.count(),
        "embedding_model": embedding_service.model_name if hasattr(embedding_service, 'model_name') else "BAAI/bge-small-en-v1.5",
        "embedding_dimension": embedding_service.dimension,
        "chroma_collection": vector_store.collection_name,
        "chroma_path": str(vector_store.chroma_dir),
        "avg_chunk_chars": round(avg_chunk_chars, 2),
        "avg_chunk_words": round(avg_chunk_words, 2),
        "processing_time_seconds": round(elapsed_time, 2)
    }
    return summary

if __name__ == "__main__":
    run_pipeline()
