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
from main import (
    _setup_watermark_image,
    _process_pdf_files,
    _process_markdown_files,
    _process_markdown_files_no_watermark,
    get_pdf_files,
    get_md_files,
    _cleanup_generated_watermark,
)


class WebUI:
    """Web UI for PDF watermark tool"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.uploaded_files: Dict[str, str] = {}  # filename -> filepath
        self.watermark_image_path: Optional[str] = None
        self.processing_status = ""
        self.current_language = i18n.get_current_language()
        # Per-file progress bars: filename -> progress bar
        self.file_progress_bars: Dict[str, "ui.linear_progress"] = {}
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
        
        # Language switcher
        with ui.row().classes('w-full justify-end p-2'):
            ui.button('English', on_click=lambda: self.switch_language('en')).classes('text-xs')
            ui.button('中文', on_click=lambda: self.switch_language('zh')).classes('text-xs')
        
        # Main container
        with ui.column().classes('w-full max-w-4xl mx-auto p-6 gap-4'):
            # Title
            ui.label(t('app_title')).classes('text-3xl font-bold mb-4')
            
            # Operation mode selection
            with ui.card().classes('w-full'):
                ui.label(t('select_operation_mode')).classes('text-xl font-semibold mb-2')
                with ui.row().classes('w-full gap-2'):
                    self.mode_radio = ui.radio(
                        {
                            'pdf': t('process_pdf_with_watermark'),
                            'markdown': t('convert_md_to_pdf_with_watermark'),
                            'markdown_no_watermark': t('convert_md_to_pdf_no_watermark'),
                            'watermark_only': t('generate_watermark_only'),
                        },
                        value='pdf'
                    ).classes('w-full')
            
            # File upload section
            with ui.card().classes('w-full'):
                ui.label('选择文件 / Select Files').classes('text-xl font-semibold mb-2')
                # 选择文件后自动上传，更符合当前需求
                ui.upload(
                    label='选择文件后自动上传 / Automatically upload after selecting files',
                    on_upload=self.handle_file_upload,
                    multiple=True,
                    auto_upload=True
                ).classes('w-full')
                
                # Display uploaded files
                self.uploaded_files_label = ui.label('').classes('mt-2')
                self.update_uploaded_files_display()

                # Container for per-file progress bars
                self.file_progress_container = ui.column().classes('w-full mt-2 gap-1')
                
                # Docsy front matter filter option (only show for markdown modes)
                # 默认勾选，用户可以取消
                self.filter_front_matter_checkbox = ui.checkbox(
                    t('filter_docsy_front_matter'),
                    value=True,
                ).classes('mt-4')
                
                # Rename PDF by H1 title option (only show for markdown modes)
                self.rename_by_title_checkbox = ui.checkbox(
                    t('rename_pdf_by_h1_title'),
                    value=False,
                ).classes('mt-2')
                
                # Show/hide filter checkbox based on mode
                def update_filter_visibility(e=None):
                    mode = self.mode_radio.value
                    # Show filter option for markdown conversion modes
                    show_filter = mode in ['markdown', 'markdown_no_watermark']
                    self.filter_front_matter_checkbox.set_visibility(show_filter)
                    self.rename_by_title_checkbox.set_visibility(show_filter)
                
                # Set initial visibility
                update_filter_visibility()
                # Update on mode change
                self.mode_radio.on('update:model-value', lambda e: update_filter_visibility())
            
            # Watermark configuration (only for modes that need watermark)
            self.watermark_card = ui.card().classes('w-full')
            
            # Show/hide watermark card based on mode
            def update_watermark_visibility(e=None):
                mode = self.mode_radio.value
                self.watermark_card.set_visibility(mode != 'markdown_no_watermark')
            
            # Set initial visibility
            update_watermark_visibility()
            # Update on mode change
            self.mode_radio.on('update:model-value', lambda e: update_watermark_visibility())
            
            with self.watermark_card:
                ui.label(t('watermark_type_title')).classes('text-xl font-semibold mb-2')
                self.watermark_type_radio = ui.radio(
                    {
                        'text': t('text_watermark_recommended'),
                        'image': t('image_watermark'),
                    },
                    value='text'
                ).classes('w-full mb-4')
                
                # Text watermark config
                with ui.column().bind_visibility_from(self.watermark_type_radio, 'value', lambda v: v == 'text'):
                    ui.label(t('enter_watermark_text')).classes('font-semibold')
                    self.watermark_text_input = ui.input(
                        label='',
                        placeholder='输入水印文本 / Enter watermark text',
                        value='Watermark'
                    ).classes('w-full')
                    
                    self.add_date_checkbox = ui.checkbox(
                        t('add_date_to_watermark').replace('? (y/n, default: y):', ''),
                        value=True
                    ).classes('mt-2')
                
                # Image watermark config
                with ui.column().bind_visibility_from(self.watermark_type_radio, 'value', lambda v: v == 'image'):
                    ui.label(t('enter_watermark_image_path')).classes('font-semibold')
                    self.watermark_image_input = ui.input(
                        label='',
                        placeholder='输入图片路径 / Enter image path',
                    ).classes('w-full')
                    
                    ui.upload(
                        label='或上传水印图片 / Or upload watermark image',
                        on_upload=self.handle_watermark_image_upload,
                        auto_upload=True
                    ).classes('w-full mt-2')
            
            # Advanced settings (collapsible)
            with ui.expansion('高级设置 / Advanced Settings').classes('w-full'):
                with ui.column().classes('gap-2'):
                    ui.label('水印类型 / Watermark Type')
                    self.watermark_style_select = ui.select(
                        ['grid', 'insert'],
                        value='grid',
                        label=''
                    ).classes('w-full')
                    
                    ui.label('透明度 / Opacity')
                    self.opacity_slider = ui.slider(
                        min=0.0, max=1.0, step=0.05, value=0.2
                    ).classes('w-full')
                    self.opacity_label = ui.label('0.2')
                    self.opacity_slider.on('update:model-value', 
                        lambda e: self.opacity_label.set_text(f'{e.args:.2f}'))
                    
                    ui.label('角度 / Angle')
                    self.angle_slider = ui.slider(
                        min=0, max=360, step=5, value=45
                    ).classes('w-full')
                    self.angle_label = ui.label('45°')
                    self.angle_slider.on('update:model-value', 
                        lambda e: self.angle_label.set_text(f'{e.args}°'))
                    
                    ui.label('水平网格数 / Horizontal Boxes')
                    self.horizontal_boxes_input = ui.number(
                        label='', value=3, min=1, max=10
                    ).classes('w-full')
                    
                    ui.label('垂直网格数 / Vertical Boxes')
                    self.vertical_boxes_input = ui.number(
                        label='', value=6, min=1, max=20
                    ).classes('w-full')
            
            # Process button
            self.process_button = ui.button(
                '开始处理 / Start Processing',
                on_click=self.process_files,
                color='primary'
            ).classes('w-full mt-4 text-lg')
            
            # Status display
            self.status_label = ui.label('').classes('w-full mt-4')
            self.status_label.visible = False
            
            # Progress bar
            self.progress_bar = ui.linear_progress(value=0).classes('w-full mt-2')
            self.progress_bar.visible = False
    
    def switch_language(self, lang: str):
        """Switch language"""
        i18n.set_language(lang)
        self.current_language = lang
        ui.notify(f'Language switched to {lang}')
        # Note: Full page reload would require JavaScript, for now just update the language
        # The next interaction will use the new language
    
    async def handle_file_upload(self, e: UploadEventArguments):
        """Handle file upload"""
        # Newer NiceGUI passes file info via e.file
        file_obj = getattr(e, 'file', None)
        if file_obj is None:
            ui.notify('上传失败：无法获取文件信息 / Upload failed: no file info', type='negative')
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
        self.update_uploaded_files_display()

        # Create or reset per-file progress bar for this file
        # Show 0 initially; will move to 1.0 when processing is done
        bar = self.file_progress_bars.get(filename)
        if bar is None:
            with self.file_progress_container:
                row = ui.row().classes('w-full items-center gap-2')
                ui.label(filename).classes('flex-1 text-sm truncate')
                bar = ui.linear_progress(value=0.0).classes('w-1/3')
            self.file_progress_bars[filename] = bar
        else:
            bar.set_value(0.0)

        ui.notify(f'文件已上传: {filename} / File uploaded: {filename}')
    
    async def handle_watermark_image_upload(self, e: UploadEventArguments):
        """Handle watermark image upload"""
        file_obj = getattr(e, 'file', None)
        if file_obj is None:
            ui.notify('水印图片上传失败：无法获取文件信息 / Watermark upload failed: no file info', type='negative')
            return

        filename = getattr(file_obj, 'name', 'watermark')

        upload_dir = Path('temp_uploads')
        upload_dir.mkdir(exist_ok=True)
        
        save_path = upload_dir / f'watermark_{filename}'
        data = await file_obj.read()
        with open(save_path, 'wb') as f:
            f.write(data)
        
        self.watermark_image_input.set_value(str(save_path))
        ui.notify(f'水印图片已上传 / Watermark image uploaded: {filename}')
    
    def update_uploaded_files_display(self):
        """Update uploaded files display"""
        if self.uploaded_files:
            files_list = '\n'.join([f'• {name}' for name in self.uploaded_files.keys()])
            self.uploaded_files_label.set_text(f'已上传文件 / Uploaded files:\n{files_list}')
        else:
            self.uploaded_files_label.set_text('未上传文件 / No files uploaded')
    
    def build_config(self) -> Dict[str, Any]:
        """Build configuration from UI inputs"""
        config = {
            'mode': self.mode_radio.value,
            'watermark_type': self.watermark_style_select.value,
            'opacity': self.opacity_slider.value,
            'angle': self.angle_slider.value,
            'horizontal_boxes': int(self.horizontal_boxes_input.value),
            'vertical_boxes': int(self.vertical_boxes_input.value),
            'image_scale': 1.0,
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
                image_path = self.watermark_image_input.value
                if image_path and Path(image_path).exists():
                    config['image'] = image_path
                else:
                    raise ValueError('水印图片路径无效 / Invalid watermark image path')
        elif config['mode'] == 'watermark_only':
            config['type'] = self.watermark_type_radio.value
            if config['type'] == 'text':
                config['text'] = self.watermark_text_input.value or 'Watermark'
                config['add_date'] = self.add_date_checkbox.value
            else:
                image_path = self.watermark_image_input.value
                if image_path and Path(image_path).exists():
                    config['image'] = image_path
                else:
                    raise ValueError('水印图片路径无效 / Invalid watermark image path')
        
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
                ui.notify('请先上传文件 / Please upload files first', type='negative')
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
            
            # Show progress
            self.process_button.disable()
            self.progress_bar.visible = True
            self.progress_bar.set_value(0.1)
            self.status_label.visible = True
            self.status_label.set_text('正在处理... / Processing...')
            # Reset per-file progress bars to 0 before starting
            for bar in self.file_progress_bars.values():
                bar.set_value(0.0)
            
            # Create output directory
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)
            
            # Process based on mode
            watermark_image: Optional[str] = None
            success = False
            
            try:
                if self.config['mode'] == 'watermark_only':
                    self.status_label.set_text(t('start_generating_watermark'))
                    watermark_image = _setup_watermark_image(self.config)
                    if watermark_image:
                        self.status_label.set_text(f'{t("watermark_image_generated")} {watermark_image}')
                        ui.notify('水印生成成功 / Watermark generated successfully', type='positive')
                        success = True
                    else:
                        self.status_label.set_text('✗ ' + t('watermark_image_not_found'))
                        ui.notify('水印生成失败 / Watermark generation failed', type='negative')
                
                elif self.config['mode'] == 'markdown_no_watermark':
                    self.status_label.set_text(t('start_converting_md_no_watermark'))
                    if not selected_md_files:
                        self.status_label.set_text('未找到可处理的Markdown文件 / No Markdown files selected')
                        ui.notify('未找到可处理的Markdown文件 / No Markdown files selected', type='warning')
                        return
                    # Run markdown conversion in a worker thread to avoid Playwright sync API inside event loop
                    success = await asyncio.to_thread(
                        _process_markdown_files_no_watermark,
                        'temp_uploads',
                        'output',
                        self.config,
                        selected_md_files,
                    )
                
                else:
                    # Setup watermark
                    self.progress_bar.set_value(0.2)
                    watermark_image = _setup_watermark_image(self.config)
                    if not watermark_image:
                        self.status_label.set_text('✗ ' + t('watermark_image_not_found'))
                        ui.notify('水印图片未找到 / Watermark image not found', type='negative')
                        return
                    
                    self.progress_bar.set_value(0.4)
                    
                    # Process files
                    if self.config['mode'] == 'pdf':
                        # Only process the currently selected files in temp_uploads
                        if selected_pdf_files:
                            self.status_label.set_text('处理PDF文件... / Processing PDF files...')
                            # Offload PDF processing to worker thread (CPU/IO heavy)
                            success = await asyncio.to_thread(
                                _process_pdf_files,
                                'temp_uploads',
                                'output',
                                watermark_image,
                                self.config,
                                selected_pdf_files,
                            )
                        elif selected_md_files:
                            # Fallback to markdown: only for selected markdown files
                            self.status_label.set_text('处理Markdown文件... / Processing Markdown files...')
                            success = await asyncio.to_thread(
                                _process_markdown_files,
                                'temp_uploads',
                                'output',
                                watermark_image,
                                self.config,
                                selected_md_files,
                            )
                        else:
                            self.status_label.set_text('未找到可处理的文件 / No files found')
                            ui.notify('未找到可处理的文件 / No files found', type='warning')
                            return
                    else:
                        # Markdown modes: only process selected markdown files
                        self.status_label.set_text('处理Markdown文件... / Processing Markdown files...')
                        if not selected_md_files:
                            self.status_label.set_text('未找到可处理的Markdown文件 / No Markdown files selected')
                            ui.notify('未找到可处理的Markdown文件 / No Markdown files selected', type='warning')
                            return
                        success = await asyncio.to_thread(
                            _process_markdown_files,
                            'temp_uploads',
                            'output',
                            watermark_image,
                            self.config,
                            selected_md_files,
                        )
                    
                    self.progress_bar.set_value(0.9)
                    
                    # Cleanup generated watermark
                    if watermark_image and self.config['mode'] != 'watermark_only':
                        _cleanup_generated_watermark(watermark_image, self.config)
                
                self.progress_bar.set_value(1.0)
                # Update per-file progress bars at the end: mark all as completed or failed
                final_value = 1.0 if success else 0.0
                for bar in self.file_progress_bars.values():
                    bar.set_value(final_value)
                
                if success:
                    self.status_label.set_text('处理完成！/ Processing completed!')
                    ui.notify('处理成功 / Processing successful', type='positive')
                else:
                    self.status_label.set_text('处理失败 / Processing failed')
                    ui.notify('处理失败 / Processing failed', type='negative')
            
            except Exception as e:
                self.status_label.set_text(f'错误 / Error: {str(e)}')
                ui.notify(f'错误 / Error: {str(e)}', type='negative')
                success = False
            
            finally:
                self.process_button.enable()
                # Reset progress after 3 seconds
                def reset_progress():
                    self.progress_bar.set_value(0)
                ui.timer(3.0, reset_progress, once=True)
        
        except Exception as e:
            self.status_label.set_text(f'配置错误 / Configuration error: {str(e)}')
            ui.notify(f'配置错误 / Configuration error: {str(e)}', type='negative')
            self.process_button.enable()
            self.progress_bar.visible = False


def run_web_ui(port: int = 8080, show: bool = True, host: str = '0.0.0.0'):
    """Run the web UI
    
    Note: This function is kept for backward compatibility with main.py --web option.
    For new code, prefer using start_webui.py directly.
    
    Args:
        port: Web server port (default: 8080)
        show: Whether to automatically open browser (default: True)
        host: Host to bind to (default: '0.0.0.0')
    """
    web_ui = WebUI()
    web_ui.build_ui()
    # Note: ui.run() must be called at module level, not inside a function
    # This function is mainly for backward compatibility
    ui.run(port=port, show=show, title=t('app_title'), host=host)


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
