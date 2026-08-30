import unittest
import sys
import pandas as pd
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.chunk_text import create_chunks

class TestChunkText(unittest.TestCase):
    def test_chunk_creation_and_metadata_preservation(self):
        sample_data = {
            "doc_id": ["doc_001"],
            "file_name": ["sample_doc.pdf"],
            "folder_category": ["engineering"],
            "page_number": [1],
            "total_pages": [5],
            "cleaned_text": ["This is paragraph one.\n\nThis is paragraph two of the sample document."]
        }
        df = pd.DataFrame(sample_data)
        chunks = create_chunks(df)
        
        self.assertGreater(len(chunks), 0)
        first_chunk = chunks[0]
        self.assertEqual(first_chunk["chunk_id"], "doc_001_1_0")
        self.assertEqual(first_chunk["doc_id"], "doc_001")
        self.assertEqual(first_chunk["file_name"], "sample_doc.pdf")
        self.assertEqual(first_chunk["folder_category"], "engineering")
        self.assertEqual(first_chunk["page_number"], 1)
        self.assertEqual(first_chunk["total_pages"], 5)
        self.assertEqual(first_chunk["chunk_index"], 0)

if __name__ == "__main__":
    unittest.main()
