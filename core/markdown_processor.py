"""
Markdown processing module for converting Markdown to PDF with Mermaid support.
"""

import asyncio
import json
import re
import threading
from pathlib import Path
from typing import List, Optional, Tuple, Dict

# 假设这些模块已在你的项目中定义
from i18n import t 
from config import WatermarkConfig
from .pdf_processor import add_watermark_to_file


# 定义资产映射：key -> 本地文件名
ASSETS_MAPPING: Dict[str, str] = {
    # --- CSS ---
    "css_github": "github-markdown.min.css",
    "css_hljs": "github.min.css",
    "css_katex": "katex.min.css",
    
    # --- JS Libs ---
    "js_hljs": "highlight.min.js",
    "js_katex": "katex.min.js",
    "js_katex_auto": "auto-render.min.js",
    "js_mermaid": "mermaid.min.js",
    "js_mdit": "markdown-it.min.js",
    "js_mdit_emoji": "markdown-it-emoji.min.js",
    
    # --- Markdown-it Plugins ---
    "js_mdit_anchor": "markdownItAnchor.min.js",
    "js_mdit_task": "markdown-it-task-lists.umd.js",
    "js_mdit_katex": "markdown-it-katex.browser.js",
    "js_mdit_toc": "markdownItTableOfContents.umd.js",
}


def get_asset_url(key: str) -> str:
    """获取资产 URL。强制使用本地 assets 目录下的文件。"""
    filename = ASSETS_MAPPING.get(key, "")
    if not filename:
        return ""
        
    local_asset = Path("assets") / filename
    if not local_asset.exists():
        print(f"✗ Critical Error: Missing local asset: {filename}. Please run download_assets.py.")
        return ""
        
    return local_asset.resolve().as_uri()


def get_custom_font_css() -> str:
    """
    Checks for local fonts and returns @font-face CSS.
    It defines 'LocalEN' for English and 'LocalCJK' for Chinese characters,
    then sets the body font family to use them in the correct order.
    """
    font_dir = Path("assets/fonts")
    
    # Find any existing Chinese font file
    cjk_font_path = None
    target_cjk_fonts = ["NotoSansMonoCJKsc-VF.otf", "NotoSansSC-Regular.otf"]
    for f_name in target_cjk_fonts:
        if (font_dir / f_name).exists():
            cjk_font_path = font_dir / f_name
            break
            
    if not cjk_font_path and font_dir.exists():
        for ext in ["*.otf", "*.ttf"]:
            found = list(font_dir.glob(ext))
            if found:
                cjk_font_path = found[0]
                break

    cjk_font_css = ""
    if cjk_font_path and cjk_font_path.exists():
        cjk_font_uri = cjk_font_path.resolve().as_uri()
        cjk_font_css = f"""
        @font-face {{
            font-family: 'LocalCJK';
            src: url('{cjk_font_uri}') format('opentype');
            font-weight: normal;
            font-style: normal;
        }}
        """

    # Combine all CSS and define the font-family stack
    final_css = cjk_font_css
    if final_css:
        # Prioritize CJK font (which includes Noto Sans Latin glyphs), then system fallbacks
        final_css += """
        .markdown-body {
            font-family: 'LocalCJK', -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif !important;
        }
        """
    
    return final_css


def remove_docsy_front_matter(md_text: str) -> str:
    """从 Markdown 文本中删除 docsy 的 front matter。"""
    lines = md_text.split('\n')
    if not lines:
        return md_text

    start_index = -1
    end_index = -1
    for i, line in enumerate(lines):
        if line.strip() == '---':
            start_index = i
            break
    
    if start_index == -1:
        return md_text
    
    for i in range(start_index + 1, len(lines)):
        if lines[i].strip() == '---':
            end_index = i
            break
    
    if end_index == -1:
        return md_text
    
    front_matter_lines = lines[start_index + 1:end_index]
    
    title = None
    title_pattern = re.compile(r'^title\s*:\s*"(.*?)"\s*$')
    for line in front_matter_lines:
        m = title_pattern.match(line.strip())
        if m:
            title = m.group(1)
            break
    
    content_lines = lines[:start_index] + lines[end_index + 1:]
    content_text = '\n'.join(content_lines)
    
    has_h1 = False
    in_code_block = False
    for line in content_lines:
        stripped = line.strip()
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if stripped.startswith('# ') and not stripped.startswith('##'):
            has_h1 = True
            break
    
    if not has_h1 and title:
        if content_text.strip():
            return f'# {title}\n\n{content_text}'
        else:
            return f'# {title}\n'
    
    return content_text


