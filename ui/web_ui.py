"""
NiceGUI web interface for PDF watermark tool.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from nicegui import ui, app
from nicegui.events import UploadEventArguments

from i18n import t, i18n
from config import WatermarkConfig
from core import setup_watermark_image
from core.pdf_processor import add_watermark_to_file
from core.markdown_processor import extract_h1_title


def cleanup_generated_watermark(watermark_image: Optional[str], config: dict) -> None:
    if not watermark_image:
        return
    
    watermark_path = Path(watermark_image)
    
    if watermark_path.exists() and watermark_path.parent.name == "watermarks":
        if config.get("type") == "text" or (config.get("type") != "image" and not config.get("image")):
            try:
                watermark_path.unlink()
                print(f"✓ Cleaned up generated watermark: {watermark_image}")
            except Exception as e:
                print(f"⚠ Warning: Failed to delete watermark file {watermark_image}: {e}")


class WebUI:
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.uploaded_files: Dict[str, str] = {}
        self.watermark_image_path: Optional[str] = None
        self.processing_status = ""
        self.current_language = i18n.get_current_language()
        self.is_processing: bool = False
        self.processed_files: List[Path] = []
        self.file_processing_status: Dict[Path, str] = {}  # 'pending', 'processing', 'completed'
        self.processing_progress: tuple[int, int] = (0, 0)  # (completed, total)
        self.file_list_container: Optional[ui.column] = None
        self.clear_files_button: Optional[ui.button] = None
        self.progress_label: Optional[ui.label] = None
        
        temp_dir = Path('temp_uploads')
        temp_dir.mkdir(exist_ok=True)
        for p in temp_dir.iterdir():
            if p.is_file():
                try:
                    p.unlink()
                except Exception:
                    pass
        
    def build_ui(self):
        ui.page_title(t('app_title'))
        
        ui.add_head_html('''
            <style>
                .main-container { max-width: 1000px; margin: 0 auto; padding: 0.5rem 0.75rem; }
                .three-column-grid { display: grid !important; grid-template-columns: 1fr 1fr 1fr !important; grid-template-rows: 320px auto !important; gap: 0.75rem !important; width: 100% !important; }
                .row-span-2 { grid-row: 1 / 3 !important; grid-column: 3 !important; height: calc(320px + 0.75rem + 320px) !important; }
                .col-span-2 { grid-column: 1 / 3 !important; grid-row: 2 !important; }
                @media (max-width: 1024px) { .three-column-grid { grid-template-columns: 1fr; } }
                .card-compact { padding: 1rem; min-height: 320px; display: flex; flex-direction: column; }
                .section-title { font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: #374151; }
                .fixed-card { width: 100%; min-height: 320px; }
                .watermark-card-flexible { width: 100%; min-height: 320px; min-width: 0; flex: 1 1 auto; }
                .file-selection-tall { min-height: calc(320px + 0.75rem + 320px) !important; }
                .file-selection-dynamic { min-height: calc(320px + 0.75rem + 320px) !important; height: auto !important; flex: 1 1 auto; }
                .output-card-dynamic { min-height: 320px; height: auto !important; flex: 1 1 auto; }
                .markdown-options-container { min-height: 48px; display: flex; align-items: flex-start; }
                .disabled-section { opacity: 0.5; pointer-events: none; position: relative; }
                .disabled-section * { cursor: not-allowed; }
                .disabled-label { color: #9ca3af !important; }
                .mode-card-content { display: flex; flex-direction: column; gap: 1rem; align-items: flex-start; }
                .mode-radio-group { display: flex; flex-direction: column; gap: 0.75rem; width: 100%; }
                .mode-radio-group .q-radio { white-space: nowrap; }
                .watermark-radio-disabled { opacity: 0.5 !important; cursor: not-allowed !important; pointer-events: none !important; }
                .watermark-card-content { display: flex; flex-direction: column; gap: 1rem; align-items: flex-start; width: 100%; }
            </style>
        ''')
        
        with ui.row().classes('w-full items-center justify-between p-4 bg-gray-50 border-b'):
            ui.label(t('app_title')).classes('text-2xl font-bold')
            with ui.row().classes('gap-3 items-center'):
                ui.button('English', on_click=lambda: self.switch_language('en')).props('flat size=md').classes('text-base px-4 py-2')
                ui.button('中文', on_click=lambda: self.switch_language('zh')).props('flat size=md').classes('text-base px-4 py-2')
        
        with ui.column().classes('main-container gap-4'):
            with ui.row().classes('three-column-grid gap-4'):
                with ui.card().classes('card-compact fixed-card'):
                    ui.label(t('select_operation_mode')).classes('section-title')
                    with ui.column().classes('mode-card-content'):
                        self.mode_radio = ui.radio(
                            {
                                'pdf': t('process_pdf_with_watermark'),
                                'markdown': t('convert_md_to_pdf_with_watermark'),
                                'watermark_only': t('generate_watermark_only'),
                            },
                            value='pdf'
                        ).classes('mode-radio-group')

                self.watermark_card = ui.card().classes('card-compact fixed-card')
                self.watermark_card_content = None
                self.watermark_title_label = None
                self.watermark_type_radio = None
                self.watermark_text_input = None
                self.add_date_checkbox = None
                self.watermark_image_upload = None

                with self.watermark_card:
                    self.watermark_card_content = ui.column().classes('watermark-card-content')
                    with self.watermark_card_content:
                        self.watermark_title_label = ui.label(t('watermark_type_title')).classes('section-title')
                        
                        # 现代化布局：使用简单的column布局
                        self.watermark_type_radio = ui.radio(
                            {
                                'text': t('text_watermark_recommended'),
                                'image': t('image_watermark'),
                            },
                            value='text'
                        ).props('inline').classes('w-full')
                            
                        
                        # 文本水印输入框和日期选项
                        with ui.column().bind_visibility_from(self.watermark_type_radio, 'value', lambda v: v == 'text').classes('w-full gap-2'):
                            self.watermark_text_input = ui.input(
                                label=t('enter_watermark_text'),
                                placeholder=t('enter_watermark_text_placeholder'),
                                value='Watermark'
                            ).classes('w-full')
                            
                            self.add_date_checkbox = ui.checkbox(
                                t('add_date'),
                                value=True
                            ).classes('w-full')
                        
                        # 图片水印上传
                        with ui.column().bind_visibility_from(self.watermark_type_radio, 'value', lambda v: v == 'image').classes('w-full'):
                            self.watermark_image_upload = ui.upload(
                                label=t('upload_watermark_image'),
                                on_upload=self.handle_watermark_image_upload,
                                auto_upload=True
                            ).classes('w-full')
                        
                        # 生成按钮 - 在生成图片水印模式时显示
                        with ui.row().classes('w-full justify-center') as generate_button_container:
                            self.generate_watermark_button = ui.button(
                                t('generate_watermark'),
                                on_click=self.generate_watermark_only,
                                color='primary',
                            ).classes('text-lg px-6')
                            
                            # 初始隐藏生成按钮
                            generate_button_container.set_visibility(False)
                            self.generate_watermark_button_container = generate_button_container

                def update_watermark_mode_behavior(e=None, skip_js=False):
                    mode = self.mode_radio.value
                    is_watermark_only = (mode == 'watermark_only')

                    # Show/hide generate watermark button
                    if self.generate_watermark_button_container:
                        self.generate_watermark_button_container.set_visibility(is_watermark_only)

                    # Update watermark type options based on mode
                    if is_watermark_only:
                        # In watermark_only mode, force text watermark and disable image option
                        self.watermark_type_radio.value = 'text'
                        # Disable image option via JavaScript (only when not skipping JS)
                        if not skip_js:
                            def disable_image_option():
                                ui.run_javascript(f'''
                                    (function() {{
                                        // Find all radio div elements with aria-label "图片水印"
                                        const imageRadios = document.querySelectorAll('div[role="radio"][aria-label="图片水印"]');
                                        for (const radio of imageRadios) {{
                                            // Check if this radio belongs to watermark type (not operation mode)
                                            const radioGroup = radio.closest('.q-option-group');
                                            if (radioGroup && radioGroup.querySelector('div[aria-label="文本水印"]')) {{
                                                // This is the watermark type radio group
                                                radio.style.opacity = '0.5';
                                                radio.style.cursor = 'not-allowed';
                                                radio.style.pointerEvents = 'none';
                                                radio.setAttribute('aria-disabled', 'true');
                                                // Also disable the input if it exists
                                                const input = radio.querySelector('input[type="radio"]');
                                                if (input) {{
                                                    input.disabled = true;
                                                }}
                                                break;
                                            }}
                                        }}
                                    }})();
                                ''')
                            # Use timer to ensure DOM is ready
                            ui.timer(0.1, disable_image_option, once=True)
                    else:
                        # In other modes, enable image option (only when not skipping JS)
                        if not skip_js:
                            def enable_image_option():
                                ui.run_javascript(f'''
                                    (function() {{
                                        // Find all radio div elements with aria-label "图片水印"
                                        const imageRadios = document.querySelectorAll('div[role="radio"][aria-label="图片水印"]');
                                        for (const radio of imageRadios) {{
                                            // Check if this radio belongs to watermark type (not operation mode)
                                            const radioGroup = radio.closest('.q-option-group');
                                            if (radioGroup && radioGroup.querySelector('div[aria-label="文本水印"]')) {{
                                                // This is the watermark type radio group
                                                radio.style.opacity = '1';
                                                radio.style.cursor = 'pointer';
                                                radio.style.pointerEvents = 'auto';
                                                radio.removeAttribute('aria-disabled');
                                                // Also enable the input if it exists
                                                const input = radio.querySelector('input[type="radio"]');
                                                if (input) {{
                                                    input.disabled = false;
                                                }}
                                                break;
                                            }}
                                        }}
                                    }})();
                                ''')
                            # Use timer to ensure DOM is ready
                            ui.timer(0.1, enable_image_option, once=True)

                # Initialize without JavaScript (skip_js=True)
                update_watermark_mode_behavior(skip_js=True)
                self.mode_radio.on('update:model-value', lambda e: update_watermark_mode_behavior(e))

                with ui.card().classes('card-compact file-selection-dynamic row-span-2'):
                    self.file_selection_title_label = ui.label(t('select_files')).classes('section-title')

                    self.file_selection_container = ui.column().classes('w-full h-full justify-between')
                    with self.file_selection_container:
                        # Create upload widget wrapper to make it easier to replace
                        self.upload_widget_container = ui.element('div').classes('w-full')
                        with self.upload_widget_container:
                            self.file_upload_widget = ui.upload(
                                label=t('auto_upload_hint'),
                                on_upload=self.handle_file_upload,
                                multiple=True,
                                auto_upload=True
                            ).classes('w-full')

                        self.uploaded_files_label = ui.label('').classes('mt-2 text-sm')

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

                        with ui.row().classes('w-full justify-center mt-auto pt-4'):
                            self.process_button = ui.button(
                                t('start_processing'),
                                on_click=self.process_files,
                                color='primary',
                            ).classes('text-lg px-6')

                    def update_file_selection_visibility(e=None):
                        mode = self.mode_radio.value
                        file_upload_needed = (mode != 'watermark_only')
                        markdown_options_needed = mode == 'markdown'

                        if file_upload_needed:
                            self.file_selection_container.classes(remove='disabled-section')
                            self.file_selection_container.classes('w-full')
                            if self.file_selection_title_label:
                                self.file_selection_title_label.classes(remove='disabled-label')
                                self.file_selection_title_label.classes('section-title')
                        else:
                            self.file_selection_container.classes('w-full disabled-section')
                            if self.file_selection_title_label:
                                self.file_selection_title_label.classes('section-title disabled-label')

                        if markdown_options_needed:
                            self.markdown_options_container.classes(remove='disabled-section')
                            self.markdown_options_container.classes('w-full mt-3 markdown-options-container')
                        else:
                            self.markdown_options_container.classes('w-full mt-3 markdown-options-container disabled-section')

                    update_file_selection_visibility()
                    self.mode_radio.on('update:model-value', lambda e: update_file_selection_visibility(e))

                with ui.card().classes('w-full card-compact output-card-dynamic col-span-2 py-0'):
                    with ui.row().classes('w-full items-center justify-between pb-0 mb-0'): # Header row: explicit zero padding/margin bottom
                        ui.label(t('processed_files')).classes('section-title mb-0 mr-4') # Title, added mr-4 for spacing
                        self.progress_label = ui.label('').classes('text-sm grow text-center -mt-1') # Changed -mt-px to -mt-1
                        self.clear_files_button = ui.button(
                            icon='delete',
                            on_click=self.clear_processed_files,
                        ).props('flat round').classes('text-gray-500')

                    self.file_list_container = ui.column().classes('w-full gap-1 mt-[-10px] pt-0') # File list container: explicit zero margin/padding top, negative margin for aggressive compaction
                    self.load_existing_output_files()
                    self.update_file_list()
            
            ui.separator().classes('opacity-0')

    def switch_language(self, lang: str):
        i18n.set_language(lang)
        self.current_language = lang
        ui.notify(t('language_switched', lang=lang), position='top')
        ui.run_javascript('location.reload()')
    
    def update_file_list(self) -> None:
        if self.file_list_container is None:
            return

        self.file_list_container.clear()

        # Update button states
        if self.clear_files_button is not None:
            self.clear_files_button.enable() if not self.is_processing else self.clear_files_button.disable()

        # Update progress in header
        if self.progress_label is not None:
            if self.is_processing and self.processing_progress[1] > 0:
                # Use current batch progress tracking
                completed_count, total_count = self.processing_progress
                progress_percentage = int((completed_count / total_count) * 100)
                self.progress_label.text = f'{completed_count}/{total_count} {progress_percentage}%'
                self.progress_label.classes('text-sm text-green-600 font-medium')
            elif len(self.processed_files) > 0:
                 # Show total count when not processing
                 total_count = len(self.processed_files)
                 self.progress_label.text = t('total_files_count', count=total_count)
                 self.progress_label.classes('text-sm text-green-600')
            else:
                self.progress_label.text = ''

        if not self.processed_files:
            with self.file_list_container:
                with ui.row().classes('items-center gap-2 text-gray-400'):
                    ui.icon('insert_drive_file')
                    ui.label(t('no_processed_files')).classes('text-sm')
            return

        with self.file_list_container:
            for file_path in self.processed_files:
                self._render_processed_file_item(file_path)

    def _render_processed_file_item(self, file_path: Path) -> None:
        status = self.file_processing_status.get(file_path, 'completed')
        file_exists = file_path.exists()

        # Determine file size display
        if file_exists:
            file_size = file_path.stat().st_size
            file_size_str = self.format_file_size(file_size)
        else:
            file_size_str = t('processing') if status == 'processing' else ''

        with ui.row().classes('w-full items-center gap-3 p-3 border rounded-lg hover:bg-gray-100 transition-colors'):
            # Status icon
            if status == 'completed' and file_exists:
                ui.icon('check_circle').props('size=sm').classes('text-green-500')
            elif status == 'processing':
                ui.spinner(size='sm', color='primary')
            elif status == 'pending':
                ui.spinner(size='sm', color='primary')
            elif status == 'error':
                ui.icon('refresh').classes('text-orange-500 cursor-pointer')  # 可点击的重试图标
            else:
                # Default to processing spinner for unknown states
                ui.spinner(size='sm', color='primary')

            with ui.column().classes('flex-1 min-w-0'):
                ui.label(file_path.name).classes('font-medium truncate')
                ui.label(file_size_str).classes('text-xs text-gray-500')

            with ui.row().classes('gap-1'):
                download_btn = ui.button(
                    icon='download',
                    on_click=lambda f=file_path: self.download_file(f),
                ).props('flat round').classes('text-primary')
                # Only enable download for completed files
                if status != 'completed' or not file_exists:
                    download_btn.disable()

                ui.button(
                    icon='delete',
                    on_click=lambda f=file_path: self.delete_file(f),
                ).props('flat round').classes('text-red-500')
    
    def format_file_size(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def download_file(self, file_path: Path) -> None:
        if not file_path.exists():
            ui.notify(t('file_not_found'), type='negative', position='top')
            return

        # 提示用户
        ui.notify(t('starting_download', filename=file_path.name), type='info', position='top')

        ui.download(str(file_path.resolve()))

    def delete_file(self, file_path: Path) -> None:
        try:
            if file_path.exists():
                file_path.unlink()

            if file_path in self.processed_files:
                self.processed_files.remove(file_path)

            self.update_file_list()
            ui.notify(t('file_deleted', filename=file_path.name), type='positive', position='top')
        except Exception as e:
            ui.notify(t('delete_failed', error=str(e)), type='negative', position='top')

    def clear_processed_files(self) -> None:
        """Clear all files in the output directory."""
        output_dir = Path('output')
        deleted_count = 0

        # Delete all files in output directory
        if output_dir.exists():
            for file_path in output_dir.iterdir():
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception:
                        continue

        # Clear the processed files list and status tracking
        self.processed_files.clear()
        self.file_processing_status.clear()
        self.processing_progress = (0, 0)
        if self.progress_label is not None:
            self.progress_label.text = ''
        self.update_file_list()

        if deleted_count > 0:
            ui.notify(t('all_files_cleared'), type='positive', position='top')
        else:
            ui.notify(t('no_files_to_clear'), type='info', position='top')

    def load_existing_output_files(self) -> None:
        """Load existing files from the output directory."""
        output_dir = Path('output')
        if not output_dir.exists():
            return

        # Clear current processed files list
        self.processed_files.clear()
        self.file_processing_status.clear()

        # Load all files from output directory
        for file_path in output_dir.iterdir():
            if file_path.is_file():
                # Include PDF files and common image formats (for watermarks)
                if file_path.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg']:
                    self.processed_files.append(file_path)
                    self.file_processing_status[file_path] = 'completed'

        # Sort files by modification time (newest first)
        self.processed_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    def recreate_upload_widget(self) -> None:
        """Recreate the file upload widget to reset its state completely."""
        if not self.file_selection_container or not self.file_upload_widget:
            return
        
        # Check if upload_widget_container exists (it should be created in build_ui)
        if not hasattr(self, 'upload_widget_container') or not self.upload_widget_container:
            # Fallback: try to recreate without container wrapper
            try:
                old_widget = self.file_upload_widget
                old_widget.delete()
                with self.file_selection_container:
                    self.file_upload_widget = ui.upload(
                        label=t('auto_upload_hint'),
                        on_upload=self.handle_file_upload,
                        multiple=True,
                        auto_upload=True
                    ).classes('w-full')
            except Exception as e:
                print(f"Warning: Could not recreate upload widget: {e}")
            return
        
        try:
            # Store the old widget and container IDs
            old_widget = self.file_upload_widget
            old_id = old_widget.id if hasattr(old_widget, 'id') else None
            container_id = self.upload_widget_container.id if hasattr(self.upload_widget_container, 'id') else None
            
            # Clear the container content using JavaScript
            if container_id:
                ui.run_javascript(f'''
                    (function() {{
                        const container = document.querySelector(`[data-id="{container_id}"]`);
                        if (container) {{
                            container.innerHTML = '';
                        }}
                    }})();
                ''')
            
            # Delete the old widget
            try:
                old_widget.delete()
            except Exception:
                pass
            
            # Also try JavaScript deletion as fallback
            if old_id:
                ui.run_javascript(f'''
                    (function() {{
                        const oldElement = document.querySelector(`[data-id="{old_id}"]`);
                        if (oldElement && oldElement.parentNode) {{
                            oldElement.parentNode.removeChild(oldElement);
                        }}
                    }})();
                ''')
            
            # Wait a moment for DOM to update
            import time
            time.sleep(0.05)
            
            # Create the new upload widget directly in the container
            # This ensures it's in the correct position (before uploaded_files_label)
            with self.upload_widget_container:
                self.file_upload_widget = ui.upload(
                    label=t('auto_upload_hint'),
                    on_upload=self.handle_file_upload,
                    multiple=True,
                    auto_upload=True
                ).classes('w-full')
        except Exception as e:
            print(f"Warning: Could not recreate upload widget: {e}")
            import traceback
            traceback.print_exc()
    
    async def handle_file_upload(self, e: UploadEventArguments):
        file_obj = getattr(e, 'file', None)
        if file_obj is None:
            ui.notify(t('upload_failed'), type='negative', position='top')
            return

        filename = getattr(file_obj, 'name', 'uploaded_file')

        upload_dir = Path('temp_uploads')
        upload_dir.mkdir(exist_ok=True)

        save_path = upload_dir / filename
        data = await file_obj.read()
        with open(save_path, 'wb') as f:
            f.write(data)

        self.uploaded_files[filename] = str(save_path)

        ui.notify(t('file_uploaded', filename=filename), position='top')
    
    async def handle_watermark_image_upload(self, e: UploadEventArguments):
        file_obj = getattr(e, 'file', None)
        if file_obj is None:
            ui.notify(t('watermark_upload_failed'), type='negative', position='top')
            return

        filename = getattr(file_obj, 'name', 'watermark')

        upload_dir = Path('temp_uploads')
        upload_dir.mkdir(exist_ok=True)
        
        save_path = upload_dir / f'watermark_{filename}'
        data = await file_obj.read()
        with open(save_path, 'wb') as f:
            f.write(data)
        
        self.watermark_image_path = str(save_path)
        ui.notify(t('watermark_image_uploaded', filename=filename), position='top')

    def _generate_watermark_from_config(self, config: Dict[str, Any]) -> Optional[Path]:
        """
        Unified implementation for watermark_only mode to generate a watermark image
        and update the processed files list / UI.
        """
        watermark_image = setup_watermark_image(config)
        if not watermark_image:
            return None

        watermark_path = Path(watermark_image)
        if not watermark_path.exists():
            return None

        # Update processed files list
        if watermark_path in self.processed_files:
            self.processed_files.remove(watermark_path)
        self.processed_files.insert(0, watermark_path)

        # Mark as completed
        self.file_processing_status[watermark_path] = 'completed'

        # Update UI
        self.update_file_list()
        return watermark_path

    async def generate_watermark_only(self):
        """Generate watermark image only (watermark_only mode)."""
        try:
            # Build configuration
            try:
                config = self.build_config()
            except ValueError as e:
                ui.notify(str(e), type='negative', position='top')
                return

            # Ensure watermark_only mode uses text watermark configuration
            config['mode'] = 'watermark_only'
            config['type'] = 'text'
            config['text'] = self.watermark_text_input.value or 'Watermark'
            config['add_date'] = self.add_date_checkbox.value

            # Generate watermark via unified helper
            watermark_path = self._generate_watermark_from_config(config)
            if watermark_path:
                ui.notify(t('watermark_generated_successfully'), type='positive', position='top')
            else:
                ui.notify(t('watermark_generation_failed'), type='negative', position='top')
        except Exception as e:
            ui.notify(t('error', error=str(e)), type='negative', position='top')
    
    def build_config(self) -> Dict[str, Any]:
        config = {
            'mode': self.mode_radio.value,
            'watermark_type': WatermarkConfig.WATERMARK_TYPE,
            'opacity': WatermarkConfig.OPACITY,
            'angle': WatermarkConfig.ANGLE,
            'horizontal_boxes': WatermarkConfig.HORIZONTAL_BOXES,
            'vertical_boxes': WatermarkConfig.VERTICAL_BOXES,
            'image_scale': WatermarkConfig.IMAGE_SCALE,
            'input_dir': 'temp_uploads',
            'output_dir': 'output',
            'verbose': False,
            'filter_front_matter': self.filter_front_matter_checkbox.value,
            'rename_by_title': self.rename_by_title_checkbox.value,
        }
        
        if config['mode'] != 'watermark_only':
            config['type'] = self.watermark_type_radio.value
            if config['type'] == 'text':
                config['text'] = self.watermark_text_input.value or 'Watermark'
                config['add_date'] = self.add_date_checkbox.value
            else:
                image_path = self.watermark_image_path
                if image_path and Path(image_path).exists():
                    config['image'] = image_path
                else:
                    raise ValueError(t('invalid_watermark_image_path'))
        elif config['mode'] == 'watermark_only':
            # watermark_only mode only supports text watermark
            config['type'] = 'text'
            config['text'] = self.watermark_text_input.value or 'Watermark'
            config['add_date'] = self.add_date_checkbox.value
        
        config.update({
            'font_size': WatermarkConfig.FONT_SIZE,
            'text_color': WatermarkConfig.TEXT_COLOR,
            'padding': WatermarkConfig.PADDING,
        })
        
        return config
    
    async def show_conflict_dialog(self, count: int) -> Optional[str]:
        with ui.dialog() as dialog, ui.card():
            ui.label(t('conflict_detected', count=count)).classes('text-lg font-bold')
            ui.label(t('conflict_description')).classes('text-sm text-gray-600')
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button(t('skip_existing'), on_click=lambda: dialog.submit('skip'))
                ui.button(t('overwrite'), on_click=lambda: dialog.submit('overwrite'))
                ui.button(t('coexist_rename'), on_click=lambda: dialog.submit('rename'))
        return await dialog

    async def process_files(self):
        try:
            if not self.uploaded_files and self.mode_radio.value != 'watermark_only':
                ui.notify(t('please_upload_files_first'), type='negative', position='top')
                return
            
            try:
                self.config = self.build_config()
            except ValueError as e:
                ui.notify(str(e), type='negative', position='top')
                return

            selected_paths: List[Path] = [
                Path(p) for p in self.uploaded_files.values() if Path(p).is_file()
            ]
            selected_pdf_files: List[Path] = [
                p for p in selected_paths if p.suffix.lower() == '.pdf'
            ]
            selected_md_files: List[Path] = [
                p for p in selected_paths if p.suffix.lower() in ('.md', '.markdown', '.MD', '.MARKDOWN')
            ]
            
            # Validate files for 'pdf' processing mode
            if self.config['mode'] == 'pdf':
                non_pdf_files = [
                    p for p in selected_paths
                    if p.suffix.lower() != '.pdf' # Only allow PDF files in this mode
                ]
                if non_pdf_files:
                    found_formats = sorted(list(set(p.suffix.lower() for p in non_pdf_files)))
                    formats_str = ', '.join(found_formats)
                    ui.notify(t('non_pdf_files_in_pdf_mode_error', formats_found=formats_str), type='negative', position='top')
                    self.process_button.enable()
                    return

            upload_dir = Path('temp_uploads')
            if upload_dir.exists():
                current_files = {Path(p).resolve() for p in self.uploaded_files.values()}
                for p in upload_dir.iterdir():
                    if not p.is_file():
                        continue
                    if p.resolve() in current_files:
                        continue
                    if p.name.startswith('watermark_'):
                        continue
                    try:
                        p.unlink()
                    except Exception:
                        pass
            
            output_dir = Path('output')
            files_to_check = selected_pdf_files + selected_md_files
            
            # Pre-calculate target paths to detect conflicts
            target_map: Dict[Path, Path] = {}
            conflicts: List[Path] = []
            
            for p in files_to_check:
                if self.config['mode'] == 'pdf':
                    out_name = p.name
                elif self.config['mode'] == 'markdown':
                    if self.config.get('rename_by_title'):
                        title = extract_h1_title(p)
                        base_name = title if title else p.stem
                    else:
                        base_name = p.stem
                    out_name = f"{base_name}.pdf"
                else:
                    continue
                
                out_path = output_dir / out_name
                target_map[p] = out_path
                if out_path.exists():
                    conflicts.append(out_path)
            
            conflict_strategy = 'rename'  # Default: Coexist
            
            if conflicts and self.config['mode'] != 'watermark_only':
                result = await self.show_conflict_dialog(len(conflicts))
                if not result:
                    self.process_button.enable()
                    return
                conflict_strategy = result

            # Filter inputs based on strategy
            final_pdf_files = []
            final_md_files = []
            
            if conflict_strategy == 'skip':
                final_pdf_files = [p for p in selected_pdf_files if not target_map.get(p, Path('')).exists()]
                final_md_files = [p for p in selected_md_files if not target_map.get(p, Path('')).exists()]
                
                if not final_pdf_files and not final_md_files:
                    ui.notify(t('no_files_to_process'), type='warning', position='top')
                    self.process_button.enable()
                    return
            else:
                final_pdf_files = selected_pdf_files
                final_md_files = selected_md_files
                
            # Update expected_outputs for UI
            expected_outputs: List[Path] = []
            
            # Helper to predict output path based on strategy
            def predict_output(p):
                base_out = target_map[p]
                # Ensure .pdf suffix for markdown files, even if the target_map[p] somehow didn't
                if p.suffix.lower() in ['.md', '.markdown'] and base_out.suffix.lower() != '.pdf':
                    base_out = base_out.with_suffix('.pdf')

                if conflict_strategy == 'overwrite':
                    return base_out
                elif conflict_strategy == 'rename' and base_out.exists():
                    # Prediction might be off if multiple conflicts, but good enough for UI init
                    return base_out.parent / f"{base_out.stem}_new{base_out.suffix}"
                return base_out

            expected_outputs.extend([predict_output(p) for p in final_pdf_files])
            expected_outputs.extend([predict_output(p) for p in final_md_files])

            if expected_outputs:
                # Add new files to the beginning of the list, avoiding duplicates
                for out_path in reversed(expected_outputs):
                    if out_path in self.processed_files:
                        self.processed_files.remove(out_path)
                    self.processed_files.insert(0, out_path)
                
                # Initialize status for these specific OUTPUT files
                for out_path in expected_outputs:
                    self.file_processing_status[out_path] = 'pending'
                
                self.processing_progress = (0, len(expected_outputs))
                self.update_file_list()

            self.is_processing = True
            self.process_button.disable()
            self.update_file_list()
            
            output_dir.mkdir(exist_ok=True)
            
            watermark_image: Optional[str] = None
            success = False
            output_files: List[Path] = []
            
            try:
                if self.config['mode'] == 'watermark_only':
                    # Use unified watermark generation helper for watermark_only mode
                    watermark_path = self._generate_watermark_from_config(self.config)
                    if watermark_path:
                        ui.notify(t('watermark_generated_successfully'), type='positive', position='top')
                        success = True
                    else:
                        ui.notify(t('watermark_generation_failed'), type='negative', position='top')

                else:
                    watermark_image = setup_watermark_image(self.config)
                    if not watermark_image:
                        ui.notify(t('watermark_image_not_found'), type='negative', position='top')
                        return
                    
                    # Process files one by one for real-time UI updates
                    if self.config['mode'] == 'pdf':
                        if final_pdf_files:
                            success, output_files = await self.process_files_individually(
                                final_pdf_files,
                                'pdf',
                                watermark_image,
                                predicted_output_map={p: target_map[p] for p in final_pdf_files},
                                conflict_strategy=conflict_strategy,
                                watermark_type=self.config.get('watermark_type', 'grid'),
                                horizontal_boxes=self.config.get('horizontal_boxes', 3),
                                vertical_boxes=self.config.get('vertical_boxes', 6),
                                angle=self.config.get('angle', 45),
                                opacity=self.config.get('opacity', 0.2),
                                image_scale=self.config.get('image_scale', 1.0),
                            )
                        elif final_md_files:
                            # Filter out keys that conflict with positional arguments
                            config_kwargs = {k: v for k, v in self.config.items() if k not in ['mode']}
                            success, output_files = await self.process_files_individually(
                                final_md_files,
                                'markdown',
                                watermark_image,
                                predicted_output_map={p: target_map[p] for p in final_md_files},
                                conflict_strategy=conflict_strategy,
                                **config_kwargs
                            )
                        else:
                            ui.notify(t('no_files_found'), type='warning', position='top')
                            return
                    else:
                        if not final_md_files:
                            ui.notify(t('no_markdown_files_selected'), type='warning', position='top')
                            return
                        # Filter out keys that conflict with positional arguments
                        config_kwargs = {k: v for k, v in self.config.items() if k not in ['mode']}
                        success, output_files = await self.process_files_individually(
                            final_md_files,
                            'markdown',
                            watermark_image,
                            predicted_output_map={p: target_map[p] for p in final_md_files},
                            conflict_strategy=conflict_strategy,
                            **config_kwargs
                        )
                    
                    if watermark_image and self.config['mode'] != 'watermark_only':
                        cleanup_generated_watermark(watermark_image, self.config)
                
                if success and output_files:
                    # No need to overwrite processed_files here as we did it at start
                    # But if names changed during processing (e.g. conflict resolution changed name differently than predicted),
                    # process_files_individually should handle it.
                    
                    # Update progress based on completed outputs
                    completed_count = len([f for f in output_files if f.exists()])
                    self.processing_progress = (completed_count, len(expected_outputs))
                    self.update_file_list()
                
                if success:
                    ui.notify(t('processing_successful'), type='positive', position='top')
                else:
                    ui.notify(t('processing_failed'), type='negative', position='top')
            
            except Exception as e:
                ui.notify(t('error', error=str(e)), type='negative', position='top')
                success = False
            
            finally:
                self.is_processing = False
                self.update_file_list()
                self.process_button.enable()
                
                # Clear uploaded files after processing is complete
                # This ensures that uploaded files are cleared so new files won't be processed together with old ones
                had_uploaded_files = bool(self.uploaded_files)
                
                if had_uploaded_files:
                    # Clear the uploaded files dictionary
                    self.uploaded_files.clear()
                    
                    # Clear temporary uploaded files (but keep watermark files)
                    upload_dir = Path('temp_uploads')
                    if upload_dir.exists():
                        for p in upload_dir.iterdir():
                            if not p.is_file():
                                continue
                            # Keep watermark files
                            if p.name.startswith('watermark_'):
                                continue
                            try:
                                p.unlink()
                            except Exception:
                                pass
                    
                    # Update uploaded files label
                    if self.uploaded_files_label:
                        self.uploaded_files_label.text = ''
                    
                    # Recreate the upload widget to reset its state completely
                    # This ensures a clean state without any residual file information
                    self.recreate_upload_widget()
        
        except Exception as e:
            ui.notify(t('configuration_error', error=str(e)), type='negative', position='top')
            self.process_button.enable()

    async def process_single_file(self, file_path: Path, mode: str, output_file: Path, watermark_image: str, **kwargs) -> bool:
        """Process a single file."""
        try:
            if mode == 'pdf':
                # Process PDF file
                success = await asyncio.to_thread(
                    add_watermark_to_file,
                    file_path,
                    output_file,
                    watermark_image,
                    kwargs.get('watermark_type', 'grid'),
                    kwargs.get('opacity', 0.2),
                    kwargs.get('angle', 45),
                    kwargs.get('image_scale', 1.0),
                    horizontal_boxes=kwargs.get('horizontal_boxes', 3),
                    vertical_boxes=kwargs.get('vertical_boxes', 6)
                )
            elif mode == 'markdown':
                # First convert markdown to PDF
                from core.markdown_processor import md_to_pdf_with_mermaid_async
                temp_pdf = output_file.with_suffix('.temp.pdf')

                # Convert markdown to PDF
                if await md_to_pdf_with_mermaid_async(file_path, temp_pdf, filter_front_matter=kwargs.get('filter_front_matter', False)):
                    if watermark_image:
                        # Add watermark to the PDF
                        success = await asyncio.to_thread(
                            add_watermark_to_file,
                            temp_pdf,
                            output_file,
                            watermark_image,
                            kwargs.get('watermark_type', 'grid'),
                            kwargs.get('opacity', 0.2),
                            kwargs.get('angle', 45),
                            kwargs.get('image_scale', 1.0),
                            horizontal_boxes=kwargs.get('horizontal_boxes', 3),
                            vertical_boxes=kwargs.get('vertical_boxes', 6)
                        )
                        # Clean up temp file
                        try:
                            temp_pdf.unlink()
                        except:
                            pass
                    else:
                        # No watermark, just move the file
                        import shutil
                        shutil.move(str(temp_pdf), str(output_file))
                        success = True
                else:
                    success = False
            else:
                success = False

            return success

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
            return False

    async def process_files_individually(self, files: List[Path], mode: str, watermark_image: str, predicted_output_map: Dict[Path, Path], **kwargs) -> Tuple[bool, List[Path]]:
        """Process files one by one with real-time UI updates."""
        from pathlib import Path

        output_dir = Path('output')
        output_dir.mkdir(parents=True, exist_ok=True)

        output_files: List[Path] = []
        success_count = 0
        
        conflict_strategy = kwargs.get('conflict_strategy', 'rename')
        rename_by_title = kwargs.get('rename_by_title', False)

        for file_path in files:
            # Get the initial predicted output path for this input file
            predicted_output_path = predicted_output_map.get(file_path)
            if not predicted_output_path:
                print(f"Warning: No predicted output path found for input file {file_path}. Skipping.")
                continue # Skip this file if prediction is missing

            # Determine actual output file path (can be different from predicted if renamed)
            actual_output_file = Path("") # Initialize
            if mode == 'markdown':
                base_name = file_path.stem
                if rename_by_title:
                     title = extract_h1_title(file_path)
                     if title:
                         base_name = title
                actual_output_file = (output_dir / base_name).with_suffix('.pdf') # Ensure .pdf suffix
            else: # mode is 'pdf'
                base_name = file_path.stem
                extension = file_path.suffix
                actual_output_file = output_dir / f"{base_name}{extension}"

            # Apply conflict resolution if the actual_output_file already exists
            if actual_output_file.exists():
                if conflict_strategy == 'overwrite':
                    pass
                elif conflict_strategy == 'skip':
                    continue
                else: # rename (default)
                    counter = 1
                    stem = actual_output_file.stem
                    suffix = actual_output_file.suffix
                    new_output_file = output_dir / f"{stem}_new{suffix}"
                    while new_output_file.exists():
                        counter += 1
                        new_output_file = output_dir / f"{stem}_new{counter}{suffix}"
                    actual_output_file = new_output_file
            
            # --- Update internal state with the actual, final output file path ---
            # If the actual output path is different from the predicted one, update self.processed_files and self.file_processing_status
            if actual_output_file != predicted_output_path:
                # Remove the predicted (placeholder) path from self.processed_files
                if predicted_output_path in self.processed_files:
                    self.processed_files.remove(predicted_output_path)
                # Remove its status entry
                if predicted_output_path in self.file_processing_status:
                    del self.file_processing_status[predicted_output_path]
                
                # Insert the actual, final output_file into self.processed_files
                if actual_output_file not in self.processed_files: # Ensure no accidental re-adds
                    self.processed_files.insert(0, actual_output_file)
            
            # Now, mark the *actual_output_file* as processing
            self.file_processing_status[actual_output_file] = 'processing'
            self.update_file_list()

            # Process the file using the actual_output_file
            try:
                success = await self.process_single_file(file_path, mode, actual_output_file, watermark_image, **kwargs)

                if success:
                    success_count += 1
                    output_files.append(actual_output_file) # Store the actual path
                    # Mark file as completed using the actual_output_file
                    self.file_processing_status[actual_output_file] = 'completed'
                    
                    # Update progress tuple to reflect actual completion count in this batch
                    current_completed = self.processing_progress[0] + 1
                    total_batch = self.processing_progress[1]
                    self.processing_progress = (current_completed, total_batch)
                else:
                    # Mark file as failed
                    self.file_processing_status[actual_output_file] = 'error'
            except Exception as e:
                print(f"Unexpected error processing {file_path.name}: {e}")
                # Mark file as failed but don't crash the whole process
                self.file_processing_status[actual_output_file] = 'error'
            
            # Update UI after each file
            self.update_file_list()
        overall_success = success_count == len(files)
        return overall_success, output_files


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
                pass