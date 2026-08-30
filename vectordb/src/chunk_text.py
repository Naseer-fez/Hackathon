import pandas as pd
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)

def create_chunks(df: pd.DataFrame) -> list:
    """Splits cleaned text into semantic chunks while preserving metadata."""
    logger.info("Creating chunks...")
    
    # We use roughly 1 character ~ 0.25 tokens, so a chunk_size of 500 tokens is ~2000 characters.
    # But for safety, we'll configure it based on characters, since text_splitter operates on characters.
    # Let's say 1 token = 4 characters approximately.
    char_chunk_size = CHUNK_SIZE * 4
    char_chunk_overlap = CHUNK_OVERLAP * 4
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=char_chunk_size,
        chunk_overlap=char_chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
        length_function=len,
    )
    
    chunks = []
    
    for _, row in df.iterrows():
        text = row['cleaned_text']
        doc_id = row['doc_id']
        file_name = row['file_name']
        folder_category = row['folder_category']
        page_number = row['page_number']
        total_pages = row['total_pages']
        
        # Split text
        splits = text_splitter.split_text(text)
        
        for idx, split in enumerate(splits):
            chunk_id = f"{doc_id}_{page_number}_{idx}"
            chunks.append({
                "chunk_id": chunk_id,
                "text": split,
                "doc_id": doc_id,
                "file_name": file_name,
                "folder_category": folder_category,
                "page_number": page_number,
                "total_pages": total_pages,
                "chunk_index": idx
            })
            
    logger.info(f"Chunks created: {len(chunks)}")
    return chunks
