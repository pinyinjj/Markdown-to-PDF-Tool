#!/usr/bin/env python3
"""
PDF Watermark Tool
将input目录中的所有PDF文件添加水印并输出到output目录，保持原文件不变。
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def run_watermark_command(args: List[str]) -> tuple[str, str, int]:
    """运行watermark CLI命令并返回结果。
    
    Args:
        args: 命令行参数列表
        
    Returns:
        (stdout, stderr, return_code): 命令执行结果
    """
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
    """检查watermark工具是否可用。
    
    Returns:
        bool: 工具是否可用
    """
    try:
        result = subprocess.run(
            ["watermark", "--help"],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_chinese_font() -> str:
    """获取可用的中文字体。
    
    Returns:
        str: 可用的中文字体名称
    """
    # 由于reportlab对中文字体支持有限，使用最兼容的字体
    # 这些字体在大多数系统上都可用，并且支持Unicode字符
    compatible_fonts = [
        "Helvetica",        # 最通用的字体
        "Arial",           # Windows通用字体
        "Times-Roman",     # 备用字体
        "Courier",         # 等宽字体
    ]
    
    # 对于中文水印，建议使用Helvetica，它支持Unicode
    # 如果显示有问题，可以尝试其他字体
    return "Times-Roman"


def get_pdf_files(input_dir: Path) -> List[Path]:
    """获取输入目录中的所有PDF文件。
    
    Args:
        input_dir: 输入目录路径
        
    Returns:
        List[Path]: PDF文件路径列表
    """
    pdf_files = []
    
    # 查找所有PDF文件（包括大写扩展名）
    for pattern in ["*.pdf", "*.PDF"]:
        pdf_files.extend(input_dir.glob(pattern))
    
    return sorted(pdf_files)


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
    """为单个PDF文件添加水印。
    
    Args:
        input_file: 输入PDF文件路径
        output_file: 输出PDF文件路径
        watermark_text: 水印文本
        watermark_type: 水印类型 ("grid" 或 "insert")
        opacity: 透明度 (0-1)
        angle: 旋转角度
        text_color: 文本颜色
        text_size: 文本大小
        **kwargs: 其他参数
        
    Returns:
        bool: 是否成功
    """
    # 基础参数
    args = [
        watermark_type,
        str(input_file),
        watermark_image if watermark_image else watermark_text,  # 使用图片或文本
        "-s", str(output_file),
        "-o", str(opacity),
        "-a", str(angle),
        "--verbose", "False"
    ]
    
    # 如果是图片水印，添加图片相关参数
    if watermark_image:
        args.extend(["-is", str(image_scale)])  # 图片缩放
    else:
        # 如果是文本水印，添加文本相关参数
        args.extend(["-tc", text_color, "-tf", text_font, "-ts", str(text_size)])
    
    # 根据水印类型添加特定参数
    if watermark_type == "grid":
        args.extend([
            "-h", str(kwargs.get("horizontal_boxes", 3)),
            "-v", str(kwargs.get("vertical_boxes", 6))
        ])
        if kwargs.get("margin", False):
            args.append("-m")
    elif watermark_type == "insert":
        args.extend([
            "-x", str(kwargs.get("x", 0.5)),
            "-y", str(kwargs.get("y", 0.5)),
            "-ha", kwargs.get("horizontal_alignment", "center")
        ])
    
    # 添加可选参数
    if kwargs.get("unselectable", False):
        args.append("--unselectable")
    
    if kwargs.get("save_as_image", False):
        args.append("--save-as-image")
    
    # 执行命令
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
    """处理输入目录中的所有PDF文件。
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        watermark_text: 水印文本
        watermark_type: 水印类型
        **kwargs: 其他水印参数
        
    Returns:
        bool: 是否全部成功
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # 检查输入目录
    if not input_path.exists():
        print(f"✗ 输入目录不存在: {input_dir}")
        return False
    
    # 创建输出目录
    output_path.mkdir(exist_ok=True)
    
    # 获取所有PDF文件
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
    
    # 处理每个文件
    success_count = 0
    total_count = len(pdf_files)
    
    for pdf_file in pdf_files:
        # 生成输出文件名
        output_file = output_path / pdf_file.name
        
        # 添加水印
        if add_watermark_to_file(
            pdf_file,
            output_file,
            watermark_image=watermark_image,
            watermark_text=watermark_text,
            watermark_type=watermark_type,
            **kwargs
        ):
            success_count += 1
    
    # 输出结果
    print("=" * 50)
    print(f"✓ 处理完成: {success_count}/{total_count} 个文件成功")
    
    if success_count < total_count:
        print(f"✗ {total_count - success_count} 个文件处理失败")
        return False
    
    return True


def main():
    """主函数：处理input目录中的所有PDF文件并添加水印。"""
    print("PDF Watermark Tool")
    print("=" * 50)
    
    # 检查watermark工具
    if not check_watermark_tool():
        print("✗ Watermark CLI工具未找到")
        print("请先安装pdf-watermark:")
        print("  pip install pdf-watermark")
        return 1
    
    print("✓ Watermark CLI工具可用")
    
    # 检查水印图片是否存在
    watermark_image = "watermarks/line.png"
    if not os.path.exists(watermark_image):
        print(f"✗ 水印图片不存在: {watermark_image}")
        print("请先运行 create_watermark_image.py 创建水印图片")
        return 1
    
    print(f"✓ 找到水印图片: {watermark_image}")
    
    # 水印配置 - 使用图片水印
    watermark_config = {
        "watermark_image": watermark_image,  # 水印图片路径
        "watermark_type": "grid",           # 水印类型: "grid" 或 "insert"
        "opacity": 0.2,                     # 透明度
        "angle": 30,                        # 旋转角度 - 45度倾斜
        "image_scale": 1.0,                 # 图片缩放比例
        
        # Grid模式参数
        "horizontal_boxes": 3,              # 水平网格数
        "vertical_boxes": 6,                # 垂直网格数
        "margin": False,                    # 是否留边距
        
        # Insert模式参数
        "x": 0.5,                           # X坐标 (0-1)
        "y": 0.5,                           # Y坐标 (0-1)
        "horizontal_alignment": "center",   # 水平对齐
        
        # 可选参数
        "unselectable": False,              # 是否不可选择
        "save_as_image": False,             # 是否保存为图片
    }
    
    # 处理所有PDF文件
    success = process_all_pdfs(**watermark_config)
    
    if success:
        print("✓ 所有文件处理完成！")
        return 0
    else:
        print("✗ 部分文件处理失败")
        return 1


if __name__ == "__main__":
    exit(main())
