#!/usr/bin/env python3
"""
PDF Watermark Tool
Add watermarks to all PDF files in the input directory and output to the output directory, keeping original files unchanged.
Also supports converting Markdown(.md) files in the input directory to Mermaid-supported PDF and output to the output directory.
"""

import os
import subprocess
import sys
import argparse
from pathlib import Path
from typing import List, Optional
from datetime import date, datetime

# Import internationalization support
from i18n import t, i18n

# ========= Configuration Constants =========

# Watermark configuration
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


def get_user_input() -> dict:
    """
    Get user input for watermark configuration.
    
    Returns:
        dict: User configuration dictionary
    """
    while True:
        print(t('app_title'))
        print("=" * 50)
        print(t('select_operation_mode'))
        print()
        
        config = {}
        
        # Operation mode selection
        print(t('operation_mode_title'))
        print(f"   [1] {t('process_pdf_with_watermark')}")
        print(f"   [2] {t('convert_md_to_pdf_with_watermark')}")
        print(f"   [3] {t('generate_watermark_only')}")
        print(f"   [4] {t('convert_md_to_pdf_no_watermark')}")
        print(f"   [0] {t('exit_program')}")
        
        while True:
            choice = input(t('invalid_choice') + " 0-4: ").strip()
            if choice == "0":
                print(t('program_exited'))
                exit(0)
            elif choice == "1":
                config["mode"] = "pdf"
                break
            elif choice == "2":
                config["mode"] = "markdown"
                break
            elif choice == "3":
                config["mode"] = "watermark_only"
                break
            elif choice == "4":
                config["mode"] = "markdown_no_watermark"
                break
            else:
                print(t('invalid_choice') + " 0-4")
        
        # If no watermark mode, skip watermark configuration
        if config.get("mode") == "markdown_no_watermark":
            config["type"] = "none"
            break
        
        # Watermark type selection
        print()
        print(t('watermark_type_title'))
        print(f"   [1] {t('text_watermark_recommended')}")
        print(f"   [2] {t('image_watermark')}")
        print(f"   [0] {t('back_to_previous')}")
        
        while True:
            choice = input(t('invalid_choice') + " 0-2: ").strip()
            if choice == "0":
                break  # Return to previous menu
            elif choice == "1":
                config["type"] = "text"
                break
            elif choice == "2":
                config["type"] = "image"
                break
            else:
                print(t('invalid_choice') + " 0-2")
        
        if choice == "0":
            continue  # Return to previous menu
        
        # If watermark type is selected, continue configuration
        if config.get("type"):
            break
    
    # Continue configuring watermark parameters
    if config.get("type") == "none":
        # No watermark mode, use default configuration
        config.update({
            "font_size": WatermarkConfig.FONT_SIZE,
            "text_color": WatermarkConfig.TEXT_COLOR,
            "padding": WatermarkConfig.PADDING,
            "watermark_type": WatermarkConfig.WATERMARK_TYPE,
            "opacity": WatermarkConfig.OPACITY,
            "angle": WatermarkConfig.ANGLE,
            "image_scale": WatermarkConfig.IMAGE_SCALE,
            "horizontal_boxes": WatermarkConfig.HORIZONTAL_BOXES,
            "vertical_boxes": WatermarkConfig.VERTICAL_BOXES,
            "input_dir": "input",
            "output_dir": "output",
            "verbose": False
        })
    elif config["type"] == "text":
        # Text watermark configuration
        print()
        print(t('text_watermark_config'))
        print(f"   [0] {t('back_to_previous')}")
        
        # Watermark text
        while True:
            text = input(t('enter_watermark_text')).strip()
            if text == "0":
                return None  # Return to previous menu
            elif text:
                config["text"] = text
                break
            else:
                print(t('watermark_text_cannot_be_empty'))
        
        # Whether to add date
        while True:
            add_date = input(t('add_date_to_watermark')).strip().lower()
            if add_date == "0":
                return None  # Return to previous menu
            elif add_date in ["", "y", "n"]:
                config["add_date"] = add_date != "n"
                break
            else:
                print(t('enter_y_n_or_0'))
    
    else:
        # Image watermark configuration
        print()
        print(t('image_watermark_config'))
        print(f"   [0] {t('back_to_previous')}")
        
        while True:
            image_path = input(t('enter_watermark_image_path')).strip()
            if image_path == "0":
                return None  # Return to previous menu
            elif image_path and os.path.exists(image_path):
                config["image"] = image_path
                break
            elif image_path:
                print(t('image_file_not_found') + f": {image_path}")
            else:
                print(t('image_path_cannot_be_empty'))
    
    # Use default configuration to fill other parameters
    config.update({
        "font_size": WatermarkConfig.FONT_SIZE,
        "text_color": WatermarkConfig.TEXT_COLOR,
        "padding": WatermarkConfig.PADDING,
        "watermark_type": WatermarkConfig.WATERMARK_TYPE,
        "opacity": WatermarkConfig.OPACITY,
        "angle": WatermarkConfig.ANGLE,
        "image_scale": WatermarkConfig.IMAGE_SCALE,
        "horizontal_boxes": WatermarkConfig.HORIZONTAL_BOXES,
        "vertical_boxes": WatermarkConfig.VERTICAL_BOXES,
        "input_dir": "input",
        "output_dir": "output",
        "verbose": False
    })
    
    return config


