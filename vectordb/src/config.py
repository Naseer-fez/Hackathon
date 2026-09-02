import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = DATA_DIR / "chroma"

# Source dataset
DATASET_PATH = Path(os.getenv("EXTRACTED_DOCUMENTS_DATASET", str(DATA_DIR / "extracted_documents.csv")))

# ChromaDB Settings
COLLECTION_NAME = "document_chunks"

# Embedding Settings
# Model: all-MiniLM-L6-v2
# - Embedding Dimension: 384
# - Why selected: State-of-the-art balance between semantic search accuracy and fast local CPU inference.
# - Memory requirements: ~200-300MB RAM.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunking Settings
CHUNK_SIZE = 500      # Tokens target per chunk (approx 2000 characters)
CHUNK_OVERLAP = 100   # Token overlap between chunks (approx 400 characters)

# Processing Settings
BATCH_SIZE = 32       # Batch size optimized for stable memory usage during embedding

# Search Settings
TOP_K = 5
