import unittest
import asyncio
from pathlib import Path
import sys
import os
import shutil

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.markdown_processor import md_to_pdf_with_mermaid

class TestMDWithImages(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("tests/img_test_job")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.output_pdf = Path("tests/img_test_output.pdf")

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        if self.output_pdf.exists():
            self.output_pdf.unlink()

    def test_markdown_with_local_image(self):
        # 1. Create a dummy image (just a small colored block)
        from PIL import Image
        img_path = self.test_dir / "test_image.png"
        img = Image.new('RGB', (100, 100), color = 'red')
        img.save(img_path)
        
        # 2. Create markdown referencing this image
        md_path = self.test_dir / "test_with_img.md"
        content = """# Document with Image
Here is a local image:
![Test Image](test_image.png)
"""
        md_path.write_text(content, encoding="utf-8")
        
        # 3. Convert to PDF
        # We run it from the job directory to simulate the 'markdown_with_images' mode behavior
        success = md_to_pdf_with_mermaid(md_path, self.output_pdf)
        
        self.assertTrue(success)
        self.assertTrue(self.output_pdf.exists())
        self.assertGreater(self.output_pdf.stat().st_size, 0)

    def test_markdown_with_image_in_subfolder(self):
        # 1. Create subfolder and image
        sub_dir = self.test_dir / "images"
        sub_dir.mkdir()
        img_path = sub_dir / "sub_image.png"
        from PIL import Image
        img = Image.new('RGB', (100, 100), color = 'blue')
        img.save(img_path)
        
        # 2. Create markdown referencing image in subfolder
        md_path = self.test_dir / "test_subfolder.md"
        content = """# Subfolder Image Test
![Blue Image](images/sub_image.png)
"""
        md_path.write_text(content, encoding="utf-8")
        
        # 3. Convert
        success = md_to_pdf_with_mermaid(md_path, self.output_pdf)
        
        self.assertTrue(success)
        self.assertTrue(self.output_pdf.exists())

if __name__ == '__main__':
    unittest.main()
