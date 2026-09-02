"""Hinglish transliteration and translation dataset ingestion helper.

Indexes key transliteration and translation pairs into Chroma/VectorDB
so that the local 2B model can use few-shot retrieval for accurate Hinglish-to-English translation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from backend.config.paths import PROJECT_ROOT, VECTORDB_DIR
from backend.logger.app_logger import get_logger
from backend.vectordb.embedding_function import SentenceTransformerEmbeddingFunction

logger = get_logger("ingestion.hinglish_helper")

DATASET_FILE = PROJECT_ROOT / "backend" / "data" / "datasets" / "hinglish_transliterate" / "merged_attempt_2.jsonl"
DEFAULT_COLLECTION_NAME = "hinglish_few_shot_pairs"


class HinglishTransliterationIndexer:
    """Helper to extract and index high-quality transliteration/translation pairs for few-shot prompting."""

    def __init__(
        self,
        chroma_path: str | Path | None = None,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        embedding_model_path: str | None = None,
    ) -> None:
        self.db_path = str(chroma_path or (VECTORDB_DIR / "hinglish"))
        Path(self.db_path).mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self._client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False),
        )
        self._embed_fn = SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_path
        )

    def get_or_create_collection(self, recreate: bool = False):
        if recreate:
            try:
                self._client.delete_collection(self.collection_name)
            except Exception:
                pass
        return self._client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def index_dataset(
        self,
        dataset_path: str | Path | None = None,
        max_samples: int = 1500,
        batch_size: int = 128,
        recreate: bool = False,
    ) -> int:
        """Ingest transliteration pairs from jsonl into ChromaDB."""
        path = Path(dataset_path or DATASET_FILE)
        if not path.exists():
            logger.error(f"Dataset file not found: {path}")
            return 0

        collection = self.get_or_create_collection(recreate=recreate)
        current_count = collection.count()
        if current_count >= max_samples and not recreate:
            logger.info(f"Collection '{self.collection_name}' already has {current_count} items. Skipping re-indexing.")
            return current_count

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        total_indexed = 0

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f):
                if idx >= max_samples:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    orig_prompt = data.get("original_prompt", "")
                    prompt_lines = [l.strip() for l in orig_prompt.split("\n") if l.strip()]
                    hindi_text = prompt_lines[-1] if prompt_lines else ""
                    hinglish_text = (
                        data.get("enhanced_completion")
                        or data.get("original_completion")
                        or ""
                    ).strip()

                    if not hinglish_text:
                        continue

                    # Text for vector similarity retrieval: Hinglish representation and raw Hindi
                    doc_repr = f"Hinglish: {hinglish_text}\nHindi: {hindi_text}"
                    chunk_id = f"hinglish_pair_{idx}"

                    ids.append(chunk_id)
                    documents.append(doc_repr)
                    metadatas.append({
                        "hindi_text": hindi_text[:500],
                        "hinglish_text": hinglish_text[:500],
                        "sample_index": idx,
                    })

                    if len(ids) >= batch_size:
                        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
                        total_indexed += len(ids)
                        ids, documents, metadatas = [], [], []
                except Exception as exc:
                    logger.debug(f"Failed parsing line {idx}: {exc}")

        if ids:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            total_indexed += len(ids)

        logger.info(f"Successfully indexed {total_indexed} Hinglish pairs into '{self.collection_name}'.")
        return total_indexed

    def retrieve_few_shot_examples(self, query: str, top_k: int = 3) -> list[dict[str, str]]:
        """Retrieve top_k closest transliteration pairs for few-shot prompting."""
        collection = self.get_or_create_collection(recreate=False)
        if collection.count() == 0:
            return []
        try:
            results = collection.query(query_texts=[query], n_results=top_k)
            metadatas = results.get("metadatas", [[]])[0]
            examples = []
            for meta in metadatas:
                examples.append({
                    "hinglish": str(meta.get("hinglish_text", "")),
                    "hindi": str(meta.get("hindi_text", "")),
                })
            return examples
        except Exception as exc:
            logger.warning(f"Few-shot retrieval failed ({type(exc).__name__}): {exc}")
            return []


def index_hinglish_data() -> int:
    indexer = HinglishTransliterationIndexer()
    return indexer.index_dataset(max_samples=1500)


if __name__ == "__main__":
    count = index_hinglish_data()
    print(f"Total Hinglish pairs indexed: {count}")
