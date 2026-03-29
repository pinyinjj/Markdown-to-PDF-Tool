import unittest
import asyncio
from pathlib import Path
import sys
import os

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.markdown_processor import md_to_pdf_with_mermaid

class TestPDFConversion(unittest.TestCase):
    def test_md_to_pdf_conversion(self):
        # Create a simple markdown file
        md_file = Path("tests/simple.md")
        pdf_file = Path("tests/simple.pdf")
        
        content = """# Test Document
This is a test document with **bold text** and a list:
- Item 1
- Item 2
"""
        md_file.write_text(content, encoding="utf-8")
        
        try:
            # Convert to PDF
            success = md_to_pdf_with_mermaid(md_file, pdf_file)
            
            self.assertTrue(success)
            self.assertTrue(pdf_file.exists())
            self.assertGreater(pdf_file.stat().st_size, 0)
        finally:
            # Cleanup
            if md_file.exists():
                md_file.unlink()
            if pdf_file.exists():
                pdf_file.unlink()

    def test_mermaid_rendering(self):
        # Mermaid rendering is hard to verify automatically but we can check if it finishes
        md_file = Path("tests/mermaid_test.md")
        pdf_file = Path("tests/mermaid_test.pdf")
        
        content = """# Mermaid Diagram
```mermaid
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
```
"""
        md_file.write_text(content, encoding="utf-8")
        
        try:
            success = md_to_pdf_with_mermaid(md_file, pdf_file)
            self.assertTrue(success)
            self.assertTrue(pdf_file.exists())
        finally:
            if md_file.exists():
                md_file.unlink()
            if pdf_file.exists():
                pdf_file.unlink()

if __name__ == '__main__':
    unittest.main()
