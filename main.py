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
from datetime import date

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
    在 watermarks/ 目录中选择一个水印图片(PNG/JPG/SVG)。
    
    Returns:
        Optional[str]: 找到的第一个图片文件路径，如果没有找到返回None
    """
    candidates: List[str] = []
    base = Path("watermarks")
    if not base.exists():
        return None
    exts = ["*.png", "*.PNG", "*.jpg", "*.jpeg", "*.svg"]
    for ext in exts:
        candidates.extend([str(p) for p in base.glob(ext)])
    return candidates[0] if candidates else None

# ========= 新增：将文本渲染为图片 (支持中文) =========

def get_today_str() -> str:
    """
    返回今天的日期字符串，格式为 YYYY-MM-DD。
    
    Returns:
        str: 今天的日期字符串
    """
    return date.today().isoformat()

def _get_font_candidates() -> List[str]:
    """
    获取常见中文字体路径候选列表。
    
    Returns:
        List[str]: 中文字体文件路径列表，按优先级排序
    """
    return [
        # Windows 常见中文字体
        r"C:\\Windows\\Fonts\\msyh.ttc",       # 微软雅黑
        r"C:\\Windows\\Fonts\\msyhbd.ttc",     # 微软雅黑 Bold
        r"C:\\Windows\\Fonts\\msyhl.ttc",      # 微软雅黑 Light
        r"C:\\Windows\\Fonts\\simhei.ttf",     # 黑体
        r"C:\\Windows\\Fonts\\simsun.ttc",     # 宋体
        r"C:\\Windows\\Fonts\\simkai.ttf",     # 楷体
        r"C:\\Windows\\Fonts\\simfang.ttf",    # 仿宋
        r"C:\\Windows\\Fonts\\SourceHanSansCN-Normal.otf",
        r"C:\\Windows\\Fonts\\NotoSansCJK-Regular.ttc",
        r"C:\\Windows\\Fonts\\AlibabaPuHuiTi-2-55-Regular.ttf",
        r"C:\\Windows\\Fonts\\HarmonyOS_Sans_SC_Regular.ttf",
        # macOS
        r"/System/Library/Fonts/PingFang.ttc",
        r"/System/Library/Fonts/Hiragino Sans GB W3.ttc",
        r"/Library/Fonts/Arial Unicode.ttf",
        # Linux 常见安装路径
        r"/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        r"/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        r"/usr/share/fonts/opentype/noto/NotoSansCJKSC-Regular.otf",
    ]


def _search_windows_fonts() -> Optional[str]:
    """
    在Windows字体目录中模糊查找中文字体。
    
    Returns:
        Optional[str]: 找到的中文字体路径，如果没有找到返回None
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
    尝试在环境变量与常见路径查找中文字体，优先微软雅黑。
    
    Returns:
        Optional[str]: 找到的中文字体路径，如果没有找到返回None
    """
    # 1) 环境变量优先
    env_font = os.environ.get("WATERMARK_FONT")
    if env_font and os.path.exists(env_font):
        return env_font

    # 2) 常见字体候选
    for font_path in _get_font_candidates():
        if os.path.exists(font_path):
            return font_path

    # 3) Windows字体目录模糊查找
    return _search_windows_fonts()


def generate_text_watermark_image(text: str, out_path: str, font_size: int = 48, color=(68, 68, 68, 220), padding: int = 20) -> Optional[str]:
    """
    将文本渲染为透明PNG图片，返回生成路径。失败返回None。
    
    Args:
        text: 要渲染的文本内容
        out_path: 输出图片路径
        font_size: 字体大小，默认48
        color: 文本颜色RGBA元组，默认(68, 68, 68, 220)
        padding: 内边距，默认20
        
    Returns:
        Optional[str]: 生成的图片路径，失败时返回None
    """
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except Exception:
        print("✗ 缺少依赖: pillow。请先运行: pip install pillow")
        return None

    font_path = _find_chinese_font_path()
    if not font_path:
        print("✗ 未找到可用中文字体。请设置环境变量 WATERMARK_FONT 指向本地 *.ttf/*.ttc，或将中文字体安装到系统。")
        return None

    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        print(f"✗ 打开字体失败: {font_path} - {e}")
        return None

    # 先测量文本尺寸
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
    print(f"✓ 文本水印图片已生成: {out_path} 使用字体: {font_path}")
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
    为单个PDF文件添加水印。
    
    Args:
        input_file: 输入PDF文件路径
        output_file: 输出PDF文件路径
        watermark_image: 水印图片路径
        watermark_type: 水印类型，默认"grid"
        opacity: 透明度，默认0.2
        angle: 旋转角度，默认45度
        image_scale: 图片缩放比例，默认1.0
        **kwargs: 其他参数，如horizontal_boxes, vertical_boxes等
        
    Returns:
        bool: 处理成功返回True，失败返回False
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
        print(f"✗ 处理文件 {input_file.name} 失败: {stderr}")
        return False
    print(f"✓ 成功处理: {input_file.name} -> {output_file.name}")
    return True


def process_all_pdfs(
    input_dir: str = "input",
    output_dir: str = "output",
    watermark_image: str = None,
    watermark_type: str = "grid",
    **kwargs
) -> bool:
    """
    处理输入目录中的所有PDF文件。
    
    Args:
        input_dir: 输入目录路径，默认"input"
        output_dir: 输出目录路径，默认"output"
        watermark_image: 水印图片路径
        watermark_type: 水印类型，默认"grid"
        **kwargs: 其他水印参数
        
    Returns:
        bool: 所有文件处理成功返回True，否则返回False
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    if not input_path.exists():
        print(f"✗ 输入目录不存在: {input_dir}")
        return False
    output_path.mkdir(exist_ok=True)

    pdf_files = get_pdf_files(input_path)
    if not pdf_files:
        print(f"✗ 在 {input_dir} 目录中未找到PDF文件")
        return False

    print(f"✓ 找到 {len(pdf_files)} 个PDF文件")
    print(f"✓ 水印图片: {watermark_image}")
    print(f"✓ 水印类型: {watermark_type}")
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
    print(f"✓ 处理完成: {success_count}/{total_count} 个文件成功")
    if success_count < total_count:
        print(f"✗ {total_count - success_count} 个文件处理失败")
        return False
    return True


