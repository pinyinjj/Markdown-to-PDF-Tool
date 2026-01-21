"""
Watermark service module for setting up watermark images.
"""

from typing import Optional
from watermark.image_setup import _setup_watermark_image as _setup_watermark_image_impl


def setup_watermark_image(config: dict) -> Optional[str]:
    """
    Set up the watermark image based on configuration.
    
    Args:
        config: Configuration dictionary with watermark settings
        
    Returns:
        Optional[str]: Path to watermark image, or None if not found
    """
    return _setup_watermark_image_impl(config)
