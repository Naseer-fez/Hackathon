"""PDF to clean Markdown extraction using PyMuPDF4LLM on CPU to conserve VRAM."""
from __future__ import annotations
import os
import tempfile
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import pymupdf4llm
from backend.logger.app_logger import get_logger

logger = get_logger("parsers.pdf_markdown_parser")


def _parse_page_chunk(file_path: str, pages: list[int]) -> str:
    """Helper function to parse a chunk of pages in a separate process."""
    try:
        content = pymupdf4llm.to_markdown(file_path, pages=pages)
        return content.strip() if isinstance(content, str) else ""
    except Exception as exc:
        logger.error(f"Failed to parse chunk {pages} of {file_path}: {exc}")
        return ""


def _parse_single_file(file_path: str) -> str:
    """Helper function to parse a single file in a separate process."""
    try:
        content = pymupdf4llm.to_markdown(file_path)
        return content.strip() if isinstance(content, str) else ""
    except Exception as exc:
        logger.error(f"Failed to parse {file_path}: {exc}")
        return ""


class PdfMarkdownParser:
    """Extracts clean Markdown text from PDF using PyMuPDF4LLM on CPU."""

    def extract_markdown_from_bytes(self, pdf_bytes: bytes) -> str:
        """Parse PDF byte stream into markdown without consuming VRAM."""
        if not pdf_bytes:
            return ""

        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(pdf_bytes)
                temp_path = tmp_file.name

            logger.info("Extracting markdown with PyMuPDF4LLM from temporary PDF...")
            markdown_content = pymupdf4llm.to_markdown(temp_path)
            return markdown_content.strip() if isinstance(markdown_content, str) else ""
        except (OSError, RuntimeError, ValueError) as exc:
            logger.error(f"Failed to extract markdown from PDF ({type(exc).__name__}: {exc})")
            return ""
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def extract_markdown_from_path(self, file_path: str) -> str:
        """Parse PDF file directly from filesystem path into clean markdown."""
        if not os.path.isfile(file_path):
            logger.warning(f"PDF file does not exist: {file_path}")
            return ""
        try:
            markdown_content = pymupdf4llm.to_markdown(file_path)
            return markdown_content.strip() if isinstance(markdown_content, str) else ""
        except (OSError, RuntimeError, ValueError) as exc:
            logger.error(f"Failed to parse PDF file at {file_path} ({type(exc).__name__}: {exc})")
            return ""

    def batch_extract_markdown_from_paths(self, file_paths: list[str]) -> dict[str, str]:
        """Process multiple PDF files concurrently using multiprocessing."""
        results: dict[str, str] = {}
        if not file_paths:
            return results

        max_workers = max(1, multiprocessing.cpu_count() - 1)
        logger.info(f"Batch processing {len(file_paths)} PDFs with {max_workers} workers...")
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(_parse_single_file, path): path for path in file_paths if os.path.isfile(path)
            }
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    results[path] = future.result()
                except Exception as exc:
                    logger.error(f"Batch extraction failed for {path}: {exc}")
                    results[path] = ""
                    
        return results

    def parallel_extract_from_large_pdf(self, file_path: str, chunk_size: int = 10) -> str:
        """Chunk a large PDF by pages and parse chunks in parallel on CPU."""
        if not os.path.isfile(file_path):
            logger.warning(f"PDF file does not exist: {file_path}")
            return ""
            
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            total_pages = doc.page_count
            doc.close()
        except Exception as exc:
            logger.warning(f"Failed to get page count with fitz, falling back to sequential: {exc}")
            return self.extract_markdown_from_path(file_path)

        if total_pages <= chunk_size:
            return self.extract_markdown_from_path(file_path)

        page_chunks = [list(range(i, min(i + chunk_size, total_pages))) for i in range(0, total_pages, chunk_size)]
        max_workers = max(1, multiprocessing.cpu_count() - 1)
        logger.info(f"Parsing {total_pages} pages in {len(page_chunks)} chunks with {max_workers} workers...")

        chunk_results: dict[int, str] = {}
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(_parse_page_chunk, file_path, chunk): idx
                for idx, chunk in enumerate(page_chunks)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    chunk_results[idx] = future.result()
                except Exception as exc:
                    logger.error(f"Chunk extraction failed for {file_path} at index {idx}: {exc}")
                    chunk_results[idx] = ""

        # Reassemble chunks in order
        ordered_texts = [chunk_results.get(i, "") for i in range(len(page_chunks))]
        return "\n\n".join(filter(None, ordered_texts))
