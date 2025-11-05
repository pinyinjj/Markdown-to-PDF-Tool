#!/usr/bin/env python3
"""
Internationalization support module
Supports English and Chinese languages, automatically selects based on system language
"""

import locale
import os
from typing import Dict, Any

try:
    # Load translations from locales modules to reduce function length
    from locales.en import EN  # type: ignore
    from locales.zh import ZH  # type: ignore
except Exception:
    EN, ZH = {}, {}


class I18n:
    """Internationalization class, manages multi-language support"""
    
    def __init__(self):
        self.current_language = self._detect_system_language()
        self.translations = self._load_translations()
    
    def _detect_system_language(self) -> str:
        """Detect system language"""
        try:
            # Get system language environment
            system_lang = locale.getdefaultlocale()[0]
            if system_lang:
                # Extract language code (e.g., 'zh_CN' -> 'zh')
                lang_code = system_lang.split('_')[0].lower()
                if lang_code in ['zh', 'chinese']:
                    return 'zh'
                elif lang_code in ['en', 'english']:
                    return 'en'
            
            # Check environment variables
            env_lang = os.environ.get('LANG', '').lower()
            if 'zh' in env_lang:
                return 'zh'
            elif 'en' in env_lang:
                return 'en'
                
        except Exception:
            pass
        
        # Default to English
        return 'en'
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translations from locales modules."""
        return {'en': EN, 'zh': ZH}
    
    def t(self, key: str, **kwargs) -> str:
        """Get translated text"""
        text = self.translations.get(self.current_language, {}).get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError):
                return text
        return text
    
    def set_language(self, language: str):
        """Set language"""
        if language in self.translations:
            self.current_language = language
    
    def get_current_language(self) -> str:
        """Get current language"""
        return self.current_language


# Global internationalization instance
i18n = I18n()

# Convenience function
def t(key: str, **kwargs) -> str:
    """Convenience function to get translated text"""
    return i18n.t(key, **kwargs)