# ========= 新增：Markdown -> PDF (支持Mermaid) =========

def get_md_files(input_dir: Path) -> List[Path]:
    """
    获取输入目录中的所有Markdown文件。
    
    Args:
        input_dir: 输入目录路径
        
    Returns:
        List[Path]: 排序后的Markdown文件路径列表
    """
    md_files: List[Path] = []
    for pattern in ["*.md", "*.MD", "*.markdown"]:
        md_files.extend(input_dir.glob(pattern))
    return sorted(md_files)


def md_to_pdf_with_mermaid(md_path: Path, out_pdf: Path) -> bool:
    """
    将Markdown转换为支持Mermaid的PDF，使用Playwright渲染。
    
    Args:
        md_path: 输入Markdown文件路径
        out_pdf: 输出PDF文件路径
        
    Returns:
        bool: 转换成功返回True，失败返回False
    """
    try:
        import markdown  # type: ignore
    except Exception:
        print("✗ 缺少依赖: markdown。请先运行: pip install markdown")
        return False
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        print("✗ 缺少依赖: playwright。请先运行: pip install playwright && playwright install")
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

    out_pdf.parent.mkdir(exist_ok=True)

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
        print(f"✓ 转换成功: {md_path.name} -> {out_pdf.name}")
        return True
    except Exception as e:
        print(f"✗ 转换失败: {md_path.name} - {e}")
        return False


