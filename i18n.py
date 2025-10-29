#!/usr/bin/env python3
"""
Internationalization support module
Supports English and Chinese languages, automatically selects based on system language
"""

import locale
import os
from typing import Dict, Any


class I18n:
    """Internationalization class, manages multi-language support"""
    
    def __init__(self):
        self.current_language = self._detect_system_language()
        self.translations = self._load_translations()
    
    def _detect_system_language(self) -> str:
        """Detect system language"""
        try:
            # Get system language environment
            system_lang = locale.getdefaultlocale()[0]
            if system_lang:
                # Extract language code (e.g., 'zh_CN' -> 'zh')
                lang_code = system_lang.split('_')[0].lower()
                if lang_code in ['zh', 'chinese']:
                    return 'zh'
                elif lang_code in ['en', 'english']:
                    return 'en'
            
            # Check environment variables
            env_lang = os.environ.get('LANG', '').lower()
            if 'zh' in env_lang:
                return 'zh'
            elif 'en' in env_lang:
                return 'en'
                
        except Exception:
            pass
        
        # Default to English
        return 'en'
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translation files"""
        return {
            'en': {
                # 主菜单
                'app_title': 'Markdown to PDF Tool',
                'select_operation_mode': 'Please select operation mode:',
                'operation_mode_title': '1. Operation Mode Selection:',
                'process_pdf_with_watermark': 'Process PDF files (add watermark)',
                'convert_md_to_pdf_with_watermark': 'Convert Markdown to PDF (add watermark)',
                'generate_watermark_only': 'Generate watermark image only',
                'convert_md_to_pdf_no_watermark': 'Convert Markdown to PDF (no watermark)',
                'exit_program': 'Exit program',
                'invalid_choice': 'Invalid choice, please enter',
                'watermark_type_title': '2. Watermark Type Selection:',
                'text_watermark_recommended': 'Text watermark (recommended)',
                'image_watermark': 'Image watermark',
                'back_to_previous': 'Back to previous',
                'text_watermark_config': '3. Text Watermark Configuration:',
                'image_watermark_config': '3. Image Watermark Configuration:',
                'enter_watermark_text': 'Please enter watermark text:',
                'watermark_text_cannot_be_empty': 'Watermark text cannot be empty, please re-enter',
                'add_date_to_watermark': 'Add date to watermark text? (y/n, default: y):',
                'enter_watermark_image_path': 'Please enter watermark image path:',
                'image_file_not_found': 'Image file not found:',
                'image_path_cannot_be_empty': 'Image path cannot be empty',
                'enter_y_n_or_0': 'Please enter y, n or 0 to go back',
                
                # 处理过程
                'start_generating_watermark': 'Start generating watermark image...',
                'start_converting_md_no_watermark': 'Start converting Markdown to PDF (no watermark)...',
                'start_processing_files': 'Start processing files...',
                'watermark_mode': 'Watermark mode',
                'input_directory': 'Input directory',
                'output_directory': 'Output directory',
                'watermark_image': 'Watermark image',
                'text_watermark_generated': 'Text watermark image generated:',
                'using_font': 'Using font:',
                'watermark_generation_completed': 'Watermark generation completed!',
                'watermark_image_generated': 'Watermark image generated:',
                'no_pdf_found_processing_md': 'No PDF found, will process Markdown and convert to PDF (Mermaid) and add watermark',
                'found_md_files': 'Found {count} Markdown files (Mermaid support)',
                'conversion_successful': 'Conversion successful: {input_file} -> {output_file}',
                'conversion_failed': 'Conversion failed: {file}',
                'conversion_failed_with_error': 'Conversion failed: {file} - {error}',
                'no_md_files_converted': 'No Markdown files converted successfully',
                'md_conversion_completed': 'Markdown conversion completed: {success}/{total} successful',
                'processing_pdf_files': 'Processing PDF files...',
                'processing_md_files': 'Processing Markdown files...',
                'pdf_processing_completed': 'PDF processing completed: {success}/{total} successful',
                'no_pdf_files_processed': 'No PDF files processed successfully',
                'found_pdf_files': 'Found {count} PDF files',
                'processing_successful': 'Processing successful: {src} -> {dst}',
                'processing_failed': 'Processing failed: {file}',
                'processing_failed_with_error': 'Processing failed: {file} - {error}',
                
                # 错误信息
                'watermark_image_not_found': 'Watermark image not found and text to image conversion failed',
                'no_md_files_in_directory': 'No Markdown files found in {directory} directory',
                'no_pdf_files_in_directory': 'No PDF files found in {directory} directory',
                'detected_non_interactive': 'Detected non-interactive environment, using default configuration...',
                'hint_interactive_mode': "Hint: Use 'python main.py --interactive' to enter interactive mode",
                'program_exited': 'Program exited',
                'missing_dependency_pillow': "Missing dependency: pillow. Please run: pip install pillow",
                'missing_dependency_markdown': "Missing dependency: markdown. Please run: pip install markdown",
                'missing_dependency_playwright': "Missing dependency: playwright. Please run: pip install playwright && playwright install",
                'chinese_font_not_found': 'No suitable CJK font found. Set WATERMARK_FONT to a local *.ttf/*.ttc or install a CJK font.',
                'open_font_failed': 'Failed to open font: {font} - {error}',
                'text_watermark_image_generated': 'Text watermark image generated: {path} Using font: {font}',
                'watermark_cli_not_found': 'Watermark CLI tool not found',
                'install_pdf_watermark_hint': 'Please install pdf-watermark:\n  pip install pdf-watermark',
                'watermark_cli_available': 'Watermark CLI tool available',
                'input_directory_not_exists': 'Input directory does not exist: {directory}',
                
                # 水印配置
                'watermark_type': 'Watermark type',
                'watermark_text': 'Watermark text',
                'watermark_image_path': 'Watermark image path',
                'add_date': 'Add date',
                'font_size': 'Font size',
                'text_color': 'Text color',
                'padding': 'Padding',
                'watermark_layout': 'Watermark layout',
                'opacity': 'Opacity',
                'rotation_angle': 'Rotation angle',
                'image_scale': 'Image scale',
                'horizontal_boxes': 'Horizontal boxes',
                'vertical_boxes': 'Vertical boxes',
                'input_dir': 'Input directory',
                'output_dir': 'Output directory',
                'verbose_output': 'Verbose output',
                'default': 'Default',
                'yes': 'Yes',
                'no': 'No',
            },
            'zh': {
                # 主菜单
                'app_title': 'Markdown转PDF工具',
                'select_operation_mode': '请选择操作模式：',
                'operation_mode_title': '1. 操作模式选择：',
                'process_pdf_with_watermark': '处理PDF文件（添加水印）',
                'convert_md_to_pdf_with_watermark': '转换Markdown到PDF（添加水印）',
                'generate_watermark_only': '仅生成图片水印',
                'convert_md_to_pdf_no_watermark': '转换Markdown到PDF（无水印）',
                'exit_program': '退出程序',
                'invalid_choice': '无效选择，请输入',
                'watermark_type_title': '2. 水印类型选择：',
                'text_watermark_recommended': '文本水印（推荐）',
                'image_watermark': '图片水印',
                'back_to_previous': '返回上一级',
                'text_watermark_config': '3. 文本水印配置：',
                'image_watermark_config': '3. 图片水印配置：',
                'enter_watermark_text': '请输入水印文本：',
                'watermark_text_cannot_be_empty': '水印文本不能为空，请重新输入',
                'add_date_to_watermark': '是否添加日期到水印文本？(y/n，默认: y)：',
                'enter_watermark_image_path': '请输入水印图片路径：',
                'image_file_not_found': '图片文件不存在：',
                'image_path_cannot_be_empty': '图片路径不能为空',
                'enter_y_n_or_0': '请输入 y、n 或 0 返回上一级',
                
                # 处理过程
                'start_generating_watermark': '开始生成水印图片...',
                'start_converting_md_no_watermark': '开始转换Markdown到PDF（无水印）...',
                'start_processing_files': '开始处理文件...',
                'watermark_mode': '水印模式',
                'input_directory': '输入目录',
                'output_directory': '输出目录',
                'watermark_image': '水印图片',
                'text_watermark_generated': '文本水印图片已生成：',
                'using_font': '使用字体：',
                'watermark_generation_completed': '水印生成完成！',
                'watermark_image_generated': '水印图片已生成：',
                'no_pdf_found_processing_md': '未找到PDF，将处理Markdown并转换为PDF (Mermaid) 并添加水印',
                'found_md_files': '找到 {count} 个Markdown文件 (Mermaid支持)',
                'conversion_successful': '转换成功：{input_file} -> {output_file}',
                'conversion_failed': '转换失败：{file}',
                'conversion_failed_with_error': '转换失败：{file} - {error}',
                'no_md_files_converted': '没有成功转换任何Markdown文件',
                'md_conversion_completed': 'Markdown转换完成：{success}/{total} 成功',
                'processing_pdf_files': '处理PDF文件...',
                'processing_md_files': '处理Markdown文件...',
                'pdf_processing_completed': 'PDF处理完成：{success}/{total} 成功',
                'no_pdf_files_processed': '没有成功处理任何PDF文件',
                'found_pdf_files': '找到 {count} 个PDF文件',
                'processing_successful': '成功处理：{src} -> {dst}',
                'processing_failed': '处理失败：{file}',
                'processing_failed_with_error': '处理失败：{file} - {error}',
                
                # 错误信息
                'watermark_image_not_found': '未找到图片水印，且文本转图片失败',
                'no_md_files_in_directory': '在 {directory} 目录中未找到Markdown文件',
                'no_pdf_files_in_directory': '在 {directory} 目录中未找到PDF文件',
                'detected_non_interactive': '检测到非交互式环境，使用默认配置...',
                'hint_interactive_mode': '提示：使用 \'python main.py --interactive\' 进入交互式模式',
                'program_exited': '程序已退出',
                'missing_dependency_pillow': '缺少依赖: pillow。请先运行: pip install pillow',
                'missing_dependency_markdown': '缺少依赖: markdown。请先运行: pip install markdown',
                'missing_dependency_playwright': '缺少依赖: playwright。请先运行: pip install playwright && playwright install',
                'chinese_font_not_found': '未找到可用中文字体。请设置环境变量 WATERMARK_FONT 指向本地 *.ttf/*.ttc，或安装中文字体。',
                'open_font_failed': '打开字体失败: {font} - {error}',
                'text_watermark_image_generated': '文本水印图片已生成: {path} 使用字体: {font}',
                'watermark_cli_not_found': 'Watermark CLI工具未找到',
                'install_pdf_watermark_hint': '请先安装pdf-watermark:\n  pip install pdf-watermark',
                'watermark_cli_available': 'Watermark CLI工具可用',
                'input_directory_not_exists': '输入目录不存在: {directory}',
                
                # 水印配置
                'watermark_type': '水印类型',
                'watermark_text': '水印文本',
                'watermark_image_path': '水印图片路径',
                'add_date': '添加日期',
                'font_size': '字体大小',
                'text_color': '文本颜色',
                'padding': '内边距',
                'watermark_layout': '水印布局',
                'opacity': '透明度',
                'rotation_angle': '旋转角度',
                'image_scale': '图片缩放',
                'horizontal_boxes': '水平网格数',
                'vertical_boxes': '垂直网格数',
                'input_dir': '输入目录',
                'output_dir': '输出目录',
                'verbose_output': '详细输出',
                'default': '默认',
                'yes': '是',
                'no': '否',
            }
        }
    
    def t(self, key: str, **kwargs) -> str:
        """Get translated text"""
        text = self.translations.get(self.current_language, {}).get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError):
                return text
        return text
    
    def set_language(self, language: str):
        """Set language"""
        if language in self.translations:
            self.current_language = language
    
    def get_current_language(self) -> str:
        """Get current language"""
        return self.current_language


# Global internationalization instance
i18n = I18n()

# Convenience function
def t(key: str, **kwargs) -> str:
    """Convenience function to get translated text"""
    return i18n.t(key, **kwargs)
