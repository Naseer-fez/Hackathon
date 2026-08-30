import sys
import os
import argparse
from pathlib import Path

# Ensure UTF-8 output handling on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import TOP_K
from src.search import DocumentSearcher

def display_results(results: list, query: str):
    print("\n" + "=" * 50)
    print(f"Search Query: {query}")
    print(f"Total Results: {len(results)}")
    print("=" * 50)
    
    if not results:
        print("No matching documents found.")
        return
        
    for res in results:
        print(f"\n==================================================")
        print(f"Result #{res['rank']}")
        print(f"Score: {res['score']:.4f} (Distance: {res['distance']:.4f})")
        print(f"File: {res['file_name']}")
        print(f"Page: {res['page_number']} of {res['total_pages']}")
        print(f"Category: {res['folder_category']}")
        print(f"Document ID: {res['doc_id']}")
        print(f"Chunk ID: {res['chunk_id']}")
        print(f"\nText:\n{res['text']}")
        print("==================================================")

def main():
    parser = argparse.ArgumentParser(description="Query the document vector database.")
    parser.add_argument("--query", "-q", type=str, help="Search query to run in non-interactive mode")
    parser.add_argument("--top_k", "-k", type=int, default=TOP_K, help="Number of results to return")
    parser.add_argument("--category", "-c", type=str, default=None, help="Filter by folder category")
    args = parser.parse_args()

    print("Initializing Document Searcher...")
    searcher = DocumentSearcher()

    if args.query:
        # Direct CLI execution
        results = searcher.search(args.query, top_k=args.top_k, category_filter=args.category)
        display_results(results, args.query)
        return

    # Interactive mode
    print("\n" + "#" * 60)
    print("  Document Vector Database - Interactive Search")
    print("  Type your query and press Enter.")
    print("  Type 'exit' or 'q' to quit.")
    print("#" * 60 + "\n")

    while True:
        try:
            query = input("Query> ").strip()
            if not query:
                continue
            if query.lower() in ["q", "quit", "exit"]:
                print("Exiting search. Goodbye!")
                break
                
            results = searcher.search(query, top_k=args.top_k, category_filter=args.category)
            display_results(results, query)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting search. Goodbye!")
            break
        except Exception as e:
            print(f"Error during search: {e}")

if __name__ == "__main__":
    main()
