import unittest
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.clean_text import clean_text

class TestCleanText(unittest.TestCase):
    def test_whitespace_normalization(self):
        raw = "This   is   a    test   sentence."
        expected = "This is a test sentence."
        self.assertEqual(clean_text(raw), expected)

    def test_line_break_reduction(self):
        raw = "Line 1\n\n\n\n\nLine 2"
        expected = "Line 1\n\nLine 2"
        self.assertEqual(clean_text(raw), expected)

    def test_ocr_spacing_fix(self):
        raw = "The f l o w of the process."
        expected = "The flow of the process."
        self.assertEqual(clean_text(raw), expected)

    def test_control_character_removal(self):
        raw = "Valid text\x00\x08with control\x1f chars"
        expected = "Valid textwith control chars"
        self.assertEqual(clean_text(raw), expected)

    def test_empty_input(self):
        self.assertEqual(clean_text(""), "")
        self.assertEqual(clean_text(None), "")
        self.assertEqual(clean_text("   \n\t  "), "")

if __name__ == "__main__":
    unittest.main()
