"""
Centralized configuration for watermark and defaults.
"""


class WatermarkConfig:
    """Watermark-related configuration constants"""
    # Whether to automatically generate image watermark from text
    GENERATE_IMAGE_FROM_TEXT = True

    # Generated text watermark image filename
    TEXT_WATERMARK_FILE = "watermarks/text_watermark.png"

    # Text watermark generation parameters
    FONT_SIZE = 36
    TEXT_COLOR = (68, 68, 68, 220)
    PADDING = 20

    # PDF watermark parameters
    WATERMARK_TYPE = "grid"
    OPACITY = 0.2
    ANGLE = 45
    IMAGE_SCALE = 1.0
    HORIZONTAL_BOXES = 3
    VERTICAL_BOXES = 6


# Backward compatibility constants
GENERATE_IMAGE_FROM_TEXT = WatermarkConfig.GENERATE_IMAGE_FROM_TEXT
TEXT_WATERMARK_FILE = WatermarkConfig.TEXT_WATERMARK_FILE


