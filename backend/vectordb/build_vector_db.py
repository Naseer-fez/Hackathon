"""CLI entrypoint to initialize, index, and query the BIS Vector Database."""
from __future__ import annotations

import argparse
import sys
import time
from backend.vectordb.config import vector_db_settings
from backend.vectordb.indexer import VectorDbIndexer
from backend.vectordb.search_service import search_standards

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run_indexing(recreate: bool = False, limit: int | None = None) -> int:
    """Run Vector DB indexing workflow and return total indexed records."""
    print("=" * 70)
    print("INDIAN STANDARDS (BIS) KNOWLEDGE BASE - VECTOR DB BUILDER")
    print(f"Target DB Path: {vector_db_settings.db_path}")
    print(f"Embedding Model: {vector_db_settings.embedding_model_name}")
    print("=" * 70)

    start_time = time.time()
    indexer = VectorDbIndexer()
    total = indexer.index_all(recreate=recreate, limit=limit)
    elapsed = time.time() - start_time
    print(f"\n[OK] Successfully indexed {total} standards into ChromaDB in {elapsed:.2f}s.")
    return total


def execute_query(query: str, mandatory: bool | None = None, top_k: int = 3) -> None:
    """Search and display results for a single query."""
    print(f"\nQuery: '{query}' | Mandatory Only: {mandatory}")
    results = search_standards(query_text=query, status_filter="Active", mandatory_only=mandatory, top_k=top_k)
    for rank, res in enumerate(results, 1):
        print(f"  #{rank} [{res['similarity_score']:.4f}] {res['standard_id']} - {res['product_category']}")
        print(f"      Mandatory: {res['mandatory']} | Scheme: {res['bis_scheme']} | QCO: {res['qco_order_title']}")


def run_sample_queries() -> None:
    """Execute sample semantic queries demonstrating hybrid search and filtering."""
    print("\n" + "=" * 70 + "\nDEMONSTRATION OF HYBRID SEMANTIC SEARCH\n" + "=" * 70)
    samples = [
        ("TMT Sariya Fe 500D ductile rebars for RCC", True),
        ("1.1 kV XLPE insulated armoured aluminium power cable A2XFY", None),
        ("HDPE pipe SDR 11 PN 16 for potable water supply Jal Jeevan Mission", True),
        ("साधारण पोर्टलैंड सीमेंट 53 ग्रेड", None),
    ]
    for q, m in samples:
        execute_query(q, m)


def main() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(description="BIS Vector Database Builder & Query Engine")
    parser.add_argument("--recreate", action="store_true", help="Recreate Chroma collection from scratch")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of standards indexed")
    parser.add_argument("--query", type=str, default=None, help="Execute a custom search query")
    parser.add_argument("--mandatory", action="store_true", default=None, help="Filter to mandatory QCO standards only")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    args = parser.parse_args()

    if args.query:
        execute_query(args.query, mandatory=args.mandatory, top_k=args.top_k)
    else:
        if not args.query:
            run_sample_queries()


if __name__ == "__main__":
    main()
