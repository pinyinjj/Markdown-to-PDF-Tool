import unittest
from pathlib import Path
import sys
import os

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.watermark_utils import generate_text_watermark_image, setup_watermark_image

class TestWatermarkUtils(unittest.TestCase):
    def test_generate_text_watermark_image(self):
        # Test basic text watermark generation
        text = "Confidential"
        path = generate_text_watermark_image(text)
        
        self.assertIsNotNone(path)
        self.assertTrue(Path(path).exists())
        self.assertTrue(path.endswith(".png"))
        
        # Cleanup
        if Path(path).exists():
            os.remove(path)

    def test_setup_watermark_image_text(self):
        config = {
            "type": "text",
            "text": "Draft",
            "add_date": False
        }
        path = setup_watermark_image(config)
        
        self.assertIsNotNone(path)
        self.assertTrue(Path(path).exists())
        
        # Cleanup
        if Path(path).exists():
            os.remove(path)

    def test_setup_watermark_image_fallback(self):
        # Should fallback to finding an existing watermark if config is empty or invalid
        path = setup_watermark_image({})
        # This might be None if no watermarks/ or assets/ images exist, 
        # but in this repo there are assets.
        # Let's check if it returns something.
        self.assertTrue(path is None or Path(path).exists())

if __name__ == '__main__':
    unittest.main()