def extract_h1_title(md_path: Path) -> Optional[str]:
    """提取 Markdown 文件中的第一个 1 级标题。"""
    try:
        content = md_path.read_text(encoding="utf-8")
        processed = remove_docsy_front_matter(content)
        lines = processed.split('\n')
        
        in_code_block = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            if stripped.startswith('# ') and not stripped.startswith('##'):
                title = stripped[1:].strip()
                invalid_chars = '<>:"/\\|?*'
                for char in invalid_chars:
                    title = title.replace(char, '_')
                title = title.strip('. ')
                if len(title) > 200:
                    title = title[:200]
                return title if title else None
    except Exception:
        pass
    return None


def get_markdown_files(input_dir: Path) -> List[Path]:
    """获取所有 Markdown 文件。"""
    md_files: List[Path] = []
    for pattern in ["*.md", "*.MD", "*.markdown"]:
        md_files.extend(input_dir.glob(pattern))
    return sorted(md_files)


def _prepare_markdown_for_render(md_path: Path, filter_front_matter: bool, resolve_relative_paths: bool = False) -> Tuple[str, str]:
    """准备用于 HTML 渲染的数据。"""
    md_text = md_path.read_text(encoding="utf-8")
    if filter_front_matter:
        md_text = remove_docsy_front_matter(md_text)
    
    if resolve_relative_paths:
        # Convert relative or absolute-style image paths to absolute file URIs
        # Pattern for Markdown images: ![alt](path)
        def replace_path(match):
            alt = match.group(1)
            original_path_str = match.group(2)
            
            # Skip if it's already a remote URL or data URI
            if original_path_str.startswith(('http://', 'https://', 'data:')):
                return match.group(0)
            
            # Extract just the filename if it looks like a path (e.g., /Docsy/images/img.png -> img.png)
            filename = Path(original_path_str).name
            
            # First, check if just the filename exists in the same directory as the MD
            # (In "markdown_with_images" mode, we've flattened the structure)
            img_path = (md_path.parent / filename).resolve()
            
            if img_path.exists():
                print(f"DEBUG: Simplified image path: [{original_path_str}] -> [{filename}]")
                return f'![{alt}]({filename})'
            
            # If not found, try to resolve original path relative to the markdown file
            img_path_full = (md_path.parent / original_path_str).resolve()
            if img_path_full.exists():
                print(f"DEBUG: Found image at original path: [{original_path_str}]")
                return match.group(0)
            
            print(f"DEBUG: Failed to resolve image path: [{original_path_str}] (searched for '{filename}' in {md_path.parent})")
            return match.group(0)
            
        # Use a more robust regex to avoid matching across lines or breaking on nested brackets
        md_text = re.sub(r'!\[([^\]]*)\]\(([^\)]*)\)', replace_path, md_text)

    md_source_js = json.dumps(md_text)
    base_href = md_path.parent.resolve().as_uri() + "/"
    return md_source_js, base_href


