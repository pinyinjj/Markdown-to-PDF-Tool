"""
Utilities for watermark image discovery, generation, and setup.
"""

import os
import platform
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import date, datetime

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None

from i18n import t
from config import WatermarkConfig


def find_watermark_image() -> Optional[str]:
    """
    Select a watermark image (PNG/JPG/SVG) from the `watermarks/` directory.

    Returns:
        Optional[str]: First image file path found, or None if not found
    """
    candidates: List[str] = []
    base = Path("watermarks")
    if not base.exists():
        return None
    exts = ["*.png", "*.PNG", "*.jpg", "*.jpeg", "*.svg"]
    for ext in exts:
        candidates.extend([str(p) for p in base.glob(ext)])
    return candidates[0] if candidates else None


def get_today_str() -> str:
    """Return today's date string in the format YYYY-MM-DD."""
    return date.today().isoformat()


def _get_font_candidates() -> List[str]:
    """Get candidate paths for common CJK fonts."""
    return [
        # Windows common CJK fonts
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\msyhl.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\simkai.ttf",
        r"C:\Windows\Fonts\simfang.ttf",
        r"C:\Windows\Fonts\SourceHanSansCN-Normal.otf",
        r"C:\Windows\Fonts\NotoSansCJK-Regular.ttc",
        r"C:\Windows\Fonts\AlibabaPuHuiTi-2-55-Regular.ttf",
        r"C:\Windows\Fonts\HarmonyOS_Sans_SC_Regular.ttf",
        # macOS
        r"/System/Library/Fonts/PingFang.ttc",
        r"/System/Library/Fonts/Hiragino Sans GB W3.ttc",
        r"/Library/Fonts/Arial Unicode.ttf",
        # Linux common install paths
        r"/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        r"/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        r"/usr/share/fonts/opentype/noto/NotoSansCJKSC-Regular.otf",
        r"/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        r"/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        r"/usr/local/share/fonts/NotoSansCJK-Regular.ttc",
    ]


def _search_windows_fonts() -> Optional[str]:
    """Fuzzy search for CJK fonts in the Windows fonts directory."""
    win_fonts = r"C:\Windows\Fonts"
    if not Path(win_fonts).is_dir():
        return None

    prefer_keys = [
        "msyh", "simhei", "simsun", "sourcehansans", "notosanscjk",
        "alibabapuhuiti", "harmonyos",
    ]

    try:
        for fname in os.listdir(win_fonts):
            lower = fname.lower()
            if any(k in lower for k in prefer_keys):
                full = Path(win_fonts) / fname
                if full.is_file():
                    return str(full)
    except Exception:
        pass

    return None


def find_cjk_font() -> Optional[str]:
    """
    Find a suitable CJK (Chinese, Japanese, Korean) font on the system.
    
    Returns:
        Path to font file, or None if not found.
    """
    # 1) Environment variable first
    env_font = os.environ.get('WATERMARK_FONT')
    if env_font and Path(env_font).exists():
        return env_font
    
    # 2) Common font candidates
    for font_path_str in _get_font_candidates():
        font_path = Path(font_path_str)
        if font_path.exists():
            return str(font_path)
    
    # 3) Fuzzy search in Windows fonts directory
    if platform.system() == 'Windows':
        result = _search_windows_fonts()
        if result:
            return result
    
    # 4) Additional Linux search in common directories
    if platform.system() == 'Linux':
        font_dirs = [
            Path('/usr/share/fonts/truetype'),
            Path('/usr/share/fonts/opentype'),
            Path('/usr/local/share/fonts'),
            Path.home() / '.fonts',
            Path.home() / '.local/share/fonts',
        ]
        for font_dir in font_dirs:
            if font_dir.exists():
                # Search for Noto CJK fonts
                for pattern in ['**/NotoSansCJK*.ttc', '**/NotoSansCJK*.otf', '**/wqy*.ttc']:
                    for font_path in font_dir.glob(pattern):
                        if font_path.is_file():
                            return str(font_path)
    
    return None


