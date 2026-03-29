import unittest
from pathlib import Path
import sys
import os

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from i18n import t

class TestI18n(unittest.TestCase):
    def test_translation_exists(self):
        # This assumes at least 'app_title' exists in both en and zh
        title_en = t('app_title', lang='en')
        title_zh = t('app_title', lang='zh')
        
        self.assertIsNotNone(title_en)
        self.assertIsNotNone(title_zh)
        self.assertNotEqual(title_en, 'app_title') # Should not return the key if it's found
        self.assertNotEqual(title_zh, 'app_title')

    def test_translation_with_variables(self):
        # Test processing_successful_detail which takes src and dst
        msg = t('processing_successful_detail', src='file.md', dst='file.pdf', lang='en')
        self.assertIn('file.md', msg)
        self.assertIn('file.pdf', msg)

if __name__ == '__main__':
    unittest.main()
