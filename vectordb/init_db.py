import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import torch
import logging

from vectordb.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDBClient:
    """
    Manages the ChromaDB instance, utilizing CUDA for local embeddings.
    """
    def __init__(self, db_path: str = config.active_db_path):
        self.db_path = db_path
        
        # Ensure mandatory GPU acceleration as per rules (cuda:0)
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        if self.device == "cpu":
            logger.warning("CUDA is not available. Falling back to CPU, which violates mandatory GPU requirement if in production!")
            
        logger.info(f"Initializing ChromaDB Client at {self.db_path}")
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        logger.info(f"Loading embedding model: {config.embedding_model} on {self.device}")
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=config.embedding_model,
            device=self.device
        )
        
    def get_or_create_collection(self, collection_name: str = config.collection_name):
        """
        Gets or creates the specified collection.
        """
        logger.info(f"Accessing collection: {collection_name}")
        return self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "Unified Vector DB for BIS Standards"}
        )

    def query_documents(self, query_text: str, n_results: int = 5, filters: dict = None):
        """
        Retrieves the top-k most relevant chunks from the database.
        Includes mandatory metadata pre-filtering capability.
        """
        collection = self.get_or_create_collection()
        logger.info(f"Querying for: '{query_text}' with filters: {filters}")
        
        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=filters  # Metadata pre-filter (e.g., {"status": "Active"})
            )
            return results
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            raise

if __name__ == "__main__":
    # Test initialization and sample optimized retrieval query
    try:
        db = VectorDBClient()
        # Ensure collection is created
        col = db.get_or_create_collection()
        print(f"Collection {col.name} initialized with {col.count()} documents.")
        
        # Example Querying (Optimized Retrieval Query)
        sample_query = "Concrete curing process requirements"
        filter_criteria = {"status": "Active"}
        
        print(f"\nExecuting Sample Query: '{sample_query}'")
        print(f"Filter: {filter_criteria}")
        
        # We wrap in try/except in case it's empty
        res = db.query_documents(query_text=sample_query, n_results=5, filters=filter_criteria)
        print("Query Results Structure:", res)
        
    except Exception as e:
        print(f"Initialization failed: {e}")
