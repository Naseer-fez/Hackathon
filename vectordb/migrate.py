import os
import json
import uuid
import logging
import re
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from chromadb.api.models.Collection import Collection

from vectordb.config import config
from vectordb.init_db import VectorDBClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_legacy_database(legacy_db_path: str, final_collection: Collection):
    """
    Extracts documents, embeddings, and metadata from an old ChromaDB 
    and upserts them into the final collection.
    """
    logger.info(f"Starting migration from legacy DB: {legacy_db_path}")
    if not os.path.exists(legacy_db_path):
        logger.warning(f"Legacy DB path {legacy_db_path} does not exist. Skipping.")
        return

    try:
        from chromadb import PersistentClient
        legacy_client = PersistentClient(path=legacy_db_path)
        # Assuming the old collections were also named similarly or we iterate through them
        collections = legacy_client.list_collections()
        
        for col in collections:
            logger.info(f"Extracting data from old collection: {col.name}")
            old_data = col.get(include=["documents", "metadatas", "embeddings"])
            
            ids = old_data.get("ids", [])
            docs = old_data.get("documents", [])
            metadatas = old_data.get("metadatas", [])
            embeddings = old_data.get("embeddings", [])
            
            if not ids:
                continue
                
            batch_size = 500
            for i in range(0, len(ids), batch_size):
                final_collection.upsert(
                    ids=ids[i:i+batch_size],
                    documents=docs[i:i+batch_size] if docs else None,
                    metadatas=metadatas[i:i+batch_size] if metadatas else None,
                    embeddings=embeddings[i:i+batch_size] if embeddings else None
                )
            logger.info(f"Migrated {len(ids)} records from {col.name}")
            
    except Exception as e:
        logger.error(f"Error migrating {legacy_db_path}: {e}")
        raise


def extract_hierarchical_chunks(pdf_path: str) -> List[Dict[str, str]]:
    """
    Reads a PDF and chunks it while attempting to maintain clause hierarchy.
    """
    chunks = []
    if not os.path.exists(pdf_path):
        logger.warning(f"PDF not found: {pdf_path}")
        return chunks

    try:
        doc = fitz.open(pdf_path)
        current_clause = "General"
        current_text = []
        
        # Regex to detect clause headings (e.g., "1 SCOPE", "2.1 Test Methods")
        clause_pattern = re.compile(r"^(\d+(\.\d+)*)\s+([A-Z].+)$")

        for page in doc:
            text = page.get_text("text")
            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                
                match = clause_pattern.match(line)
                if match:
                    # Save previous chunk
                    if current_text:
                        chunks.append({
                            "clause": current_clause,
                            "text": " ".join(current_text)
                        })
                        current_text = []
                    current_clause = match.group(1) + " " + match.group(3)
                else:
                    current_text.append(line)
                    
        # Add final chunk
        if current_text:
            chunks.append({
                "clause": current_clause,
                "text": " ".join(current_text)
            })
            
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {e}")
        
    return chunks


def ingest_new_dataset(final_collection: Collection):
    """
    Reads the new scraped BIS dataset, chunks the PDFs, and upserts them.
    """
    json_path = os.path.join(config.bis_data_path, "bis_scraped_amendments.json")
    pdf_dir = os.path.join(config.bis_data_path, "downloads")
    
    logger.info(f"Ingesting new dataset from: {json_path}")
    if not os.path.exists(json_path):
        logger.warning(f"JSON data not found: {json_path}. Skipping new dataset ingestion.")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            metadata_records = json.load(f)
            
        for record in metadata_records:
            is_code = record.get("is_code", "Unknown")
            pdf_filename = record.get("pdf_filename") # Assume JSON holds the filename
            
            if not pdf_filename:
                pdf_filename = f"{is_code.replace(':', '_')}.pdf"
                
            pdf_path = os.path.join(pdf_dir, pdf_filename)
            chunks = extract_hierarchical_chunks(pdf_path)
            
            if not chunks:
                continue

            ids = []
            docs = []
            metadatas = []

            for i, chunk in enumerate(chunks):
                chunk_id = f"{is_code}_chunk_{i}_{uuid.uuid4().hex[:6]}"
                ids.append(chunk_id)
                docs.append(chunk["text"])
                
                # Attach all mandatory metadata
                meta = {
                    "is_code": is_code,
                    "standard_year": str(record.get("standard_year", "")),
                    "status": record.get("status", "Unknown"),
                    "amendment_number": str(record.get("amendment_number", "")),
                    "document_type": record.get("document_type", "Standard"),
                    "clause_hierarchy": chunk["clause"]
                }
                metadatas.append(meta)
                
            # Add to collection
            logger.info(f"Adding {len(ids)} chunks for {is_code}")
            final_collection.add(
                ids=ids,
                documents=docs,
                metadatas=metadatas
            )

    except Exception as e:
        logger.error(f"Error ingesting new dataset: {e}")
        raise

def run_migration():
    """
    Main migration pipeline.
    """
    db_client = VectorDBClient()
    final_col = db_client.get_or_create_collection()
    
    # 1. Migrate Old Database 1
    migrate_legacy_database(config.old_db_1_path, final_col)
    
    # 2. Migrate Old Database 2
    migrate_legacy_database(config.old_db_2_path, final_col)
    
    # 3. Ingest New Scraped BIS Dataset
    ingest_new_dataset(final_col)
    
    logger.info(f"Migration completed successfully. Total documents in Final DB: {final_col.count()}")

if __name__ == "__main__":
    run_migration()