def run_watermark_command(args: List[str]) -> tuple[str, str, int]:
    """
    Run watermark CLI command and return results.
    
    Args:
        args: List of arguments for watermark command
        
    Returns:
        tuple: (stdout, stderr, return_code) Command execution results
    """
    # Try different watermark command paths
    watermark_commands = [
        "watermark",  # Command in system PATH
        "pdf-watermark",  # Alternative command name
        sys.executable.replace("python", "watermark"),  # Command in virtual environment
    ]
    
    for cmd in watermark_commands:
        try:
            result = subprocess.run(
                [cmd] + args,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout, result.stderr, 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    return "", "watermark command not found", 1


def check_watermark_tool() -> bool:
    """
    Check if watermark tool is available.
    
    Returns:
        bool: True if watermark tool is available, False otherwise
    """
    try:
        subprocess.run(["watermark", "--help"], capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_pdf_files(input_dir: Path) -> List[Path]:
    """
    Get all PDF files in the input directory.
    
    Args:
        input_dir: Input directory path
        
    Returns:
        List[Path]: Sorted list of PDF file paths
    """
    pdf_files: List[Path] = []
    for pattern in ["*.pdf", "*.PDF"]:
        pdf_files.extend(input_dir.glob(pattern))
    return sorted(pdf_files)


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

# ========= New: Render text to image (CJK supported) =========

def get_today_str() -> str:
    """
    Return today's date string in the format YYYY-MM-DD.
    
    Returns:
        str: Date string
    """
    return date.today().isoformat()

def _get_font_candidates() -> List[str]:
    """
    Get candidate paths for common CJK fonts.
    
    Returns:
        List[str]: Font file paths in priority order
    """
    return [
        # Windows common CJK fonts
        r"C:\\Windows\\Fonts\\msyh.ttc",       # Microsoft YaHei
        r"C:\\Windows\\Fonts\\msyhbd.ttc",     # Microsoft YaHei Bold
        r"C:\\Windows\\Fonts\\msyhl.ttc",      # Microsoft YaHei Light
        r"C:\\Windows\\Fonts\\simhei.ttf",     # SimHei
        r"C:\\Windows\\Fonts\\simsun.ttc",     # SimSun
        r"C:\\Windows\\Fonts\\simkai.ttf",     # KaiTi
        r"C:\\Windows\\Fonts\\simfang.ttf",    # FangSong
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
    """
    Fuzzy search for CJK fonts in the Windows fonts directory.
    
    Returns:
        Optional[str]: Font path if found, else None
    """
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
    """
    Look for a CJK font via env var and common paths.
    
    Returns:
        Optional[str]: Font path if found, else None
    """
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
    
    Args:
        text: Text content to render
        out_path: Output image path
        font_size: Font size, default 48
        color: RGBA tuple for text color, default (68, 68, 68, 220)
        padding: Padding in pixels, default 20
        
    Returns:
        Optional[str]: Generated image path, or None on failure
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
    print("✓ " + t('text_watermark_image_generated', path=out_path, font=font_path))
    return out_path


def add_watermark_to_file(
    input_file: Path,
    output_file: Path,
    watermark_image: str,
    watermark_type: str = "grid",
    opacity: float = 0.2,
    angle: float = 45,
    image_scale: float = 1.0,
    **kwargs
) -> bool:
    """
    Add a watermark to a single PDF file.
    
    Args:
        input_file: Input PDF file path
        output_file: Output PDF file path
        watermark_image: Watermark image path
        watermark_type: Watermark type, default "grid"
        opacity: Opacity, default 0.2
        angle: Rotation angle in degrees, default 45
        image_scale: Image scale, default 1.0
        **kwargs: Additional parameters such as horizontal_boxes, vertical_boxes
        
    Returns:
        bool: True if succeeded, False otherwise
    """
    args = [
        watermark_type,
        str(input_file),
        watermark_image,
        "-s", str(output_file),
        "-o", str(opacity),
        "-a", str(angle),
        "-is", str(image_scale),
        "--verbose", "False"
    ]
    if watermark_type == "grid":
        args.extend(["-h", str(kwargs.get("horizontal_boxes", 3)), "-v", str(kwargs.get("vertical_boxes", 6))])
        if kwargs.get("margin", False):
            args.append("-m")
    elif watermark_type == "insert":
        args.extend(["-x", str(kwargs.get("x", 0.5)), "-y", str(kwargs.get("y", 0.5)), "-ha", kwargs.get("horizontal_alignment", "center")])
    if kwargs.get("unselectable", False):
        args.append("--unselectable")
    if kwargs.get("save_as_image", False):
        args.append("--save-as-image")

    stdout, stderr, return_code = run_watermark_command(args)
    if return_code != 0:
        print("✗ " + t('processing_failed_with_error', file=input_file.name, error=stderr))
        return False
    print("✓ " + t('processing_successful', src=input_file.name, dst=output_file.name))
    return True


def process_all_pdfs(
    input_dir: str = "input",
    output_dir: str = "output",
    watermark_image: str = None,
    watermark_type: str = "grid",
    **kwargs
) -> bool:
    """
    Process all PDF files in the input directory.
    
    Args:
        input_dir: Input directory path, default "input"
        output_dir: Output directory path, default "output"
        watermark_image: Watermark image path
        watermark_type: Watermark type, default "grid"
        **kwargs: Other watermark parameters
        
    Returns:
        bool: True if all files succeeded, else False
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    if not input_path.exists():
        print("✗ " + t('input_directory_not_exists', directory=input_dir))
        return False
    output_path.mkdir(parents=True, exist_ok=True)

    pdf_files = get_pdf_files(input_path)
    if not pdf_files:
        print("✗ " + t('no_pdf_files_in_directory', directory=input_dir))
        return False

    print("✓ " + t('found_pdf_files', count=len(pdf_files)))
    print(f"✓ {t('watermark_image')}: {watermark_image}")
    print(f"✓ {t('watermark_type')}: {watermark_type}")
    print("=" * 50)

    success_count = 0
    total_count = len(pdf_files)
    for pdf_file in pdf_files:
        output_file = output_path / pdf_file.name
        if add_watermark_to_file(
            pdf_file,
            output_file,
            watermark_image=watermark_image,
            watermark_type=watermark_type,
            **kwargs
        ):
            success_count += 1

    print("=" * 50)
    print("✓ " + t('pdf_processing_completed', success=success_count, total=total_count))
    if success_count < total_count:
        print("✗ " + t('processing_failed'))
        return False
    return True


# ========= New: Markdown -> PDF (Mermaid supported) =========

def get_md_files(input_dir: Path) -> List[Path]:
    """
    Get all Markdown files in the input directory.
    
    Args:
        input_dir: Input directory path
        
    Returns:
        List[Path]: Sorted list of Markdown file paths
    """
    md_files: List[Path] = []
    for pattern in ["*.md", "*.MD", "*.markdown"]:
        md_files.extend(input_dir.glob(pattern))
    return sorted(md_files)


def md_to_pdf_with_mermaid(md_path: Path, out_pdf: Path) -> bool:
    """
    Convert Markdown to a Mermaid-supported PDF using Playwright.
    
    Args:
        md_path: Input Markdown file path
        out_pdf: Output PDF file path
        
    Returns:
        bool: True if succeeded, False otherwise
    """
    try:
        import markdown  # type: ignore
    except Exception:
        print("✗ " + t('missing_dependency_markdown'))
        return False
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        print("✗ " + t('missing_dependency_playwright'))
        return False

    html_body = markdown.markdown(
        md_path.read_text(encoding="utf-8"),
        extensions=["fenced_code", "tables", "toc"]
    )

    html = f"""
<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<title>{md_path.stem}</title>
<link rel=\"preconnect\" href=\"https://cdnjs.cloudflare.com\">
<link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown.min.css\">
<link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css\">
<style>
@page {{ size: A4; margin: 18mm; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Liberation Sans', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'WenQuanYi Micro Hei', sans-serif;
  line-height: 1.6;
}}
.markdown-body {{ box-sizing: border-box; min-width: 200px; max-width: 980px; margin: 0 auto; }}
pre, code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; }}
.mermaid {{ text-align: center; margin: 12px 0; }}
h1, h2, h3 {{ page-break-after: avoid; }}
img {{ max-width: 100%; }}
</style>
<script src=\"https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js\"></script>
<script src=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js\"></script>
<script>mermaid.initialize({{ startOnLoad: true, securityLevel: 'loose' }});</script>
</head>
<body>
<article class=\"markdown-body\">
{html_body}
</article>
<script>
(function() {{
  const blocks = Array.from(document.querySelectorAll('code.language-mermaid, pre code.language-mermaid'));
  blocks.forEach((code) => {{
    const parent = code.closest('pre') || code;
    const container = document.createElement('div');
    container.className = 'mermaid';
    container.textContent = code.textContent;
    parent.replaceWith(container);
  }});
  try {{ window.hljs?.highlightAll(); }} catch (e) {{}}
  setTimeout(() => window.mermaid?.init(), 50);
}})();
</script>
</body>
</html>
"""

    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            try:
                page.wait_for_function("document.querySelectorAll('.mermaid svg').length > 0", timeout=5000)
            except Exception:
                pass
            page.pdf(path=str(out_pdf), print_background=True, prefer_css_page_size=True)
            browser.close()
        print("✓ " + t('conversion_successful', input_file=md_path.name, output_file=out_pdf.name))
        return True
    except Exception as e:
        print("✗ " + t('conversion_failed_with_error', file=md_path.name, error=str(e)))
        return False


def process_all_mds(
    input_dir: str = "input",
    output_dir: str = "output",
    watermark_image: Optional[str] = None,
    config: Optional[dict] = None,
) -> bool:
    """
    Process all Markdown files, convert to PDF, and add watermark.
    
    Args:
        input_dir: Input directory path, default "input"
        output_dir: Output directory path, default "output"
        watermark_image: Watermark image path
        config: User configuration dictionary
        
    Returns:
        bool: True if all files succeeded, else False
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    if not input_path.exists():
        print("✗ " + t('input_directory_not_exists', directory=input_dir))
        return False
    output_path.mkdir(parents=True, exist_ok=True)

    md_files = get_md_files(input_path)
    if not md_files:
        print("✗ " + t('no_md_files_in_directory', directory=input_dir))
        return False

    print("✓ " + t('found_md_files', count=len(md_files)))
    ok = 0
    for md in md_files:
        out_pdf = output_path / f"{md.stem}.pdf"
        if md_to_pdf_with_mermaid(md, out_pdf):
            # After conversion, add watermark (image watermark only)
            if watermark_image:
                # Use user configuration or defaults
                watermark_type = config.get("watermark_type", WatermarkConfig.WATERMARK_TYPE) if config else WatermarkConfig.WATERMARK_TYPE
                horizontal_boxes = config.get("horizontal_boxes", WatermarkConfig.HORIZONTAL_BOXES) if config else WatermarkConfig.HORIZONTAL_BOXES
                vertical_boxes = config.get("vertical_boxes", WatermarkConfig.VERTICAL_BOXES) if config else WatermarkConfig.VERTICAL_BOXES
                angle = config.get("angle", WatermarkConfig.ANGLE) if config else WatermarkConfig.ANGLE
                opacity = config.get("opacity", WatermarkConfig.OPACITY) if config else WatermarkConfig.OPACITY
                image_scale = config.get("image_scale", WatermarkConfig.IMAGE_SCALE) if config else WatermarkConfig.IMAGE_SCALE
                
                add_watermark_to_file(
                    input_file=out_pdf,
                    output_file=out_pdf,
                    watermark_image=watermark_image,
                    watermark_type=watermark_type,
                    horizontal_boxes=horizontal_boxes,
                    vertical_boxes=vertical_boxes,
                    angle=angle,
                    opacity=opacity,
                    image_scale=image_scale,
                )
            ok += 1
    print("=" * 50)
    print("✓ " + t('md_conversion_completed', success=ok, total=len(md_files)))
    return ok == len(md_files)


def _setup_watermark_image(config: dict) -> Optional[str]:
    """
    Set up the watermark image, preferring generation from text.
    
    Args:
        config: User configuration dictionary
        
    Returns:
        Optional[str]: Path to watermark image, or None if unavailable
    """
    # If an image watermark is explicitly provided
    if config.get("type") == "image" and "image" in config:
        if os.path.exists(config["image"]):
            return config["image"]
        else:
            print("✗ " + t('image_file_not_found') + f": {config['image']}")
            return None
    
    # Generate watermark image from text
    if config.get("type") == "text" and "text" in config:
        # Build watermark text for image content (optionally append date for display)
        if config.get("add_date", True):
            watermark_text = f"{config['text']} - {get_today_str()}"
        else:
            watermark_text = config["text"]

        # Build output filename based on text + digits-only timestamp (no special chars)
        def _sanitize_filename(value: str) -> str:
            # Keep letters, numbers, underscore, hyphen, and space; replace others with '_'
            safe = []
            for ch in value:
                if ch.isalnum() or ch in ['_', '-', ' ']:
                    safe.append(ch)
                else:
                    safe.append('_')
            # Collapse spaces to '_' and limit length
            name = ''.join(safe).strip()
            name = '_'.join(name.split())
            return name[:80] if len(name) > 80 else name

        base_text_for_filename = _sanitize_filename(config["text"]) or "watermark"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        out_dir = Path("watermarks")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = str(out_dir / f"{base_text_for_filename}_{timestamp}.png")

        # Generate the text watermark image
        generated = generate_text_watermark_image(
            watermark_text,
            out_path,
            font_size=config.get("font_size", WatermarkConfig.FONT_SIZE),
            color=config.get("text_color", WatermarkConfig.TEXT_COLOR),
            padding=config.get("padding", WatermarkConfig.PADDING)
        )
        if generated:
            return generated
        else:
            return find_watermark_image()
    
    # Fallback: find an existing watermark image if generation fails
    return find_watermark_image()


def _process_pdf_files(input_dir: str, output_dir: str, watermark_image: str, config: dict) -> bool:
    """
    Process PDF files and add watermark.
    
    Args:
        input_dir: Input directory path
        output_dir: Output directory path
        watermark_image: Watermark image path
        config: User configuration dictionary
        
    Returns:
        bool: True on success, else False
    """
    if not check_watermark_tool():
        print("✗ " + t('watermark_cli_not_found'))
        print(t('install_pdf_watermark_hint'))
        return False
    
    print("✓ " + t('watermark_cli_available'))
    return process_all_pdfs(
        input_dir=input_dir,
        output_dir=output_dir,
        watermark_image=watermark_image,
        watermark_type=config.get("watermark_type", WatermarkConfig.WATERMARK_TYPE),
        horizontal_boxes=config.get("horizontal_boxes", WatermarkConfig.HORIZONTAL_BOXES),
        vertical_boxes=config.get("vertical_boxes", WatermarkConfig.VERTICAL_BOXES),
        angle=config.get("angle", WatermarkConfig.ANGLE),
        opacity=config.get("opacity", WatermarkConfig.OPACITY),
        image_scale=config.get("image_scale", WatermarkConfig.IMAGE_SCALE),
    )


def _process_markdown_files(input_dir: str, output_dir: str, watermark_image: str, config: dict) -> bool:
    """
    Convert Markdown files to PDF and add watermark.
    
    Args:
        input_dir: Input directory path
        output_dir: Output directory path
        watermark_image: Watermark image path
        config: User configuration dictionary
        
    Returns:
        bool: True on success, else False
    """
    print("✓ " + t('no_pdf_found_processing_md'))
    return process_all_mds(
        input_dir=input_dir,
        output_dir=output_dir,
        watermark_image=watermark_image,
        config=config,
    )


def _process_markdown_files_no_watermark(input_dir: str, output_dir: str, config: dict) -> bool:
    """
    Convert Markdown files to PDF (no watermark).
    
    Args:
        input_dir: Input directory path
        output_dir: Output directory path
        config: User configuration dictionary
        
    Returns:
        bool: True on success, else False
    """
    print("✓ " + t('start_converting_md_no_watermark'))
    
    # Get Markdown files
    md_files = get_md_files(Path(input_dir))
    if not md_files:
        print("✗ " + t('no_md_files_in_directory', directory=input_dir))
        return False

    print("✓ " + t('found_md_files', count=len(md_files)))
    
    # Convert Markdown to PDF (no watermark)
    success_count = 0
    for md_file in md_files:
        try:
            pdf_path = Path(output_dir) / f"{md_file.stem}.pdf"
            success = md_to_pdf_with_mermaid(md_file, pdf_path)
            if success:
                print("✓ " + t('conversion_successful', input_file=md_file.name, output_file=pdf_path.name))
                success_count += 1
            else:
                print("✗ " + t('conversion_failed', file=md_file.name))
        except Exception as e:
            print("✗ " + t('conversion_failed_with_error', file=md_file.name, error=str(e)))

    if success_count == 0:
        print("✗ " + t('no_md_files_converted'))
        return False

    print("✓ " + t('md_conversion_completed', success=success_count, total=len(md_files)))
    return True


def main():
    """Main function: prioritize adding watermarks to PDFs; if no PDFs, convert Markdown to PDF (with Mermaid support) and add watermarks based on settings."""
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            # Force interactive mode
            while True:
                config = get_user_input()
                if config is not None:
                    break
        elif sys.argv[1] == "--lang" and len(sys.argv) > 2:
            # Set language
            i18n.set_language(sys.argv[2])
            print(f"Language set to: {i18n.get_current_language()}")
            # Continue normal flow
            if sys.stdin.isatty():
                while True:
                    config = get_user_input()
                    if config is not None:
                        break
            else:
                print(t('detected_non_interactive'))
                print(t('hint_interactive_mode'))
                config = {
                    "type": "text",
                    "text": "Watermark",
                    "add_date": True,
                    "font_size": WatermarkConfig.FONT_SIZE,
                    "text_color": WatermarkConfig.TEXT_COLOR,
                    "padding": WatermarkConfig.PADDING,
                    "watermark_type": WatermarkConfig.WATERMARK_TYPE,
                    "opacity": WatermarkConfig.OPACITY,
                    "angle": WatermarkConfig.ANGLE,
                    "image_scale": WatermarkConfig.IMAGE_SCALE,
                    "horizontal_boxes": WatermarkConfig.HORIZONTAL_BOXES,
                    "vertical_boxes": WatermarkConfig.VERTICAL_BOXES,
                    "input_dir": "input",
                    "output_dir": "output",
                    "verbose": False
                }
        else:
            print("Usage: python main.py [--interactive] [--lang en|zh]")
            return 1
    elif sys.stdin.isatty():
        # Interactive environment, use user input
        while True:
            config = get_user_input()
            if config is not None:
                break
    else:
        # Non-interactive environment, use default configuration
        print(t('detected_non_interactive'))
        print(t('hint_interactive_mode'))
        config = {
            "type": "text",
            "text": "Watermark",
            "add_date": True,
            "font_size": WatermarkConfig.FONT_SIZE,
            "text_color": WatermarkConfig.TEXT_COLOR,
            "padding": WatermarkConfig.PADDING,
            "watermark_type": WatermarkConfig.WATERMARK_TYPE,
            "opacity": WatermarkConfig.OPACITY,
            "angle": WatermarkConfig.ANGLE,
            "image_scale": WatermarkConfig.IMAGE_SCALE,
            "horizontal_boxes": WatermarkConfig.HORIZONTAL_BOXES,
            "vertical_boxes": WatermarkConfig.VERTICAL_BOXES,
            "input_dir": "input",
            "output_dir": "output",
            "verbose": False
        }
    
    # If watermark-only mode
    if config.get("mode") == "watermark_only":
        print()
        print("=" * 50)
        print(t('start_generating_watermark'))
        
        # Set up watermark image
        watermark_image = _setup_watermark_image(config)
        if not watermark_image:
            print("✗ " + t('watermark_image_not_found'))
            return 1
        
        print(f"✓ {t('watermark_image_generated')} {watermark_image}")
        print("✓ " + t('watermark_generation_completed'))
        return 0
    
    # If no-watermark mode
    if config.get("mode") == "markdown_no_watermark":
        print()
        print("=" * 50)
        print(t('start_converting_md_no_watermark'))
        
        input_dir = config["input_dir"]
        output_dir = config["output_dir"]
        
        # Convert Markdown directly without adding watermark
        success = _process_markdown_files_no_watermark(input_dir, output_dir, config)
        return 0 if success else 1
    
    input_dir = config["input_dir"]
    output_dir = config["output_dir"]

    # Set up watermark image
    watermark_image = _setup_watermark_image(config)
    if not watermark_image:
        print("✗ " + t('watermark_image_not_found'))
        return 1

    print()
    print("=" * 50)
    print(t('start_processing_files'))
    print(f"✓ {t('watermark_type')}: {config.get('watermark_type', WatermarkConfig.WATERMARK_TYPE)}")
    if config.get("verbose", False):
        print(f"✓ {t('input_directory')}: {input_dir}")
        print(f"✓ {t('output_directory')}: {output_dir}")
        print(f"✓ {t('watermark_image')}: {watermark_image}")

    # Choose processing method by mode
    if config.get("mode") == "pdf":
        # Process PDF files
        success = _process_pdf_files(input_dir, output_dir, watermark_image, config)
    elif config.get("mode") == "markdown":
        # Process Markdown files
        success = _process_markdown_files(input_dir, output_dir, watermark_image, config)
    else:
        # Auto-detect mode (backward compatible)
        pdf_files_present = len(get_pdf_files(Path(input_dir))) > 0
        if pdf_files_present:
            success = _process_pdf_files(input_dir, output_dir, watermark_image, config)
        else:
            success = _process_markdown_files(input_dir, output_dir, watermark_image, config)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

