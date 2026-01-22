"""
Core processing modules for PDF watermark tool.
"""

from .pdf_processor import process_pdf_files, get_pdf_files, check_watermark_tool
from .markdown_processor import process_markdown_files, get_markdown_files
from .watermark_utils import setup_watermark_image

__all__ = [
    'process_pdf_files',
    'get_pdf_files',
    'check_watermark_tool',
    'process_markdown_files',
    'get_markdown_files',
    'setup_watermark_image',
]