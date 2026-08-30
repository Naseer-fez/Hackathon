import logging
import gc
from typing import List
import numpy as np
from .config import EMBEDDING_MODEL

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Embedding service supporting both SentenceTransformers and Chroma ONNX models.
    Operates 100% locally and offline without external API requirements.
    Optimized for low-memory footprint and stability.
    """
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self.engine = None
        self.dimension = 384
        
        logger.info(f"Initializing EmbeddingService with model: '{self.model_name}'...")
        
        # 1. Attempt using ONNXMiniLM / DefaultEmbeddingFunction for all-MiniLM-L6-v2
        if "minilm" in self.model_name.lower():
            try:
                import chromadb.utils.embedding_functions as ef
                self.engine = ef.DefaultEmbeddingFunction()
                # Warm-up to verify dimension
                test_emb = self.engine(["warmup test"])
                self.dimension = len(test_emb[0])
                logger.info(f"Initialized high-performance ONNX embedding engine. Dimension: {self.dimension}")
                return
            except Exception as e:
                logger.warning(f"Chroma ONNX embedding function initialization notice: {e}. Falling back to SentenceTransformer.")

        # 2. Attempt using SentenceTransformer
        try:
            from sentence_transformers import SentenceTransformer
            self.st_model = SentenceTransformer(self.model_name)
            self.dimension = self.st_model.get_sentence_embedding_dimension()
            self.engine = "sentence_transformers"
            logger.info(f"Initialized SentenceTransformer '{self.model_name}'. Dimension: {self.dimension}")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer directly ({e}). Falling back to ONNX embedding function.")
            import chromadb.utils.embedding_functions as ef
            self.engine = ef.DefaultEmbeddingFunction()
            test_emb = self.engine(["warmup test"])
            self.dimension = len(test_emb[0])
            self.model_name = "all-MiniLM-L6-v2 (ONNX)"

    def embed_batch(self, texts: List[str], mini_batch_size: int = 16) -> List[List[float]]:
        """
        Generates dense vector embeddings for a list of text strings.
        Processes in small sub-batches to prevent memory spikes, and normalizes vectors.
        """
        if not texts:
            return []
            
        all_embeddings = []
        
        for i in range(0, len(texts), mini_batch_size):
            chunk = texts[i:i + mini_batch_size]
            
            if hasattr(self, 'st_model') and self.engine == "sentence_transformers":
                emb = self.st_model.encode(
                    chunk,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                all_embeddings.extend(emb.tolist())
            else:
                # Chroma ONNX Embedding Function
                raw_emb = self.engine(chunk)
                for item in raw_emb:
                    arr = np.array(item, dtype=np.float32)
                    norm = np.linalg.norm(arr)
                    if norm > 0:
                        arr = arr / norm
                    all_embeddings.append(arr.tolist())
                    
        # Periodic garbage collection for memory management
        gc.collect()
        return all_embeddings