def process_all_mds(
    input_dir: str = "input",
    output_dir: str = "output",
    watermark_image: Optional[str] = None,
    config: Optional[dict] = None,
) -> bool:
    """
    处理输入目录中的所有Markdown文件，转换为PDF并添加水印。
    
    Args:
        input_dir: 输入目录路径，默认"input"
        output_dir: 输出目录路径，默认"output"
        watermark_image: 水印图片路径
        config: 用户配置字典
        
    Returns:
        bool: 所有文件处理成功返回True，否则返回False
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    if not input_path.exists():
        print(f"✗ 输入目录不存在: {input_dir}")
        return False
    output_path.mkdir(exist_ok=True)

    md_files = get_md_files(input_path)
    if not md_files:
        print(f"✗ 在 {input_dir} 目录中未找到Markdown文件")
        return False

    print(f"✓ 找到 {len(md_files)} 个Markdown文件 (Mermaid支持)")
    ok = 0
    for md in md_files:
        out_pdf = output_path / f"{md.stem}.pdf"
        if md_to_pdf_with_mermaid(md, out_pdf):
            # 转换后添加水印（仅使用图片水印）
            if watermark_image:
                # 使用用户配置或默认值
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
    print(f"✓ Markdown转换完成: {ok}/{len(md_files)} 成功")
    return ok == len(md_files)


def _setup_watermark_image(config: dict) -> Optional[str]:
    """
    设置水印图片，优先从文本生成。
    
    Args:
        config: 用户配置字典
        
    Returns:
        Optional[str]: 水印图片路径，如果无法获取返回None
    """
    # 如果指定了图片水印
    if config.get("type") == "image" and "image" in config:
        if os.path.exists(config["image"]):
            return config["image"]
        else:
            print(f"✗ 指定的水印图片不存在: {config['image']}")
            return None
    
    # 从文本生成水印图片
    if config.get("type") == "text" and "text" in config:
        # 构建水印文本
        if config.get("add_date", True):
            watermark_text = f"{config['text']} - {get_today_str()}"
        else:
            watermark_text = config["text"]
        
        # 生成文本水印图片
        generated = generate_text_watermark_image(
            watermark_text, 
            WatermarkConfig.TEXT_WATERMARK_FILE, 
            font_size=config.get("font_size", WatermarkConfig.FONT_SIZE),
            color=config.get("text_color", WatermarkConfig.TEXT_COLOR),
            padding=config.get("padding", WatermarkConfig.PADDING)
        )
        if generated:
            return generated
        else:
            return find_watermark_image()
    
    # 回退到查找现有水印图片
    return find_watermark_image()


def _process_pdf_files(input_dir: str, output_dir: str, watermark_image: str, config: dict) -> bool:
    """
    处理PDF文件添加水印。
    
    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径
        watermark_image: 水印图片路径
        config: 用户配置字典
        
    Returns:
        bool: 处理成功返回True，失败返回False
    """
    if not check_watermark_tool():
        print("✗ Watermark CLI工具未找到")
        print("请先安装pdf-watermark:\n  pip install pdf-watermark")
        return False
    
    print("✓ Watermark CLI工具可用")
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
    处理Markdown文件转换为PDF并添加水印。
    
    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径
        watermark_image: 水印图片路径
        config: 用户配置字典
        
    Returns:
        bool: 处理成功返回True，失败返回False
    """
    print("✓ 未找到PDF，将处理Markdown并转换为PDF (Mermaid) 并添加水印")
    return process_all_mds(
        input_dir=input_dir,
        output_dir=output_dir,
        watermark_image=watermark_image,
        config=config,
    )


def _process_markdown_files_no_watermark(input_dir: str, output_dir: str, config: dict) -> bool:
    """
    处理Markdown文件转换为PDF（无水印）。
    
    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径
        config: 用户配置字典
        
    Returns:
        bool: 处理成功返回True，失败返回False
    """
    print("✓ " + t('start_converting_md_no_watermark'))
    
    # 获取Markdown文件
    md_files = get_md_files(Path(input_dir))
    if not md_files:
        print("✗ " + t('no_md_files_in_directory', directory=input_dir))
        return False

    print("✓ " + t('found_md_files', count=len(md_files)))
    
    # 转换Markdown到PDF（无水印）
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
    
    # 如果是仅生成水印模式
    if config.get("mode") == "watermark_only":
        print()
        print("=" * 50)
        print(t('start_generating_watermark'))
        
        # 设置水印图片
        watermark_image = _setup_watermark_image(config)
        if not watermark_image:
            print("✗ " + t('watermark_image_not_found'))
            return 1
        
        print(f"✓ {t('watermark_image_generated')} {watermark_image}")
        print("✓ " + t('watermark_generation_completed'))
        return 0
    
    # 如果是无水印模式
    if config.get("mode") == "markdown_no_watermark":
        print()
        print("=" * 50)
        print(t('start_converting_md_no_watermark'))
        
        input_dir = config["input_dir"]
        output_dir = config["output_dir"]
        
        # 直接转换Markdown，不添加水印
        success = _process_markdown_files_no_watermark(input_dir, output_dir, config)
        return 0 if success else 1
    
    input_dir = config["input_dir"]
    output_dir = config["output_dir"]

    # 设置水印图片
    watermark_image = _setup_watermark_image(config)
    if not watermark_image:
        print("✗ " + t('watermark_image_not_found'))
        return 1

    print()
    print("=" * 50)
    print(t('start_processing_files'))
    print(f"✓ {t('watermark_mode')}: 图片")
    if config.get("verbose", False):
        print(f"✓ {t('input_directory')}: {input_dir}")
        print(f"✓ {t('output_directory')}: {output_dir}")
        print(f"✓ {t('watermark_image')}: {watermark_image}")

    # 根据模式选择处理方式
    if config.get("mode") == "pdf":
        # 处理PDF文件
        success = _process_pdf_files(input_dir, output_dir, watermark_image, config)
    elif config.get("mode") == "markdown":
        # 处理Markdown文件
        success = _process_markdown_files(input_dir, output_dir, watermark_image, config)
    else:
        # 自动检测模式（向后兼容）
        pdf_files_present = len(get_pdf_files(Path(input_dir))) > 0
        if pdf_files_present:
            success = _process_pdf_files(input_dir, output_dir, watermark_image, config)
        else:
            success = _process_markdown_files(input_dir, output_dir, watermark_image, config)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