def generate_text_watermark_image(
    text: str,
    output_path: str,
    font_size: int = None,
    text_color: tuple = None,
    padding: int = None,
    add_date: bool = False
) -> Optional[str]:
    """
    Generate a watermark image from text.
    
    Args:
        text: Watermark text
        output_path: Path to save the generated image
        font_size: Font size (defaults to WatermarkConfig.FONT_SIZE)
        text_color: Text color as RGBA tuple (defaults to WatermarkConfig.TEXT_COLOR)
        padding: Padding around text (defaults to WatermarkConfig.PADDING)
        add_date: Whether to add current date to the text
    
    Returns:
        Path to generated image, or None if generation failed
    """
    if Image is None:
        print("✗ " + t('missing_dependency_pillow'))
        return None
    
    # Use defaults from config if not provided
    font_size = font_size or WatermarkConfig.FONT_SIZE
    text_color = text_color or WatermarkConfig.TEXT_COLOR
    padding = padding or WatermarkConfig.PADDING
    
    # Add date if requested
    if add_date:
        date_str = datetime.now().strftime('%Y-%m-%d')
        text = f"{text}\n{date_str}"
    
    # Find font
    font_path = find_cjk_font()
    font = None
    
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print("⚠ " + t('open_font_failed', font=font_path, error=str(e)))
    
    # Fallback to default font if CJK font not found or failed to load
    if font is None:
        print("⚠ " + t('chinese_font_not_found'))
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
    
    if font is None:
        print("✗ Failed to load any font")
        return None
    
    # Calculate text size
    try:
        # Create a temporary image to measure text
        temp_img = Image.new('RGBA', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except Exception:
        # Fallback if textbbox is not available (older Pillow)
        try:
            temp_img = Image.new('RGBA', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            text_width, text_height = temp_draw.textsize(text, font=font)
        except Exception:
            # Very old Pillow or no font - use estimates
            text_width = len(text) * font_size
            text_height = font_size
    
    # Create image with padding
    img_width = text_width + padding * 2
    img_height = text_height + padding * 2
    
    # Create transparent image
    img = Image.new('RGBA', (img_width, img_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw text
    try:
        draw.text(
            (padding, padding),
            text,
            fill=text_color,
            font=font
        )
    except Exception as e:
        print(f"✗ Failed to draw text: {e}")
        return None
    
    # Ensure output directory exists
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Save image
    try:
        img.save(output_path, 'PNG')
        print("✓ " + t('text_watermark_image_generated', path=output_path, font=font_path or 'default'))
        return output_path
    except Exception as e:
        print(f"✗ Failed to save watermark image: {e}")
        return None


def _sanitize_filename(value: str) -> str:
    safe = []
    for ch in value:
        if ch.isalnum() or ch in ['_', '-', ' ']:
            safe.append(ch)
        else:
            safe.append('_')
    name = ''.join(safe).strip()
    name = '_'.join(name.split())
    return name[:80] if len(name) > 80 else name


def _image_from_config(config: dict) -> Optional[str]:
    image = config.get("image")
    if config.get("type") == "image" and image:
        if Path(image).exists():
            return image
        print("✗ " + t('image_file_not_found') + f": {image}")
    return None


def _watermark_text_from_config(config: dict) -> Optional[str]:
    if config.get("type") != "text" or not config.get("text"):
        return None
    if config.get("add_date", True):
        return f"{config['text']} - {get_today_str()}"
    return config["text"]


def _output_path_for_text_config(config: dict) -> str:
    base_text_for_filename = _sanitize_filename(config.get("text", "watermark")) or "watermark"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    out_dir = Path("watermarks")
    out_dir.mkdir(parents=True, exist_ok=True)
    return str(out_dir / f"{base_text_for_filename}_{timestamp}.png")


def _generate_text_or_fallback(watermark_text: str, config: dict) -> Optional[str]:
    out_path = _output_path_for_text_config(config)
    generated = generate_text_watermark_image(
        watermark_text,
        out_path,
        font_size=config.get("font_size", WatermarkConfig.FONT_SIZE),
        text_color=config.get("text_color", WatermarkConfig.TEXT_COLOR),
        padding=config.get("padding", WatermarkConfig.PADDING),
        add_date=False  # Date already added in _watermark_text_from_config
    )
    return generated or find_watermark_image()


def setup_watermark_image(config: Dict[str, Any]) -> Optional[str]:
    """
    Setup watermark image based on configuration.
    
    If config type is 'image', returns the image path.
    If config type is 'text', generates a text watermark image and returns its path.
    
    Args:
        config: Configuration dictionary with 'type' key and related settings
    
    Returns:
        Path to watermark image, or None if setup failed
    """
    if not config:
        return None
    
    # Try image from config first
    image = _image_from_config(config)
    if image:
        return image

    # Try text watermark generation
    watermark_text = _watermark_text_from_config(config)
    if watermark_text:
        return _generate_text_or_fallback(watermark_text, config)

    # Fallback to finding existing watermark image
    return find_watermark_image()
