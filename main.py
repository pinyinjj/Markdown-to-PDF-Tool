#!/usr/bin/env python3
"""
PDF Watermark Tool
将input目录中的所有PDF文件添加水印并输出到output目录，保持原文件不变。
同时支持将input目录中的Markdown(.md)转换为支持Mermaid的PDF并输出到output目录。
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def run_watermark_command(args: List[str]) -> tuple[str, str, int]:
    """运行watermark CLI命令并返回结果。"""
    try:
        result = subprocess.run(
            ["watermark"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout, result.stderr, 0
    except subprocess.CalledProcessError as e:
        return e.stdout, e.stderr, e.returncode
    except FileNotFoundError:
        return "", "watermark command not found", 1


def check_watermark_tool() -> bool:
    """检查watermark工具是否可用。"""
    try:
        subprocess.run(["watermark", "--help"], capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_pdf_files(input_dir: Path) -> List[Path]:
    """获取输入目录中的所有PDF文件。"""
    pdf_files: List[Path] = []
    for pattern in ["*.pdf", "*.PDF"]:
        pdf_files.extend(input_dir.glob(pattern))
    return sorted(pdf_files)


def find_watermark_image() -> Optional[str]:
    """在 watermarks/ 目录中选择一个水印图片(PNG/JPG/SVG)。"""
    candidates: List[str] = []
    base = Path("watermarks")
    if not base.exists():
        return None
    exts = ["*.png", "*.PNG", "*.jpg", "*.jpeg", "*.svg"]
    for ext in exts:
        candidates.extend([str(p) for p in base.glob(ext)])
    return candidates[0] if candidates else None


def add_watermark_to_file(
    input_file: Path,
    output_file: Path,
    watermark_image: str = None,
    watermark_text: str = "CONFIDENTIAL",
    watermark_type: str = "grid",
    opacity: float = 0.2,
    angle: float = 45,
    text_color: str = "#000000",
    text_size: int = 24,
    text_font: str = "Helvetica",
    image_scale: float = 1.0,
    **kwargs
) -> bool:
    """为单个PDF文件添加水印。"""
    args = [
        watermark_type,
        str(input_file),
        watermark_image if watermark_image else watermark_text,
        "-s", str(output_file),
        "-o", str(opacity),
        "-a", str(angle),
        "--verbose", "False"
    ]
    if watermark_image:
        args.extend(["-is", str(image_scale)])
    else:
        args.extend(["-tc", text_color, "-tf", text_font, "-ts", str(text_size)])
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
    watermark_text: str = "云箭集团 - 刘子正",
    watermark_type: str = "grid",
    **kwargs
) -> bool:
    """处理输入目录中的所有PDF文件。"""
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
    if watermark_image:
        print(f"✓ 水印图片: {watermark_image}")
    else:
        print(f"✓ 水印文本: {watermark_text}")
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
            watermark_text=watermark_text,
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
    md_files: List[Path] = []
    for pattern in ["*.md", "*.MD", "*.markdown"]:
        md_files.extend(input_dir.glob(pattern))
    return sorted(md_files)


def md_to_pdf_with_mermaid(md_path: Path, out_pdf: Path) -> bool:
    """将Markdown转换为支持Mermaid的PDF，使用Playwright渲染。"""
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


def process_all_mds(input_dir: str = "input", output_dir: str = "output", watermark_image: Optional[str] = None) -> bool:
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
            # 转换后添加图片水印（45°网格）
            if watermark_image:
                add_watermark_to_file(
                    input_file=out_pdf,
                    output_file=out_pdf,
                    watermark_image=watermark_image,
                    watermark_text="",
                    watermark_type="grid",
                    horizontal_boxes=3,
                    vertical_boxes=6,
                    angle=45,
                    opacity=0.2,
                    image_scale=1.0,
                )
            ok += 1
    print("=" * 50)
    print(f"✓ Markdown转换完成: {ok}/{len(md_files)} 成功")
    return ok == len(md_files)


def main():
    """主函数：优先为PDF添加水印；若无PDF，则转换Markdown到PDF(支持Mermaid)并添加45°图片水印。"""
    print("PDF Watermark Tool")
    print("=" * 50)

    input_dir = "input"
    output_dir = "output"

    watermark_image = find_watermark_image()
    if not watermark_image:
        print("✗ 未在 watermarks/ 目录中找到水印图片(PNG/JPG/SVG)")
        print("请将水印图片放入 watermarks/ 目录后重试")
        return 1
    print(f"✓ 使用水印图片: {watermark_image}")

    pdf_files_present = len(get_pdf_files(Path(input_dir))) > 0
    if pdf_files_present:
        if not check_watermark_tool():
            print("✗ Watermark CLI工具未找到")
            print("请先安装pdf-watermark:\n  pip install pdf-watermark")
            return 1
        print("✓ Watermark CLI工具可用")
        success = process_all_pdfs(
            input_dir=input_dir,
            output_dir=output_dir,
            watermark_image=watermark_image,
            watermark_text="云箭集团 - 刘子正",
            watermark_type="grid",
            horizontal_boxes=3,
            vertical_boxes=6,
            angle=45,
            opacity=0.2,
            image_scale=1.0,
        )
        return 0 if success else 1

    print("✓ 未找到PDF，将处理Markdown并转换为PDF (Mermaid) 并添加45°图片水印")
    success = process_all_mds(input_dir=input_dir, output_dir=output_dir, watermark_image=watermark_image)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

