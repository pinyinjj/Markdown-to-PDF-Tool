"""
PDF processing module for adding watermarks to PDF files.
"""

import subprocess
import sys
from pathlib import Path
from typing import List

from i18n import t


def run_watermark_command(args: List[str]) -> tuple:
    """
    Execute the watermark CLI command.
    Checks multiple possible command names for compatibility.
    """
    watermark_commands = [
        "watermark",
        "pdf-watermark",
        sys.executable.replace("python", "watermark"),
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
    """Check if the watermark tool is available in the system path."""
    try:
        subprocess.run(["watermark", "--help"], capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


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
    Add watermark to a single PDF file using the external CLI tool.
    This function is used by both the CLI and the Web UI.
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
        # Log error to console for debugging
        print("✗ " + t('processing_failed_with_error', file=input_file.name, error=stderr))
        return False
        
    print("✓ " + t('processing_successful_detail', src=input_file.name, dst=output_file.name))
    return True