async def md_to_pdf_with_mermaid_async(md_path: Path, out_pdf: Path, filter_front_matter: bool = False, resolve_relative_paths: bool = False) -> bool:
    """异步转换 Markdown 为 PDF。"""
    import sys
    import asyncio
    
    # Second safety check: Playwright needs Proactor on Windows
    if sys.platform == 'win32':
        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except:
                pass

    try:
        from playwright.async_api import async_playwright
    except Exception:
        print("✗ Playwright dependency missing")
        return False

    md_source_js, base_href = _prepare_markdown_for_render(md_path, filter_front_matter, resolve_relative_paths)
    font_css = get_custom_font_css()
    
    js_keys = [
        'js_mdit', 'js_hljs', 'js_katex', 'js_katex_auto', 'js_mermaid',
        'js_mdit_anchor', 'js_mdit_toc', 'js_mdit_katex', 'js_mdit_task', 'js_mdit_emoji'
    ]
    script_tags = "\n".join([f'<script src="{get_asset_url(key)}"></script>' for key in js_keys if get_asset_url(key)])

    template_path = Path(__file__).parent / "template.html"
    if not template_path.exists():
        print(f"✗ Critical Error: HTML template not found at {template_path}")
        return False
    
    template_content = template_path.read_text(encoding="utf-8")
    
    replacements = {
        "__VAR_BASE_HREF__": base_href,
        "__VAR_TITLE__": md_path.stem,
        "__VAR_CSS_GITHUB__": get_asset_url('css_github'),
        "__VAR_CSS_HLJS__": get_asset_url('css_hljs'),
        "__VAR_CSS_KATEX__": get_asset_url('css_katex'),
        "__VAR_FONT_CSS__": font_css,
        "__VAR_SCRIPT_TAGS__": script_tags,
        "__VAR_MD_SOURCE__": md_source_js
    }
    
    html = template_content
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html)
        tmp_html_path = Path(f.name)

    try:
        async with async_playwright() as p:
            # 允许跨域访问本地文件（CSS/JS）
            browser = await p.chromium.launch(args=["--allow-file-access-from-files", "--no-sandbox"])
            page = await browser.new_page()
            
            await page.goto(tmp_html_path.resolve().as_uri(), wait_until="networkidle", timeout=60000)
            
            # 确保字体加载完成
            await page.evaluate("document.fonts.ready")
            
            await page.wait_for_function(
                "document.getElementById('md-root') && document.getElementById('md-root').innerHTML.trim().length > 0", 
                timeout=30000
            )

            await page.pdf(path=str(out_pdf), print_background=True, prefer_css_page_size=True)
            await browser.close()
        return True
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        return False
    finally:
        if tmp_html_path.exists():
            tmp_html_path.unlink()


def md_to_pdf_with_mermaid(md_path: Path, out_pdf: Path, filter_front_matter: bool = False, resolve_relative_paths: bool = False) -> bool:
    """同步包装器。"""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(md_to_pdf_with_mermaid_async(md_path, out_pdf, filter_front_matter, resolve_relative_paths))
    
    result = {"ok": False}
    def _runner():
        result["ok"] = asyncio.run(md_to_pdf_with_mermaid_async(md_path, out_pdf, filter_front_matter, resolve_relative_paths))
    t_thread = threading.Thread(target=_runner)
    t_thread.start()
    t_thread.join()
    return bool(result.get("ok", False))


def process_markdown_files(
    input_dir: str = "input",
    output_dir: str = "output",
    watermark_image: Optional[str] = None,
    config: Optional[dict] = None,
    files: Optional[List[Path]] = None,
    no_watermark: bool = False,
) -> Tuple[bool, List[Path]]:
    """批量转换 Markdown 文件。"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    if not input_path.exists():
        return False, []
    output_path.mkdir(parents=True, exist_ok=True)

    md_files = sorted(files) if files is not None else get_markdown_files(input_path)
    if not md_files:
        return False, []

    ok = 0
    output_files: List[Path] = []
    filter_front_matter = config.get("filter_front_matter", False) if config else False
    rename_by_title = config.get("rename_by_title", False) if config else False
    
    for md in md_files:
        out_pdf = output_path / f"{md.stem}.pdf"
        if md_to_pdf_with_mermaid(md, out_pdf, filter_front_matter=filter_front_matter):
            watermark_success = True
            if watermark_image and not no_watermark:
                watermark_success = add_watermark_to_file(
                    input_file=out_pdf,
                    output_file=out_pdf,
                    watermark_image=watermark_image,
                    watermark_type=config.get("watermark_type", "grid") if config else "grid",
                    opacity=config.get("opacity", 0.2) if config else 0.2,
                    angle=config.get("angle", 45) if config else 45,
                    image_scale=config.get("image_scale", 1.0) if config else 1.0,
                )
            
            if watermark_success and rename_by_title:
                h1_title = extract_h1_title(md)
                if h1_title:
                    new_pdf_path = output_path / f"{h1_title}.pdf"
                    if new_pdf_path.exists():
                        counter = 1
                        while new_pdf_path.exists():
                            new_pdf_path = output_path / f"{h1_title}_{counter}.pdf"
                            counter += 1
                    out_pdf.rename(new_pdf_path)
                    out_pdf = new_pdf_path
            
            if watermark_success:
                ok += 1
                output_files.append(out_pdf)
    
    return ok == len(md_files), output_files