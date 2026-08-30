# Document-to-Vector Pipeline

This project processes extracted document text from a CSV file, cleans it, chunks it, embeds it using a local Sentence Transformers model, and stores the vectors in a local ChromaDB database. It is designed to support high-quality semantic document retrieval.

## Data Source
**Input Dataset:** `D:\CODE\Hackathon__test\data\extracted_documents.csv`
**Database Location:** `D:\CODE\Hackathon\vectordb\data\chroma`

## Architecture Highlights
- **Embedding Model**: `BAAI/bge-small-en-v1.5` (Fast, locally-run, excellent retrieval performance).
- **Chunking Strategy**: Langchain `RecursiveCharacterTextSplitter`. Chunks text into ~500 tokens with 100-token overlaps, splitting on paragraph and sentence boundaries for semantic integrity.
- **Metadata**: Retains source document IDs, filenames, categories, and page numbers at the chunk level.

## Installation

1. Open PowerShell and navigate to the project directory:
```powershell
cd D:\CODE\Hackathon\vectordb
```

2. Create a virtual environment:
```powershell
python -m venv .venv
```

3. Activate the virtual environment:
```powershell
.venv\Scripts\activate
```

4. Install dependencies:
```powershell
pip install -r requirements.txt
```

## Usage

### 1. Build the Vector Database
To process the CSV and build the ChromaDB database, run:
```powershell
python scripts/build_database.py
```
This script handles safe upserts; rerunning it will update existing chunks instead of creating duplicates.

### 2. Inspect the Database
To view statistics about the stored vectors (e.g. total vectors, unique documents, category distribution):
```powershell
python scripts/inspect_database.py
```

### 3. Query the Database
To perform semantic searches interactively:
```powershell
python scripts/query_database.py
```

## Troubleshooting
- **Memory Errors during embedding**: Reduce `BATCH_SIZE` in `src/config.py`.
- **Duplicate Records**: The pipeline generates deterministic chunk IDs (`{doc_id}_{page_number}_{chunk_index}`). Rerunning the build script will safely upsert.
