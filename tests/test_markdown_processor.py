import unittest
from pathlib import Path
import sys
import os

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.markdown_processor import remove_docsy_front_matter, extract_h1_title

class TestMarkdownProcessor(unittest.TestCase):
    def test_remove_docsy_front_matter(self):
        md_content = """---
title: "Test Title"
linkTitle: "Test"
weight: 10
---
# Actual Content
Hello world"""
        # Since content already has an H1 (# Actual Content), it should just return the content
        expected = "# Actual Content\nHello world"
        result = remove_docsy_front_matter(md_content)
        self.assertEqual(result.strip(), expected.strip())

    def test_remove_docsy_front_matter_no_h1(self):
        md_content = """---
title: "Only Title"
---
Just some text."""
        expected = "# Only Title\n\nJust some text."
        result = remove_docsy_front_matter(md_content)
        self.assertEqual(result.strip(), expected.strip())

    def test_extract_h1_title(self):
        # Create a temporary markdown file
        test_file = Path("tests/temp_test.md")
        test_file.write_text("# My Awesome Title\nSome content", encoding="utf-8")
        
        try:
            title = extract_h1_title(test_file)
            self.assertEqual(title, "My Awesome Title")
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_extract_h1_title_from_front_matter(self):
        test_file = Path("tests/temp_front.md")
        test_file.write_text('---\ntitle: "Front Matter Title"\n---\nSome content', encoding="utf-8")
        
        try:
            title = extract_h1_title(test_file)
            self.assertEqual(title, "Front Matter Title")
        finally:
            if test_file.exists():
                test_file.unlink()

if __name__ == '__main__':
    unittest.main()
