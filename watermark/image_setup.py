"""
Utilities for watermark image discovery, generation, and setup.
"""

import os
from pathlib import Path
from typing import List, Optional
from datetime import date, datetime

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
        r"C:\\Windows\\Fonts\\msyh.ttc",
        r"C:\\Windows\\Fonts\\msyhbd.ttc",
        r"C:\\Windows\\Fonts\\msyhl.ttc",
        r"C:\\Windows\\Fonts\\simhei.ttf",
        r"C:\\Windows\\Fonts\\simsun.ttc",
        r"C:\\Windows\\Fonts\\simkai.ttf",
        r"C:\\Windows\\Fonts\\simfang.ttf",
        r"C:\\Windows\\Fonts\\SourceHanSansCN-Normal.otf",
        r"C:\\Windows\\Fonts\\NotoSansCJK-Regular.ttc",
        r"C:\\Windows\\Fonts\\AlibabaPuHuiTi-2-55-Regular.ttf",
        r"C:\\Windows\\Fonts\\HarmonyOS_Sans_SC_Regular.ttf",
        # macOS
        r"/System/Library/Fonts/PingFang.ttc",
        r"/System/Library/Fonts/Hiragino Sans GB W3.ttc",
        r"/Library/Fonts/Arial Unicode.ttf",
        # Linux common install paths
        r"/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        r"/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        r"/usr/share/fonts/opentype/noto/NotoSansCJKSC-Regular.otf",
    ]


def _search_windows_fonts() -> Optional[str]:
    """Fuzzy search for CJK fonts in the Windows fonts directory."""
    win_fonts = r"C:\\Windows\\Fonts"
    if not os.path.isdir(win_fonts):
        return None

    prefer_keys = [
        "msyh", "simhei", "simsun", "sourcehansans", "notosanscjk",
        "alibabapuhuiti", "harmonyos",
    ]

    try:
        for fname in os.listdir(win_fonts):
            lower = fname.lower()
            if any(k in lower for k in prefer_keys):
                full = os.path.join(win_fonts, fname)
                if os.path.isfile(full):
                    return full
    except Exception:
        pass

    return None


def _find_chinese_font_path() -> Optional[str]:
    """Look for a CJK font via env var and common paths."""
    # 1) Environment variable first
    env_font = os.environ.get("WATERMARK_FONT")
    if env_font and os.path.exists(env_font):
        return env_font

    # 2) Common font candidates
    for font_path in _get_font_candidates():
        if os.path.exists(font_path):
            return font_path

    # 3) Fuzzy search in Windows fonts directory
    return _search_windows_fonts()


def generate_text_watermark_image(text: str, out_path: str, font_size: int = 48, color=(68, 68, 68, 220), padding: int = 20) -> Optional[str]:
    """
    Render text to a transparent PNG image and return the generated path.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except Exception:
        print("✗ " + t('missing_dependency_pillow'))
        return None

    font_path = _find_chinese_font_path()
    if not font_path:
        print("✗ " + t('chinese_font_not_found'))
        return None

    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        print("✗ " + t('open_font_failed', font=font_path, error=str(e)))
        return None

    # Measure text size first
    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    img = Image.new("RGBA", (text_w + padding * 2, text_h + padding * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((padding, padding), text, font=font, fill=color)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(t('text_watermark_image_generated', path=out_path, font=font_path))
    return out_path


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


# ---- New small helpers to simplify setup ----

def _image_from_config(config: dict) -> Optional[str]:
    image = config.get("image")
    if config.get("type") == "image" and image:
        if os.path.exists(image):
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
        color=config.get("text_color", WatermarkConfig.TEXT_COLOR),
        padding=config.get("padding", WatermarkConfig.PADDING)
    )
    return generated or find_watermark_image()


def _setup_watermark_image(config: dict) -> Optional[str]:
    """
    Set up the watermark image, preferring generation from text.
    """
    image = _image_from_config(config)
    if image:
        return image

    watermark_text = _watermark_text_from_config(config)
    if watermark_text:
        return _generate_text_or_fallback(watermark_text, config)

    return find_watermark_image()


