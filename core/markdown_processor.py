"""
Markdown processing module for converting Markdown to PDF with Mermaid support.
"""

import json
import re
from pathlib import Path
from typing import List, Optional, Tuple

from i18n import t
from config import WatermarkConfig
from .pdf_processor import add_watermark_to_file


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


def get_markdown_files(input_dir: Path) -> List[Path]:
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
<script src=\"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.js\"></script>
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


async def md_to_pdf_with_mermaid_async(md_path: Path, out_pdf: Path, filter_front_matter: bool = False) -> bool:
    """
    Async version of md_to_pdf_with_mermaid for use in async contexts.

    Convert Markdown to a Mermaid-supported PDF using Playwright.

    Args:
        md_path: Input Markdown file path
        out_pdf: Output PDF file path
        filter_front_matter: If True, remove docsy front matter (YAML between --- markers)

    Returns:
        bool: True if succeeded, False otherwise
    """
    try:
        from playwright.async_api import async_playwright  # type: ignore
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
<meta charset="utf-8">
<title>{md_path.stem}</title>
<link rel="preconnect" href="https://cdnjs.cloudflare.com">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
<!-- KaTeX for LaTeX math rendering -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
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
.markdown-body ol {{ list-style-type: decimal; padding-left: 2em; }}
.markdown-body ol ol {{ list-style-type: lower-alpha; }}
.markdown-body ol ol ol {{ list-style-type: lower-roman; }}
</style>
<!-- KaTeX JS -->
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" onload="renderMathInElement(document.body, {{ delimiters: [{{left: '$$', right: '$$', display: true}}, {{left: '$', right: '$', display: false}}] }})"></script>
<!-- Mermaid -->
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
<script>
mermaid.initialize({{
  startOnLoad: true,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'arial',
  fontSize: 14
}});
</script>
<!-- markdown-it + plugins -->
<script src="https://cdn.jsdelivr.net/npm/markdown-it@14.0.0/dist/markdown-it.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/markdown-it-anchor@8.6.7/dist/markdownItAnchor.umd.js"></script>
<script src="https://cdn.jsdelivr.net/npm/markdown-it-table-of-contents@0.6.0/dist/markdownItTableOfContents.umd.js"></script>
<script src="https://cdn.jsdelivr.net/npm/markdown-it-highlightjs@4.0.1/dist/markdown-it-highlightjs.umd.js"></script>
<script src="https://cdn.jsdelivr.net/npm/markdown-it-katex@2.0.3/dist/markdown-it-katex.umd.js"></script>
<script src="https://cdn.jsdelivr.net/npm/markdown-it-task-lists@2.1.1/dist/markdown-it-task-lists.umd.js"></script>
<script src="https://cdn.jsdelivr.net/npm/markdown-it-emoji@3.0.0/dist/markdown-it-emoji.umd.js"></script>
<script>
const md = markdownit({{
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {{
    if (lang && hljs.getLanguage(lang)) {{
      try {{
        return hljs.highlight(str, {{ language: lang }}).value;
      }} catch (__) {{}}
    }}
    return '';
  }}
}})
.use(markdownItAnchor, {{ level: [1, 2, 3, 4, 5, 6] }})
.use(markdownItTableOfContents)
.use(markdownItHighlightjs)
.use(markdownItKatex)
.use(markdownItTaskLists)
.use(markdownItEmoji);

const mdSource = {md_source_js};
const rendered = md.render(mdSource);
document.getElementById('md-root').innerHTML = rendered;

// Re-run KaTeX
if (typeof renderMathInElement === 'function') {{
  renderMathInElement(document.body, {{ delimiters: [{{left: '$$', right: '$$', display: true}}, {{left: '$', right: '$', display: false}}] }});
}}

// Re-run Mermaid
if (typeof mermaid !== 'undefined') {{
  mermaid.init();
}}
</script>
</head>
<body>
<div id="md-root" class="markdown-body"></div>
</body>
</html>"""

    # Write HTML to temporary file
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html)
        tmp_html_path = Path(f.name)

    try:
        async with async_playwright() as p:
            # Allow Chromium to load local file:// resources (images, etc.)
            browser = await p.chromium.launch(args=["--allow-file-access-from-files"])
            page = await browser.new_page()
            await page.goto(tmp_html_path.resolve().as_uri(), wait_until="networkidle")
            try:
                # Wait until markdown-it rendering produced list items and (if present) mermaid completed
                await page.wait_for_function("document.querySelectorAll('#md-root li').length > 0", timeout=5000)
                await page.wait_for_function("document.querySelectorAll('.mermaid').length == 0 || document.querySelectorAll('.mermaid svg').length >= document.querySelectorAll('.mermaid').length", timeout=5000)
            except Exception:
                pass
            # Wait for styles to be fully applied
            await page.wait_for_timeout(500)
            await page.pdf(path=str(out_pdf), print_background=True, prefer_css_page_size=True)
            await browser.close()
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


def process_markdown_files(
    input_dir: str = "input",
    output_dir: str = "output",
    watermark_image: Optional[str] = None,
    config: Optional[dict] = None,
    files: Optional[List[Path]] = None,
    no_watermark: bool = False,
) -> Tuple[bool, List[Path]]:
    """
    Process all Markdown files, convert to PDF, and optionally add watermark.
    
    Args:
        input_dir: Input directory path, default "input"
        output_dir: Output directory path, default "output"
        watermark_image: Watermark image path (optional)
        config: User configuration dictionary
        files: Optional list of specific files to process
        no_watermark: If True, skip watermark addition
        
    Returns:
        tuple: (success: bool, output_files: List[Path])
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    if not input_path.exists():
        print("✗ " + t('input_directory_not_exists', directory=input_dir))
        return False, []
    output_path.mkdir(parents=True, exist_ok=True)

    # If a specific file list is provided, only process those files.
    # Otherwise, process all Markdown files in the input directory.
    md_files = sorted(files) if files is not None else get_markdown_files(input_path)
    if not md_files:
        print("✗ " + t('no_md_files_in_directory', directory=input_dir))
        return False, []

    print(t('found_md_files', count=len(md_files)))
    ok = 0
    output_files: List[Path] = []
    
    # Get filter_front_matter setting from config
    filter_front_matter = config.get("filter_front_matter", False) if config else False
    rename_by_title = config.get("rename_by_title", False) if config else False
    
    for md in md_files:
        out_pdf = output_path / f"{md.stem}.pdf"
        if md_to_pdf_with_mermaid(md, out_pdf, filter_front_matter=filter_front_matter):
            # After conversion, add watermark (image watermark only)
            watermark_success = True
            if watermark_image and not no_watermark:
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
                        out_pdf = new_pdf_path
                    except Exception as e:
                        print(f"⚠ Failed to rename PDF: {e}")
            
            if watermark_success:
                ok += 1
                output_files.append(out_pdf)
    
    print("=" * 50)
    print(t('md_conversion_completed', success=ok, total=len(md_files)))
    return ok == len(md_files), output_files
