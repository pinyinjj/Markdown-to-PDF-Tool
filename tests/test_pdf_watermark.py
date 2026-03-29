import unittest
from pathlib import Path
import sys
import os

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.markdown_processor import md_to_pdf_with_mermaid
from core.pdf_processor import add_watermark_to_file
from core.watermark_utils import generate_text_watermark_image

class TestPDFWatermark(unittest.TestCase):
    def test_add_watermark_to_pdf(self):
        # 1. Create a dummy PDF
        md_file = Path("tests/dummy.md")
        pdf_file = Path("tests/dummy.pdf")
        watermarked_pdf = Path("tests/dummy_watermarked.pdf")
        
        md_file.write_text("# Dummy Document\nContent", encoding="utf-8")
        
        try:
            # Generate PDF
            success = md_to_pdf_with_mermaid(md_file, pdf_file)
            self.assertTrue(success)
            self.assertTrue(pdf_file.exists())
            
            # 2. Generate a watermark image
            watermark_image_path = generate_text_watermark_image("CONFIDENTIAL")
            self.assertIsNotNone(watermark_image_path)
            self.assertTrue(Path(watermark_image_path).exists())
            
            # 3. Add watermark to PDF
            watermark_success = add_watermark_to_file(
                input_file=pdf_file,
                output_file=watermarked_pdf,
                watermark_image=watermark_image_path,
                watermark_type="grid",
                opacity=0.3,
                angle=30
            )
            
            self.assertTrue(watermark_success)
            self.assertTrue(watermarked_pdf.exists())
            self.assertGreater(watermarked_pdf.stat().st_size, 0)
            
        finally:
            # Cleanup
            for f in [md_file, pdf_file, watermarked_pdf]:
                if f.exists():
                    f.unlink()
            if 'watermark_image_path' in locals() and watermark_image_path and Path(watermark_image_path).exists():
                os.remove(watermark_image_path)

if __name__ == '__main__':
    unittest.main()
