"""
NiceGUI web interface for PDF watermark tool.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from nicegui import ui, app
from nicegui.events import UploadEventArguments

from i18n import t, i18n
from config import WatermarkConfig
from core import (
    setup_watermark_image,
    process_pdf_files,
    process_markdown_files,
    get_pdf_files,
    get_markdown_files,
    check_watermark_tool,
)


def cleanup_generated_watermark(watermark_image: Optional[str], config: dict) -> None:
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


class WebUI:
    """Web UI for PDF watermark tool"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.uploaded_files: Dict[str, str] = {}  # filename -> filepath
        self.watermark_image_path: Optional[str] = None
        self.processing_status = ""
        self.current_language = i18n.get_current_language()
        # Whether a processing job is currently running
        self.is_processing: bool = False
        # Track processed output files for download
        self.processed_files: List[Path] = []
        # File list container
        self.file_list_container: Optional[ui.column] = None
        # Header clear button for file output section
        self.clear_files_button: Optional[ui.button] = None
        # Ensure temp_uploads directory exists and is initially clean
        temp_dir = Path('temp_uploads')
        temp_dir.mkdir(exist_ok=True)
        for p in temp_dir.iterdir():
            if p.is_file():
                try:
                    p.unlink()
                except Exception:
                    # Best-effort cleanup only
                    pass
        
    def build_ui(self):
        """Build the web UI"""
        # Set page title
        ui.page_title(t('app_title'))
        
        # Add custom CSS for modern layout
        ui.add_head_html('''
            <style>
                .main-container {
                    max-width: 1000px;
                    margin: 0 auto;
                    padding: 0.5rem 0.75rem;
                }
                .three-column-grid {
                    display: grid !important;
                    grid-template-columns: 1fr 1fr 1fr !important;
                    grid-template-rows: 320px 320px !important;
                    gap: 0.75rem !important;
                    width: 100% !important;
                }
                .row-span-2 {
                    grid-row: 1 / 3 !important;
                    grid-column: 3 !important;
                    height: calc(320px + 0.75rem + 320px) !important;
                }
                .col-span-2 {
                    grid-column: 1 / 3 !important;
                    grid-row: 2 !important;
                }
                @media (max-width: 1024px) {
                    .three-column-grid {
                        grid-template-columns: 1fr;
                    }
                }
                .card-compact {
                    padding: 0.75rem;
                    min-height: 320px;
                    height: 320px;
                    display: flex;
                    flex-direction: column;
                }
                .section-title {
                    font-size: 1rem;
                    font-weight: 600;
                    margin-bottom: 0.75rem;
                    color: #374151;
                }
                .fixed-card {
                    width: 100%;
                    min-height: 320px;
                    height: 320px;
                }
                .watermark-card-flexible {
                    width: 100%;
                    min-height: 320px;
                    height: 320px;
                    min-width: 0;
                    flex: 1 1 auto;
                }
                .file-selection-tall {
                    height: calc(320px + 0.75rem + 320px) !important;
                    min-height: calc(320px + 0.75rem + 320px) !important;
                }
                .markdown-options-container {
                    min-height: 48px;
                    display: flex;
                    align-items: flex-start;
                }
                .disabled-section {
                    opacity: 0.5;
                    pointer-events: none;
                    position: relative;
                }
                .disabled-section * {
                    cursor: not-allowed;
                }
                .disabled-label {
                    color: #9ca3af !important;
                }
            </style>
        ''')
        
        # Header with title and language switcher
        with ui.row().classes('w-full items-center justify-between p-4 bg-gray-50 border-b'):
            ui.label(t('app_title')).classes('text-2xl font-bold')
            with ui.row().classes('gap-3 items-center'):
                ui.button('English', on_click=lambda: self.switch_language('en')).props('flat size=md').classes('text-base px-4 py-2')
                ui.button('中文', on_click=lambda: self.switch_language('zh')).props('flat size=md').classes('text-base px-4 py-2')
        
        # Main container with 2x3 grid layout
        with ui.column().classes('main-container gap-4'):
            # 2x3 grid: 1 2 3 / 4 5 6
            # 1: 操作模式, 2: 水印设置, 3+6: 选择文件（row-span-2）, 4+5: 文件输出（col-span-2）
            with ui.row().classes('three-column-grid gap-4'):
                # 1: 操作模式
                with ui.card().classes('card-compact fixed-card'):
                    ui.label(t('select_operation_mode')).classes('section-title')
                    self.mode_radio = ui.radio(
                        {
                            'pdf': t('process_pdf_with_watermark'),
                            'markdown': t('convert_md_to_pdf_with_watermark'),
                            'markdown_no_watermark': t('convert_md_to_pdf_no_watermark'),
                            'watermark_only': t('generate_watermark_only'),
                        },
                        value='pdf'
                    ).classes('w-full')

                # 2: 水印设置（always visible, grayed out when disabled）
                self.watermark_card = ui.card().classes('card-compact fixed-card')
                self.watermark_card_content = None
                self.watermark_title_label = None
                self.watermark_type_radio = None
                self.watermark_text_input = None
                self.watermark_image_path: Optional[str] = None  # 存储上传的水印图片路径
                self.add_date_checkbox = None
                self.watermark_image_upload = None

                def update_watermark_visibility(e=None):
                    """Update watermark visibility based on mode."""
                    mode = self.mode_radio.value
                    is_disabled = (mode == 'markdown_no_watermark')

                    if self.watermark_card_content:
                        if is_disabled:
                            # Gray out but keep visible
                            self.watermark_card_content.classes('w-full disabled-section')
                            if self.watermark_title_label:
                                self.watermark_title_label.classes('section-title disabled-label')
                        else:
                            # Show normally - remove disabled classes
                            self.watermark_card_content.classes(remove='disabled-section')
                            self.watermark_card_content.classes('w-full')
                            if self.watermark_title_label:
                                self.watermark_title_label.classes(remove='disabled-label')
                                self.watermark_title_label.classes('section-title')

                    # All controls are disabled via CSS when is_disabled is True
                    # The disabled-section class handles opacity and pointer-events

                with self.watermark_card:
                    self.watermark_card_content = ui.column().classes('w-full')
                    with self.watermark_card_content:
                        self.watermark_title_label = ui.label(t('watermark_type_title')).classes('section-title')
                        self.watermark_type_radio = ui.radio(
                            {
                                'text': t('text_watermark_recommended'),
                                'image': t('image_watermark'),
                            },
                            value='text'
                        ).classes('w-full mb-3').props('inline')

                        # Text watermark config
                        with ui.column().bind_visibility_from(self.watermark_type_radio, 'value', lambda v: v == 'text'):
                            self.watermark_text_input = ui.input(
                                label=t('enter_watermark_text'),
                                placeholder=t('enter_watermark_text_placeholder'),
                                value='Watermark'
                            ).classes('w-full')

                            self.add_date_checkbox = ui.checkbox(
                                t('add_date'),
                                value=True
                            ).classes('mt-2')

                        # Image watermark config
                        image_watermark_column = ui.column().classes('w-full').bind_visibility_from(self.watermark_type_radio, 'value', lambda v: v == 'image')
                        with image_watermark_column:
                            # 只保留上传组件，使用与"选择文件"相同的设置
                            self.watermark_image_upload = ui.upload(
                                label=t('upload_watermark_image'),
                                on_upload=self.handle_watermark_image_upload,
                                auto_upload=True
                            ).classes('w-full')

                # 初始化水印区域可见性
                update_watermark_visibility()
                self.mode_radio.on('update:model-value', lambda e: update_watermark_visibility(e))

                # 3+6: 选择文件（右侧整列，row-span-2）
                with ui.card().classes('card-compact fixed-card row-span-2 file-selection-tall'):
                    self.file_selection_title_label = ui.label(t('select_files')).classes('section-title')

                    # File selection container for enabling/disabling
                    self.file_selection_container = ui.column().classes('w-full h-full justify-between')
                    with self.file_selection_container:
                        self.file_upload_widget = ui.upload(
                            label=t('auto_upload_hint'),
                            on_upload=self.handle_file_upload,
                            multiple=True,
                            auto_upload=True
                        ).classes('w-full')

                        # Display uploaded files
                        self.uploaded_files_label = ui.label('').classes('mt-2 text-sm')

                        # Markdown options container (always takes space)
                        self.markdown_options_container = ui.column().classes('w-full mt-3 markdown-options-container')
                        with self.markdown_options_container:
                            with ui.row().classes('w-full gap-4'):
                                self.filter_front_matter_checkbox = ui.checkbox(
                                    t('filter_docsy_front_matter'),
                                    value=True,
                                )

                                self.rename_by_title_checkbox = ui.checkbox(
                                    t('rename_pdf_by_h1_title'),
                                    value=False,
                                )

                        # “开始处理”按钮：固定在选择文件卡片底部，居中显示
                        with ui.row().classes('w-full justify-center mt-auto pt-4 border-t'):
                            self.process_button = ui.button(
                                t('start_processing'),
                                on_click=self.process_files,
                                color='primary',
                            ).classes('text-lg px-6')

                    # Enable/disable file selection and markdown options based on mode
                    def update_file_selection_visibility(e=None):
                        """Update file selection and markdown options visibility based on mode."""
                        mode = self.mode_radio.value
                        # File upload is needed for all modes except watermark_only
                        file_upload_needed = (mode != 'watermark_only')
                        # Markdown options are only needed for markdown modes
                        markdown_options_needed = mode in ['markdown', 'markdown_no_watermark']

                        # Update file selection visibility
                        if file_upload_needed:
                            # Remove disabled style and show normally
                            self.file_selection_container.classes(remove='disabled-section')
                            self.file_selection_container.classes('w-full')
                            if self.file_selection_title_label:
                                self.file_selection_title_label.classes(remove='disabled-label')
                                self.file_selection_title_label.classes('section-title')
                        else:
                            # Add disabled-section class
                            self.file_selection_container.classes('w-full disabled-section')
                            if self.file_selection_title_label:
                                self.file_selection_title_label.classes('section-title disabled-label')

                        # Update markdown options visibility
                        if markdown_options_needed:
                            # Remove disabled style and show normally
                            self.markdown_options_container.classes(remove='disabled-section')
                            self.markdown_options_container.classes('w-full mt-3 markdown-options-container')
                        else:
                            # Add disabled-section class
                            self.markdown_options_container.classes('w-full mt-3 markdown-options-container disabled-section')

                    # Initialize once and update on mode change
                    update_file_selection_visibility()
                    self.mode_radio.on('update:model-value', lambda e: update_file_selection_visibility(e))

                # 4+5: 文件输出（占据第二行的前两列，col-span-2）
                with ui.card().classes('w-full card-compact fixed-card col-span-2'):
                    with ui.row().classes('w-full items-center justify-between mb-2'):
                        ui.label(t('processed_files')).classes('section-title mb-0')
                        self.clear_files_button = ui.button(
                            icon='delete',
                            on_click=self.clear_processed_files,
                        ).props('flat round').classes('text-gray-500')

                    self.file_list_container = ui.column().classes('w-full gap-2')
                    self.update_file_list()
            
            # 底部：保留一个轻微的间距（不再放按钮）
            ui.separator().classes('opacity-0')

    def switch_language(self, lang: str):
        """Switch language and reload page"""
        i18n.set_language(lang)
        self.current_language = lang
        ui.notify(t('language_switched', lang=lang))
        # Reload page to update all text
        ui.run_javascript('location.reload()')
    
    def update_file_list(self) -> None:
        """渲染“处理结果文件”列表的新实现"""
        if self.file_list_container is None:
            return

        # 清空容器
        self.file_list_container.clear()

        # 处理中时，隐藏列表内容，仅显示加载动画，并禁用清空按钮
        if self.is_processing:
            if self.clear_files_button is not None:
                self.clear_files_button.disable()

            with self.file_list_container:
                with ui.row().classes('w-full items-center justify-center py-4 gap-3 text-gray-500'):
                    ui.spinner(size='md', color='primary')
                    ui.label(t('processing'))
            return
        else:
            if self.clear_files_button is not None:
                self.clear_files_button.enable()

        # 没有任何文件时的空状态
        if not self.processed_files:
            with self.file_list_container:
                with ui.row().classes('items-center gap-2 text-gray-400'):
                    ui.icon('insert_drive_file')
                    ui.label(t('no_processed_files')).classes('text-sm')
            return

        # 有文件时，逐条渲染
        with self.file_list_container:
            for file_path in self.processed_files:
                self._render_processed_file_item(file_path)

    def _render_processed_file_item(self, file_path: Path) -> None:
        """渲染单个处理结果文件的行"""
        file_exists = file_path.exists()
        if file_exists:
            file_size = file_path.stat().st_size
            file_size_str = self.format_file_size(file_size)
        else:
            file_size_str = t('processing')

        with ui.row().classes('w-full items-center gap-3 p-3 border rounded-lg hover:bg-gray-50 transition-colors'):
            # 图标：已完成用绿色勾，其他用默认文档图标
            if file_exists:
                ui.icon('check_circle').classes('text-green-500')
            else:
                ui.icon('description').classes('text-gray-400')

            # 文件名和大小
            with ui.column().classes('flex-1 min-w-0'):
                ui.label(file_path.name).classes('font-medium truncate')
                ui.label(file_size_str).classes('text-xs text-gray-500')

            # 操作区
            with ui.row().classes('gap-1'):
                # 下载按钮：仅在文件已生成且当前不在全局处理中时可用
                download_btn = ui.button(
                    icon='download',
                    on_click=lambda f=file_path: self.download_file(f),
                ).props('flat round').classes('text-primary')
                if not file_exists or self.is_processing:
                    download_btn.disable()

                # 删除按钮：始终可用
                ui.button(
                    icon='delete',
                    on_click=lambda f=file_path: self.delete_file(f),
                ).props('flat round').classes('text-red-500')
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def download_file(self, file_path: Path) -> None:
        """下载单个处理结果文件"""
        if not file_path.exists():
            ui.notify(t('file_not_found'), type='negative')
            return

        ui.download(str(file_path))
        ui.notify(t('downloading', filename=file_path.name))

    def delete_file(self, file_path: Path) -> None:
        """删除单个处理结果文件并从列表中移除"""
        try:
            if file_path.exists():
                file_path.unlink()

            if file_path in self.processed_files:
                self.processed_files.remove(file_path)

            self.update_file_list()
            ui.notify(t('file_deleted', filename=file_path.name), type='positive')
        except Exception as e:
            ui.notify(t('delete_failed', error=str(e)), type='negative')

    def clear_processed_files(self) -> None:
        """清空所有处理结果文件及其在磁盘上的对应文件"""
        # 复制列表，避免迭代时修改原列表
        files_to_delete = list(self.processed_files)
        deleted_count = 0

        for file_path in files_to_delete:
            try:
                if file_path.exists():
                    file_path.unlink()
                deleted_count += 1
            except Exception:
                # 单个文件删除失败不影响整体流程
                continue

        self.processed_files.clear()
        self.update_file_list()

        if deleted_count > 0:
            ui.notify(t('all_files_cleared'), type='positive')
    
    async def handle_file_upload(self, e: UploadEventArguments):
        """Handle file upload"""
        # Newer NiceGUI passes file info via e.file
        file_obj = getattr(e, 'file', None)
        if file_obj is None:
            ui.notify(t('upload_failed'), type='negative')
            return

        filename = getattr(file_obj, 'name', 'uploaded_file')

        # Save uploaded file to a temporary directory
        upload_dir = Path('temp_uploads')
        upload_dir.mkdir(exist_ok=True)

        save_path = upload_dir / filename
        # SmallFileUpload.read() is async and returns bytes
        data = await file_obj.read()
        with open(save_path, 'wb') as f:
            f.write(data)

        self.uploaded_files[filename] = str(save_path)

        ui.notify(t('file_uploaded', filename=filename))
    
    async def handle_watermark_image_upload(self, e: UploadEventArguments):
        """Handle watermark image upload"""
        file_obj = getattr(e, 'file', None)
        if file_obj is None:
            ui.notify(t('watermark_upload_failed'), type='negative')
            return

        filename = getattr(file_obj, 'name', 'watermark')

        upload_dir = Path('temp_uploads')
        upload_dir.mkdir(exist_ok=True)
        
        save_path = upload_dir / f'watermark_{filename}'
        data = await file_obj.read()
        with open(save_path, 'wb') as f:
            f.write(data)
        
        # 保存上传的水印图片路径
        self.watermark_image_path = str(save_path)
        ui.notify(t('watermark_image_uploaded', filename=filename))
    
    
    def build_config(self) -> Dict[str, Any]:
        """Build configuration from UI inputs"""
        config = {
            'mode': self.mode_radio.value,
            'watermark_type': WatermarkConfig.WATERMARK_TYPE,  # Use default
            'opacity': WatermarkConfig.OPACITY,  # Use default
            'angle': WatermarkConfig.ANGLE,  # Use default
            'horizontal_boxes': WatermarkConfig.HORIZONTAL_BOXES,  # Use default
            'vertical_boxes': WatermarkConfig.VERTICAL_BOXES,  # Use default
            'image_scale': WatermarkConfig.IMAGE_SCALE,
            'input_dir': 'temp_uploads',
            'output_dir': 'output',
            'verbose': False,
            'filter_front_matter': self.filter_front_matter_checkbox.value,
            'rename_by_title': self.rename_by_title_checkbox.value,
        }
        
        # Add watermark type and content
        if config['mode'] != 'markdown_no_watermark' and config['mode'] != 'watermark_only':
            config['type'] = self.watermark_type_radio.value
            if config['type'] == 'text':
                config['text'] = self.watermark_text_input.value or 'Watermark'
                config['add_date'] = self.add_date_checkbox.value
            else:
                # 从上传的图片路径获取
                image_path = self.watermark_image_path
                if image_path and Path(image_path).exists():
                    config['image'] = image_path
                else:
                    raise ValueError(t('invalid_watermark_image_path'))
        elif config['mode'] == 'watermark_only':
            config['type'] = self.watermark_type_radio.value
            if config['type'] == 'text':
                config['text'] = self.watermark_text_input.value or 'Watermark'
                config['add_date'] = self.add_date_checkbox.value
            else:
                # 从上传的图片路径获取
                image_path = self.watermark_image_path
                if image_path and Path(image_path).exists():
                    config['image'] = image_path
                else:
                    raise ValueError(t('invalid_watermark_image_path'))
        
        # Apply defaults
        config.update({
            'font_size': WatermarkConfig.FONT_SIZE,
            'text_color': WatermarkConfig.TEXT_COLOR,
            'padding': WatermarkConfig.PADDING,
        })
        
        return config
    
    async def process_files(self):
        """Process files based on configuration (runs heavy work in background threads)"""
        try:
            # Validate uploaded files
            if not self.uploaded_files and self.mode_radio.value != 'watermark_only':
                ui.notify(t('please_upload_files_first'), type='negative')
                return
            
            # Build configuration
            try:
                self.config = self.build_config()
            except ValueError as e:
                ui.notify(str(e), type='negative')
                return

            # Build list of currently selected files (only those in upload list)
            selected_paths: List[Path] = [
                Path(p) for p in self.uploaded_files.values() if Path(p).is_file()
            ]
            selected_pdf_files: List[Path] = [
                p for p in selected_paths if p.suffix.lower() == '.pdf'
            ]
            selected_md_files: List[Path] = [
                p for p in selected_paths if p.suffix.lower() in ('.md', '.markdown')
            ]

            # Clean up stale files in temp_uploads: only keep currently uploaded files
            # so that "upload which, process which" is honored.
            upload_dir = Path('temp_uploads')
            if upload_dir.exists():
                # Set of paths for files uploaded in this session
                current_files = {Path(p).resolve() for p in self.uploaded_files.values()}
                for p in upload_dir.iterdir():
                    # Only consider regular files (skip subdirs if any)
                    if not p.is_file():
                        continue
                    # Keep files that are in current_files or are watermark images
                    if p.resolve() in current_files:
                        continue
                    if p.name.startswith('watermark_'):
                        continue
                    try:
                        p.unlink()
                    except Exception:
                        # Best-effort cleanup; ignore failures
                        pass
            
            # BEFORE processing: pre-populate file output list with expected output files
            expected_outputs: List[Path] = []
            output_dir = Path('output')
            if self.config['mode'] == 'pdf':
                if selected_pdf_files:
                    expected_outputs = [output_dir / p.name for p in selected_pdf_files]
                elif selected_md_files:
                    expected_outputs = [output_dir / f'{p.stem}.pdf' for p in selected_md_files]
            elif self.config['mode'] in ['markdown', 'markdown_no_watermark']:
                expected_outputs = [output_dir / f'{p.stem}.pdf' for p in selected_md_files]
            # watermark_only 模式没有文件输出列表
            if expected_outputs:
                self.processed_files = expected_outputs
                self.update_file_list()

            # 标记为处理中，并禁用按钮
            self.is_processing = True
            # Disable button while processing
            self.process_button.disable()
            # 点击后立即更新文件输出区域：展示加载动画，隐藏旧结果
            self.update_file_list()
            
            # Create output directory
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)
            
            # Process based on mode
            watermark_image: Optional[str] = None
            success = False
            output_files: List[Path] = []
            
            try:
                if self.config['mode'] == 'watermark_only':
                    watermark_image = setup_watermark_image(self.config)
                    if watermark_image:
                        ui.notify(t('watermark_generated_successfully'), type='positive')
                        success = True
                    else:
                        ui.notify(t('watermark_generation_failed'), type='negative')
                
                elif self.config['mode'] == 'markdown_no_watermark':
                    if not selected_md_files:
                        ui.notify(t('no_markdown_files_selected'), type='warning')
                        return
                    # Run markdown conversion in a worker thread to avoid Playwright sync API inside event loop
                    success, output_files = await asyncio.to_thread(
                        process_markdown_files,
                        'temp_uploads',
                        'output',
                        None,  # no watermark
                        self.config,
                        selected_md_files,
                        no_watermark=True,
                    )
                
                else:
                    # Setup watermark
                    watermark_image = setup_watermark_image(self.config)
                    if not watermark_image:
                        ui.notify(t('watermark_image_not_found'), type='negative')
                        return
                    
                    # Process files
                    if self.config['mode'] == 'pdf':
                        # Only process the currently selected files in temp_uploads
                        if selected_pdf_files:
                            # Offload PDF processing to worker thread (CPU/IO heavy)
                            success, output_files = await asyncio.to_thread(
                                process_pdf_files,
                                'temp_uploads',
                                'output',
                                watermark_image,
                                self.config.get('watermark_type', 'grid'),
                                selected_pdf_files,
                                horizontal_boxes=self.config.get('horizontal_boxes', 3),
                                vertical_boxes=self.config.get('vertical_boxes', 6),
                                angle=self.config.get('angle', 45),
                                opacity=self.config.get('opacity', 0.2),
                                image_scale=self.config.get('image_scale', 1.0),
                            )
                        elif selected_md_files:
                            # Fallback to markdown: only for selected markdown files
                            success, output_files = await asyncio.to_thread(
                                process_markdown_files,
                                'temp_uploads',
                                'output',
                                watermark_image,
                                self.config,
                                selected_md_files,
                            )
                        else:
                            ui.notify(t('no_files_found'), type='warning')
                            return
                    else:
                        # Markdown modes: only process selected markdown files
                        if not selected_md_files:
                            ui.notify(t('no_markdown_files_selected'), type='warning')
                            return
                        success, output_files = await asyncio.to_thread(
                            process_markdown_files,
                            'temp_uploads',
                            'output',
                            watermark_image,
                            self.config,
                            selected_md_files,
                        )
                    
                    # Cleanup generated watermark
                    if watermark_image and self.config['mode'] != 'watermark_only':
                        cleanup_generated_watermark(watermark_image, self.config)
                
                # Update processed files list
                if success and output_files:
                    self.processed_files = output_files
                    self.update_file_list()
                
                if success:
                    ui.notify(t('processing_successful'), type='positive')
                else:
                    ui.notify(t('processing_failed'), type='negative')
            
            except Exception as e:
                ui.notify(t('error', error=str(e)), type='negative')
                success = False
            
            finally:
                # 标记处理结束并刷新列表（此时存在的文件会显示下载按钮）
                self.is_processing = False
                self.update_file_list()
                self.process_button.enable()
        
        except Exception as e:
            ui.notify(t('configuration_error', error=str(e)), type='negative')
            self.process_button.enable()


@app.on_shutdown
async def cleanup_temp_uploads_on_shutdown() -> None:
    """Clean up temp_uploads directory when the app is shutting down."""
    upload_dir = Path('temp_uploads')
    if not upload_dir.exists():
        return
    for p in upload_dir.iterdir():
        if p.is_file():
            try:
                p.unlink()
            except Exception:
                # Best-effort cleanup only
                pass
