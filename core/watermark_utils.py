"""
Utilities for watermark image discovery, generation, and setup.
"""

import os
import platform
from pathlib import Path
import tempfile
import shutil # Added for shutil.move
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
    Select a watermark image (PNG/JPG/SVG) from the `watermarks/` or `assets/` directory.

    Returns:
        Optional[str]: First image file path found, or None if not found
    """
    candidates: List[str] = []
    # Check both user watermarks dir and system assets dir
    search_dirs = [Path("watermarks"), Path("assets")]
    
    exts = ["*.png", "*.PNG", "*.jpg", "*.jpeg", "*.svg"]
    
    for base in search_dirs:
        if not base.exists():
            continue
        for ext in exts:
            # Add found images to candidates
            found = list(base.glob(ext))
            candidates.extend([str(p) for p in found])
            
    return candidates[0] if candidates else None


def get_today_str() -> str:
    """Return today's date string in the format YYYY-MM-DD."""
    return date.today().isoformat()


def _get_local_font_candidates() -> List[str]:
    """
    Search for fonts in local assets directory (project root/assets).
    This allows for self-contained execution (e.g. in Docker) without installing system fonts.
    """
    candidates = []
    # Check paths relative to CWD and script location
    possible_roots = [
        Path("assets"), 
        Path(__file__).parent.parent / "assets"
    ]
    
    checked_paths = set()
    
    for root in possible_roots:
        if not root.exists():
            continue
            
        # Search in assets/ and assets/fonts/
        search_dirs = [root, root / "fonts"]
        
        for d in search_dirs:
            resolved_d = d.resolve()
            if not d.exists() or resolved_d in checked_paths:
                continue
            
            checked_paths.add(resolved_d)
            
            # Look for font files
            for ext in ["*.ttc", "*.ttf", "*.otf"]:
                for font_path in d.glob(ext):
                    # Skip KaTeX fonts (math symbols) as they aren't suitable for general text
                    if "KaTeX" in font_path.name:
                        continue
                    candidates.append(str(font_path.resolve()))
                    
    return candidates


def find_cjk_font() -> Optional[str]:
    """
    Find a suitable CJK (Chinese, Japanese, Korean) font in the local 'assets' directory.
    It prioritizes Simplified Chinese fonts to prevent garbled text issues.
    """
    candidates = _get_local_font_candidates()
    
    # Prioritize Simplified Chinese fonts to ensure correct character rendering
    # Switch the order to test the mono font first
    preferred_fonts = ['NotoSansMonoCJKsc-VF.otf', 'NotoSansSC-Regular.otf']
    
    for font_name in preferred_fonts:
        for candidate_path in candidates:
            if font_name in candidate_path:
                return candidate_path

    # If no preferred font is found, return the first available one as a fallback
    if candidates:
        return candidates[0]
        
    return None


def generate_text_watermark_image(
    text: str,
    font_size: int = None,
    text_color: tuple = None,
    padding: int = None,
    add_date: bool = False
) -> Optional[str]:
    """
    Generate a watermark image from text into a temporary file.
    
    Args:
        text: Watermark text
        font_size: Font size (defaults to WatermarkConfig.FONT_SIZE)
        text_color: Text color as RGBA tuple (defaults to WatermarkConfig.TEXT_COLOR)
        padding: Padding around text (defaults to WatermarkConfig.PADDING)
        add_date: Whether to add current date to the text
    
    Returns:
        Path to generated temporary image, or None if generation failed
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
    
    
    # Save image to a temporary file
    try:
        # Use a temporary file to store the generated watermark image
        temp_dir = Path("/home/yj/.gemini/tmp/c2327b82b93ac09a25e74aba6385271e48c34b57ad6a55827b04d6cf72c865e7") # Using project temp directory
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png", dir=temp_dir)
        temp_output_path = temp_file.name
        temp_file.close() # Close the file handle as img.save will open it again

        img.save(temp_output_path, 'PNG')
        print("✓ " + t('text_watermark_image_generated', path=temp_output_path, font=font_path or 'default'))
        return temp_output_path
    except Exception as e:
        print(f"✗ Failed to save temporary watermark image: {type(e).__name__} - {e}")
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
    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)
    return str(out_dir / f"{base_text_for_filename}_{timestamp}.png")


def _generate_text_or_fallback(watermark_text: str, config: dict, save_to_output: bool) -> Optional[str]:
    generated_temp_path = generate_text_watermark_image(
        watermark_text,
        font_size=config.get("font_size", WatermarkConfig.FONT_SIZE),
        text_color=config.get("text_color", WatermarkConfig.TEXT_COLOR),
        padding=config.get("padding", WatermarkConfig.PADDING),
        add_date=False  # Date already added in _watermark_text_from_config
    )
    
    if generated_temp_path and save_to_output:
        final_output_path = _output_path_for_text_config(config)
        try:
            shutil.move(generated_temp_path, final_output_path)
            return final_output_path
        except Exception as e:
            print(f"✗ Failed to move temporary watermark to final output: {e}")
            # Ensure temporary file is removed if move fails
            if Path(generated_temp_path).exists():
                os.remove(generated_temp_path)
            return None
    elif generated_temp_path:
        return generated_temp_path
        
    return find_watermark_image()


def setup_watermark_image(config: Dict[str, Any], save_to_output: bool = False) -> Optional[str]:
    """
    Setup watermark image based on configuration.
    
    If config type is 'image', returns the image path.
    If config type is 'text', generates a text watermark image and returns its path.
    
    Args:
        config: Configuration dictionary with 'type' key and related settings
        save_to_output: If True, and a text watermark is generated, it will be saved
                        to the 'output' directory. Otherwise, a temporary file path is returned.
    
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
        return _generate_text_or_fallback(watermark_text, config, save_to_output)

    # Fallback to finding existing watermark image
    return find_watermark_image()
