"""
PDF processing module for adding watermarks to PDF files.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from i18n import t


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


def process_pdf_files(
    input_dir: str = "input",
    output_dir: str = "output",
    watermark_image: str = None,
    watermark_type: str = "grid",
    files: Optional[List[Path]] = None,
    **kwargs
) -> Tuple[bool, List[Path]]:
    """
    Process all PDF files in the input directory.
    
    Args:
        input_dir: Input directory path, default "input"
        output_dir: Output directory path, default "output"
        watermark_image: Watermark image path
        watermark_type: Watermark type, default "grid"
        files: Optional list of specific files to process
        **kwargs: Other watermark parameters
        
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
    # Otherwise, process all PDF files in the input directory.
    pdf_files = sorted(files) if files is not None else get_pdf_files(input_path)
    if not pdf_files:
        print("✗ " + t('no_pdf_files_in_directory', directory=input_dir))
        return False, []

    print(t('found_pdf_files', count=len(pdf_files)))
    print(f"{t('watermark_image')}: {watermark_image}")
    print(f"{t('watermark_type')}: {watermark_type}")
    print("=" * 50)

    success_count = 0
    total_count = len(pdf_files)
    output_files: List[Path] = []
    
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
            output_files.append(output_file)

    print("=" * 50)
    print(t('pdf_processing_completed', success=success_count, total=total_count))
    if success_count < total_count:
        print("✗ " + t('processing_failed'))
        return False, output_files
    return True, output_files
