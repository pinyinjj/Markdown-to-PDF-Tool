#!/usr/bin/env python3
"""
PDF Watermark Tool
Add watermarks to all PDF files in the input directory and output to the output directory, keeping original files unchanged.
Also supports converting Markdown(.md) files in the input directory to Mermaid-supported PDF and output to the output directory.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional
from datetime import date, datetime
import json
import re

# Import internationalization support
from i18n import t, i18n
from config import WatermarkConfig, GENERATE_IMAGE_FROM_TEXT, TEXT_WATERMARK_FILE
from ui.input_flow import get_user_input
from watermark.image_setup import (
    _setup_watermark_image,
    find_watermark_image,
    generate_text_watermark_image,
    get_today_str,
)

# ========= Configuration Constants =========


# get_user_input is now imported from ui.input_flow


def run_watermark_command(args: List[str]) -> tuple:
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


# find_watermark_image moved to watermark.image_setup

# ========= New: Render text to image (CJK supported) =========

# get_today_str moved to watermark.image_setup

# font candidate helpers moved to watermark.image_setup


# windows font search moved to watermark.image_setup


# font path finder moved to watermark.image_setup


# text watermark generation moved to watermark.image_setup


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
    files: Optional[List[Path]] = None,
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

    # If a specific file list is provided, only process those files.
    # Otherwise, process all PDF files in the input directory.
    pdf_files = sorted(files) if files is not None else get_pdf_files(input_path)
    if not pdf_files:
        print("✗ " + t('no_pdf_files_in_directory', directory=input_dir))
        return False

    print(t('found_pdf_files', count=len(pdf_files)))
    print(f"{t('watermark_image')}: {watermark_image}")
    print(f"{t('watermark_type')}: {watermark_type}")
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
    print(t('pdf_processing_completed', success=success_count, total=total_count))
    if success_count < total_count:
        print("✗ " + t('processing_failed'))
        return False
    return True


# ========= New: Markdown -> PDF (Mermaid supported) =========

def remove_docsy_front_matter(md_text: str) -> str:
    """
    Remove docsy front matter (YAML front matter between --- markers) from Markdown text.
    If the document doesn't have a level-1 heading (#), extract title from front matter
    and add it as a level-1 heading.
    
    Args:
        md_text: Original Markdown text
        
    Returns:
        str: Markdown text with front matter removed and title added if needed
    """
    lines = md_text.split('\n')
    
    if not lines:
        return md_text

    # Find the first and second Docsy front matter delimiters:
    # a line that consists of --- followed only by optional whitespace.
    start_index = -1
    end_index = -1
    for i, line in enumerate(lines):
        if line.strip() == '---':
            start_index = i
            break
    
    # No opening delimiter found -> nothing to do
    if start_index == -1:
        return md_text
    
    for i in range(start_index + 1, len(lines)):
        if lines[i].strip() == '---':
            end_index = i
            break
    
    # If no closing --- found, return original text (invalid / incomplete front matter)
    if end_index == -1:
        return md_text
    
    # Extract front matter content (between first --- and second ---)
    front_matter_lines = lines[start_index + 1:end_index]
    front_matter_text = '\n'.join(front_matter_lines)
    
    # Extract title from front matter:
    # We only trust the string inside the first pair of double quotes after `title:`
    title = None
    # NOTE: this is a real regex; \s means whitespace
    title_pattern = re.compile(r'^title\s*:\s*"(.*?)"\s*$')
    for line in front_matter_lines:
        m = title_pattern.match(line.strip())
        if m:
            title = m.group(1)
            break
    
    # Get content without front matter (keep any content before the first ---)
    content_lines = lines[:start_index] + lines[end_index + 1:]
    content_text = '\n'.join(content_lines)
    
    # Check if document has a level-1 heading (#)
    # Skip code blocks to avoid matching code comments
    has_h1 = False
    in_code_block = False
    for line in content_lines:
        stripped = line.strip()
        
        # Check for code block markers
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        
        # Skip lines inside code blocks
        if in_code_block:
            continue
        
        # Check for # heading (must be at start of line or after whitespace)
        if stripped.startswith('# ') and not stripped.startswith('##'):
            has_h1 = True
            break
    
    # If no H1 found and we have a title, add it as H1
    if not has_h1 and title:
        # Add title as level-1 heading at the beginning of content
        if content_text.strip():
            return f'# {title}\n\n{content_text}'
        else:
            return f'# {title}\n'
    
    # Return content without front matter (title already exists or no title found)
    return content_text


def extract_h1_title(md_path: Path) -> Optional[str]:
    """
    Extract the first level-1 heading (# Title) from a Markdown file.
    Skips code blocks to avoid matching code comments.
    
    Args:
        md_path: Path to the Markdown file
        
    Returns:
        Optional[str]: The title text (without #), or None if not found
    """
    try:
        # Read original content
        content = md_path.read_text(encoding="utf-8")
        # Apply the same Docsy front matter removal + title injection logic,
        # so that we see the synthetic H1 when there is only a Docsy title.
        processed = remove_docsy_front_matter(content)
        lines = processed.split('\n')
        
        # Track if we're inside a code block (```...```)
        in_code_block = False
        
        for line in lines:
            stripped = line.strip()
            
            # Check for code block markers
            if stripped.startswith('```'):
                in_code_block = not in_code_block
                continue
            
            # Skip lines inside code blocks
            if in_code_block:
                continue
            
            # Check for # heading (must be exactly #, not ##)
            # Also ensure it's at the start of the line (not indented code)
            if stripped.startswith('# ') and not stripped.startswith('##'):
                # Extract title: remove # and leading/trailing whitespace
                title = stripped[1:].strip()
                # Sanitize filename: remove invalid characters
                # Replace common invalid chars with underscore or remove
                invalid_chars = '<>:"/\\|?*'
                for char in invalid_chars:
                    title = title.replace(char, '_')
                # Remove leading/trailing dots and spaces
                title = title.strip('. ')
                # Limit length to avoid filesystem issues
                if len(title) > 200:
                    title = title[:200]
                return title if title else None
    except Exception:
        pass
    return None


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


def md_to_pdf_with_mermaid(md_path: Path, out_pdf: Path, filter_front_matter: bool = False) -> bool:
    """
    Convert Markdown to a Mermaid-supported PDF using Playwright.
    
    Args:
        md_path: Input Markdown file path
        out_pdf: Output PDF file path
        filter_front_matter: If True, remove docsy front matter (YAML between --- markers)
        
    Returns:
        bool: True if succeeded, False otherwise
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        print("✗ " + t('missing_dependency_playwright'))
        return False
    # Read raw Markdown source; we'll render with markdown-it in the browser to match VSCode markdown-preview-enhanced
    md_text = md_path.read_text(encoding="utf-8")
    
    # Remove front matter if requested
    if filter_front_matter:
        md_text = remove_docsy_front_matter(md_text)
    
    md_source_js = json.dumps(md_text)

    # Base directory (as file:// URI) for resolving relative paths in JS (images, local links)
    base_href = md_path.parent.resolve().as_uri() + "/"

    html = f"""
<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<title>{md_path.stem}</title>
<link rel=\"preconnect\" href=\"https://cdnjs.cloudflare.com\">
<link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown.min.css\">
<link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css\">
<!-- KaTeX for LaTeX math rendering -->
<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css\">
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
/* List styling to mirror GitHub/markdown-it */
.markdown-body ul {{ list-style-type: disc; padding-left: 2em; }}
.markdown-body ul ul {{ list-style-type: circle; }}
.markdown-body ul ul ul {{ list-style-type: square; }}
.markdown-body ol {{ padding-left: 2em; }}
/* KaTeX math rendering styles */
.katex {{ font-size: 1.1em; }}
.katex-display {{ margin: 1em 0; }}
</style>
<script src=\"https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js\"></script>
<script src=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js\"></script>
<!-- markdown-it (same family as VSCode markdown-preview-enhanced) -->
<script src=\"https://cdn.jsdelivr.net/npm/markdown-it@14/dist/markdown-it.min.js\"></script>
<!-- KaTeX for rendering LaTeX math expressions -->
<script src=\"https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js\"></script>
<script src=\"https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js\"></script>
<script>mermaid.initialize({{ startOnLoad: false, securityLevel: 'loose' }});</script>
</head>
<body>
<article class=\"markdown-body\" id=\"md-root\"></article>
<script>
// Expose base path for fixing local links (used below)
window.__MD_BASE_HREF__ = {json.dumps(base_href)};
</script>
<script>
(function() {{
  const mdSrc = {md_source_js};
  // Pre-process: replace math expressions with HTML comments as placeholders
  // This prevents markdown-it from processing them
  const mathData = [];
  let processedMd = mdSrc;
  
  // Handle display math $$...$$ first (must be processed before inline $)
  processedMd = processedMd.replace(/\\$\\$([\\s\\S]*?)\\$\\$/g, (match, content) => {{
    const id = mathData.length;
    mathData.push({{ type: 'display', content: content.trim() }});
    return `<!--MATH_DISPLAY_${{id}}-->`;
  }});
  
  // Handle inline math $...$ (avoid matching $$ by checking it's not preceded or followed by $)
  // Use a function to check context since lookbehind may not be supported
  processedMd = processedMd.replace(/\\$([^$\\n]+?)\\$/g, (match, content, offset, string) => {{
    // Check if this is actually part of a $$...$$ (already processed)
    if (string.substring(Math.max(0, offset - 1), offset) === '$' || 
        string.substring(offset + match.length, offset + match.length + 1) === '$') {{
      return match; // Skip, it's part of display math
    }}
    // Check if it's inside a comment placeholder (already processed)
    const before = string.substring(Math.max(0, offset - 50), offset);
    const after = string.substring(offset + match.length, offset + match.length + 50);
    if (before.includes('<!--MATH_') || after.includes('<!--MATH_')) {{
      return match; // Skip
    }}
    const id = mathData.length;
    mathData.push({{ type: 'inline', content: content.trim() }});
    return `<!--MATH_INLINE_${{id}}-->`;
  }});
  
  const md = window.markdownit({{ html: true, linkify: true, typographer: true, breaks: true }});
  let html = md.render(processedMd);
  
  // Replace HTML comment placeholders with actual math elements
  mathData.forEach((math, index) => {{
    const displayComment = `<!--MATH_DISPLAY_${{index}}-->`;
    const inlineComment = `<!--MATH_INLINE_${{index}}-->`;
    const comment = math.type === 'display' ? displayComment : inlineComment;
    
    if (html.includes(comment)) {{
      const tag = math.type === 'display' ? 'div' : 'span';
      const className = math.type === 'display' ? 'katex-display' : 'math-inline';
      const mathElement = `<${{tag}} class="${{className}}" data-math-content="${{math.content.replace(/"/g, '&quot;')}}">${{math.content}}</${{tag}}>`;
      html = html.replace(comment, mathElement);
    }}
  }});
  
  const root = document.getElementById('md-root');
  root.innerHTML = html;

  // Normalize local image sources and links to absolute file:// URLs based on the markdown file directory
  try {{
    const base = window.__MD_BASE_HREF__;
    if (base) {{
      // Fix <img src="..."> so that ./xxx.png 指向 markdown 所在目录，而不是输出 html 所在目录
      const imgs = root.querySelectorAll('img[src]');
      imgs.forEach(img => {{
        const src = img.getAttribute('src');
        if (!src) return;
        // Skip absolute/remote/data URLs
        if (/^(https?:|data:|ftp:)/i.test(src)) return;
        try {{
          const u = new URL(src, base);
          img.setAttribute('src', u.href);
        }} catch (e) {{}}
      }});

      // Fix <a href="..."> for local files (.ulg 等)
      const anchors = root.querySelectorAll('a[href]');
      anchors.forEach(a => {{
        const href = a.getAttribute('href');
        if (!href) return;
        // Only rewrite relative links, skip http(s), mailto etc.
        if (/^(https?:|mailto:|tel:|ftp:)/i.test(href)) return;
        try {{
          const u = new URL(href, base);
          a.setAttribute('href', u.href);
        }} catch (e) {{}}
      }});
    }}
  }} catch (e) {{}}
  // Convert mermaid code blocks
  const blocks = Array.from(root.querySelectorAll('code.language-mermaid, pre code.language-mermaid'));
  blocks.forEach((code) => {{
    const parent = code.closest('pre') || code;
    const container = document.createElement('div');
    container.className = 'mermaid';
    container.textContent = code.textContent;
    parent.replaceWith(container);
  }});
  try {{ window.hljs?.highlightAll(); }} catch (e) {{}}
  // Render math expressions with KaTeX
  try {{
    if (window.katex) {{
      // Render inline math (span.math-inline elements)
      root.querySelectorAll('span.math-inline').forEach(span => {{
        const mathContent = span.getAttribute('data-math-content') || span.textContent || '';
        if (mathContent && !span.querySelector('.katex')) {{
          try {{
            window.katex.render(mathContent.trim(), span, {{ throwOnError: false, displayMode: false }});
          }} catch (e) {{
            console.warn('KaTeX inline math error:', e, mathContent);
          }}
        }}
      }});
      // Render display math (div.katex-display elements)
      root.querySelectorAll('div.katex-display').forEach(div => {{
        const mathContent = div.getAttribute('data-math-content') || div.textContent || '';
        if (mathContent && !div.querySelector('.katex')) {{
          try {{
            window.katex.render(mathContent.trim(), div, {{ throwOnError: false, displayMode: true }});
          }} catch (e) {{
            console.warn('KaTeX display math error:', e, mathContent);
          }}
        }}
      }});
    }}
    // Also use auto-render as fallback for any remaining math expressions
    if (window.renderMathInElement) {{
      window.renderMathInElement(root, {{
        delimiters: [
          {{left: '$$', right: '$$', display: true}},
          {{left: '$', right: '$', display: false}},
          {{left: '\\\\[', right: '\\\\]', display: true}},
          {{left: '\\\\(', right: '\\\\)', display: false}}
        ],
        throwOnError: false,
        strict: false
      }});
    }}
  }} catch (e) {{ console.error('KaTeX rendering error:', e); }}
  setTimeout(() => window.mermaid?.init(), 50);
}})();
</script>
</body>
</html>
"""
 
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Write HTML to a temporary file and open it via file:// URL so that Chromium
    # is allowed to load local images referenced by relative paths.
    tmp_html_path = out_pdf.with_suffix(".html")
    tmp_html_path.write_text(html, encoding="utf-8")

    try:
        with sync_playwright() as p:
            # Allow Chromium to load local file:// resources (images, etc.)
            browser = p.chromium.launch(args=["--allow-file-access-from-files"])
            page = browser.new_page()
            page.goto(tmp_html_path.resolve().as_uri(), wait_until="networkidle")
            try:
                # Wait until markdown-it rendering produced list items and (if present) mermaid completed
                page.wait_for_function("document.querySelectorAll('#md-root li').length > 0", timeout=5000)
                page.wait_for_function("document.querySelectorAll('.mermaid').length == 0 || document.querySelectorAll('.mermaid svg').length >= document.querySelectorAll('.mermaid').length", timeout=5000)
            except Exception:
                pass
            # Wait for styles to be fully applied
            page.wait_for_timeout(500)
            page.pdf(path=str(out_pdf), print_background=True, prefer_css_page_size=True)
            browser.close()
        print("✓ " + t('conversion_successful', input_file=md_path.name, output_file=out_pdf.name))
        return True
    except Exception as e:
        print("✗ " + t('conversion_failed_with_error', file=md_path.name, error=str(e)))
        return False
    finally:
        try:
            if tmp_html_path.exists():
                tmp_html_path.unlink()
        except Exception:
            # Best-effort cleanup only
            pass


def process_all_mds(
    input_dir: str = "input",
    output_dir: str = "output",
    watermark_image: Optional[str] = None,
    config: Optional[dict] = None,
    files: Optional[List[Path]] = None,
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

    # If a specific file list is provided, only process those files.
    # Otherwise, process all Markdown files in the input directory.
    md_files = sorted(files) if files is not None else get_md_files(input_path)
    if not md_files:
        print("✗ " + t('no_md_files_in_directory', directory=input_dir))
        return False

    print(t('found_md_files', count=len(md_files)))
    ok = 0
    # Get filter_front_matter setting from config
    filter_front_matter = config.get("filter_front_matter", False) if config else False
    rename_by_title = config.get("rename_by_title", False) if config else False
    
    for md in md_files:
        out_pdf = output_path / f"{md.stem}.pdf"
        if md_to_pdf_with_mermaid(md, out_pdf, filter_front_matter=filter_front_matter):
            # After conversion, add watermark (image watermark only)
            watermark_success = True
            if watermark_image:
                # Use user configuration or defaults
                watermark_type = config.get("watermark_type", WatermarkConfig.WATERMARK_TYPE) if config else WatermarkConfig.WATERMARK_TYPE
                horizontal_boxes = config.get("horizontal_boxes", WatermarkConfig.HORIZONTAL_BOXES) if config else WatermarkConfig.HORIZONTAL_BOXES
                vertical_boxes = config.get("vertical_boxes", WatermarkConfig.VERTICAL_BOXES) if config else WatermarkConfig.VERTICAL_BOXES
                angle = config.get("angle", WatermarkConfig.ANGLE) if config else WatermarkConfig.ANGLE
                opacity = config.get("opacity", WatermarkConfig.OPACITY) if config else WatermarkConfig.OPACITY
                image_scale = config.get("image_scale", WatermarkConfig.IMAGE_SCALE) if config else WatermarkConfig.IMAGE_SCALE
                
                watermark_success = add_watermark_to_file(
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
            
            # Rename PDF based on H1 title if requested (after watermark is added)
            if watermark_success and rename_by_title:
                h1_title = extract_h1_title(md)
                if h1_title:
                    new_pdf_path = output_path / f"{h1_title}.pdf"
                    try:
                        # If target file exists, add a number suffix
                        if new_pdf_path.exists():
                            counter = 1
                            while new_pdf_path.exists():
                                new_pdf_path = output_path / f"{h1_title}_{counter}.pdf"
                                counter += 1
                        out_pdf.rename(new_pdf_path)
                        print(f"✓ Renamed PDF: {out_pdf.name} -> {new_pdf_path.name}")
                    except Exception as e:
                        print(f"⚠ Failed to rename PDF: {e}")
            
            if watermark_success:
                ok += 1
    print("=" * 50)
    print(t('md_conversion_completed', success=ok, total=len(md_files)))
    return ok == len(md_files)


# watermark image setup moved to watermark.image_setup


def _process_pdf_files(
    input_dir: str,
    output_dir: str,
    watermark_image: str,
    config: dict,
    files: Optional[List[Path]] = None,
) -> bool:
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
    
    print(t('watermark_cli_available'))
    return process_all_pdfs(
        input_dir=input_dir,
        output_dir=output_dir,
        watermark_image=watermark_image,
        watermark_type=config.get("watermark_type", WatermarkConfig.WATERMARK_TYPE),
        files=files,
        horizontal_boxes=config.get("horizontal_boxes", WatermarkConfig.HORIZONTAL_BOXES),
        vertical_boxes=config.get("vertical_boxes", WatermarkConfig.VERTICAL_BOXES),
        angle=config.get("angle", WatermarkConfig.ANGLE),
        opacity=config.get("opacity", WatermarkConfig.OPACITY),
        image_scale=config.get("image_scale", WatermarkConfig.IMAGE_SCALE),
    )


def _process_markdown_files(
    input_dir: str,
    output_dir: str,
    watermark_image: str,
    config: dict,
    files: Optional[List[Path]] = None,
) -> bool:
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
    print(t('no_pdf_found_processing_md'))
    return process_all_mds(
        input_dir=input_dir,
        output_dir=output_dir,
        watermark_image=watermark_image,
        config=config,
        files=files,
    )


def _process_markdown_files_no_watermark(
    input_dir: str,
    output_dir: str,
    config: dict,
    files: Optional[List[Path]] = None,
) -> bool:
    """
    Convert Markdown files to PDF (no watermark).
    """
    print(t('start_converting_md_no_watermark'))
    return process_all_mds(
        input_dir=input_dir,
        output_dir=output_dir,
        watermark_image=None,
        config=config,
        files=files,
    )


def _build_default_config() -> dict:
    """Create the default non-interactive configuration dict."""
    return {
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


# ---- New helpers to reduce main() complexity ----

def _obtain_config_from_cli_and_env() -> dict:
    """Unify config acquisition based on CLI args and TTY."""
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--web":
            # Start web UI - redirect to start_webui.py for proper execution
            try:
                import subprocess
                port = 8080
                if len(sys.argv) > 2:
                    try:
                        port = int(sys.argv[2])
                    except ValueError:
                        pass
                # Use start_webui.py for proper NiceGUI execution
                script_path = Path(__file__).parent / "start_webui.py"
                subprocess.run([sys.executable, str(script_path), "--port", str(port)])
                return {}  # Web UI doesn't return config
            except Exception as e:
                print(f"✗ Failed to start web UI: {e}")
                print("Please use: python start_webui.py")
                sys.exit(1)
        if arg == "--interactive":
            while True:
                cfg = get_user_input()
                if cfg is not None:
                    return cfg
        if arg == "--lang" and len(sys.argv) > 2:
            i18n.set_language(sys.argv[2])
            print(f"Language set to: {i18n.get_current_language()}")
            if sys.stdin.isatty():
                while True:
                    cfg = get_user_input()
                    if cfg is not None:
                        return cfg
            print(t('detected_non_interactive'))
            print(t('hint_interactive_mode'))
            return _build_default_config()
        print("Usage: python main.py [--interactive] [--web [port]] [--lang en|zh]")
        sys.exit(1)

    if sys.stdin.isatty():
        while True:
            cfg = get_user_input()
            if cfg is not None:
                return cfg
    print(t('detected_non_interactive'))
    print(t('hint_interactive_mode'))
    return _build_default_config()


def _cleanup_generated_watermark(watermark_image: Optional[str], config: dict) -> None:
    """
    Clean up generated watermark image file after processing.
    Only deletes files in the watermarks/ directory that were generated from text.
    Does not delete user-provided image watermarks.
    
    Args:
        watermark_image: Path to the watermark image file
        config: User configuration dictionary
    """
    if not watermark_image:
        return
    
    watermark_path = Path(watermark_image)
    
    # Only delete if:
    # 1. The file exists
    # 2. It's in the watermarks/ directory
    # 3. It was generated from text (not a user-provided image)
    if watermark_path.exists() and watermark_path.parent.name == "watermarks":
        # Check if this is a generated text watermark (not user-provided image)
        if config.get("type") == "text" or (config.get("type") != "image" and not config.get("image")):
            try:
                watermark_path.unlink()
                print(f"✓ Cleaned up generated watermark: {watermark_image}")
            except Exception as e:
                print(f"⚠ Warning: Failed to delete watermark file {watermark_image}: {e}")


def _dispatch_by_mode(config: dict) -> int:
    """Process files according to selected mode."""
    watermark_image: Optional[str] = None
    is_watermark_only_mode = config.get("mode") == "watermark_only"
    
    try:
        if is_watermark_only_mode:
            print()
            print("=" * 50)
            print(t('start_generating_watermark'))
            watermark_image = _setup_watermark_image(config)
            if not watermark_image:
                print("✗ " + t('watermark_image_not_found'))
                return 1
            print(f"{t('watermark_image_generated')} {watermark_image}")
            print(t('watermark_generation_completed'))
            # Don't clean up in watermark_only mode - user wants to keep it
            return 0

        if config.get("mode") == "markdown_no_watermark":
            print()
            print("=" * 50)
            print(t('start_converting_md_no_watermark'))
            return 0 if _process_markdown_files_no_watermark(config["input_dir"], config["output_dir"], config) else 1

        input_dir = config["input_dir"]
        output_dir = config["output_dir"]

        watermark_image = _setup_watermark_image(config)
        if not watermark_image:
            print("✗ " + t('watermark_image_not_found'))
            return 1

        print()
        print("=" * 50)
        print(t('start_processing_files'))
        print(f"{t('watermark_type')}: {config.get('watermark_type', WatermarkConfig.WATERMARK_TYPE)}")
        if config.get("verbose", False):
            print(f"{t('input_directory')}: {input_dir}")
            print(f"{t('output_directory')}: {output_dir}")
            print(f"{t('watermark_image')}: {watermark_image}")

        if config.get("mode") == "pdf":
            pdf_files_present = len(get_pdf_files(Path(input_dir))) > 0
            if pdf_files_present:
                success = _process_pdf_files(input_dir, output_dir, watermark_image, config)
            else:
                # No PDF files found, automatically fallback to Markdown processing
                md_files_present = len(get_md_files(Path(input_dir))) > 0
                if md_files_present:
                    print(t('no_pdf_found_processing_md'))
                    success = _process_markdown_files(input_dir, output_dir, watermark_image, config)
                else:
                    print("✗ " + t('no_pdf_files_in_directory', directory=input_dir))
                    print("✗ " + t('no_md_files_in_directory', directory=input_dir))
                    success = False
        elif config.get("mode") == "markdown":
            success = _process_markdown_files(input_dir, output_dir, watermark_image, config)
        else:
            pdf_files_present = len(get_pdf_files(Path(input_dir))) > 0
            success = _process_pdf_files(input_dir, output_dir, watermark_image, config) if pdf_files_present else _process_markdown_files(input_dir, output_dir, watermark_image, config)

        # Clean up generated watermark after processing (except in watermark_only mode)
        if watermark_image and not is_watermark_only_mode:
            _cleanup_generated_watermark(watermark_image, config)
        
        return 0 if success else 1
    except Exception as e:
        # Ensure cleanup even if there's an error (except in watermark_only mode)
        if watermark_image and not is_watermark_only_mode:
            _cleanup_generated_watermark(watermark_image, config)
        print(f"✗ Error during processing: {e}")
        return 1


def main():
    """Main function with simplified structure: acquire config, then dispatch by mode."""
    config = _obtain_config_from_cli_and_env()
    # If config is empty, it means web UI was started (which doesn't return)
    if not config:
        return 0
    return _dispatch_by_mode(config)


if __name__ == "__main__":
    exit(main())

