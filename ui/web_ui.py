"""
NiceGUI web interface for PDF watermark tool.
"""

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
)


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
        self.file_list_container: Optional[ui.column] = None
        self.clear_files_button: Optional[ui.button] = None
        
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
                .three-column-grid { display: grid !important; grid-template-columns: 1fr 1fr 1fr !important; grid-template-rows: 320px 320px !important; gap: 0.75rem !important; width: 100% !important; }
                .row-span-2 { grid-row: 1 / 3 !important; grid-column: 3 !important; height: calc(320px + 0.75rem + 320px) !important; }
                .col-span-2 { grid-column: 1 / 3 !important; grid-row: 2 !important; }
                @media (max-width: 1024px) { .three-column-grid { grid-template-columns: 1fr; } }
                .card-compact { padding: 1rem; min-height: 320px; height: 320px; display: flex; flex-direction: column; }
                .section-title { font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: #374151; }
                .fixed-card { width: 100%; min-height: 320px; height: 320px; }
                .watermark-card-flexible { width: 100%; min-height: 320px; height: 320px; min-width: 0; flex: 1 1 auto; }
                .file-selection-tall { height: calc(320px + 0.75rem + 320px) !important; min-height: calc(320px + 0.75rem + 320px) !important; }
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

                with ui.card().classes('card-compact fixed-card row-span-2 file-selection-tall'):
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

                with ui.card().classes('w-full card-compact fixed-card col-span-2'):
                    with ui.row().classes('w-full items-center justify-between mb-2'):
                        ui.label(t('processed_files')).classes('section-title mb-0')
                        self.clear_files_button = ui.button(
                            icon='delete',
                            on_click=self.clear_processed_files,
                        ).props('flat round').classes('text-gray-500')

                    self.file_list_container = ui.column().classes('w-full gap-2')
                    self.update_file_list()
            
            ui.separator().classes('opacity-0')

    def switch_language(self, lang: str):
        i18n.set_language(lang)
        self.current_language = lang
        ui.notify(t('language_switched', lang=lang))
        ui.run_javascript('location.reload()')
    
    def update_file_list(self) -> None:
        if self.file_list_container is None:
            return

        self.file_list_container.clear()

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
        file_exists = file_path.exists()
        if file_exists:
            file_size = file_path.stat().st_size
            file_size_str = self.format_file_size(file_size)
        else:
            file_size_str = t('processing')

        with ui.row().classes('w-full items-center gap-3 p-3 border rounded-lg hover:bg-gray-50 transition-colors'):
            if file_exists:
                ui.icon('check_circle').classes('text-green-500')
            else:
                ui.icon('description').classes('text-gray-400')

            with ui.column().classes('flex-1 min-w-0'):
                ui.label(file_path.name).classes('font-medium truncate')
                ui.label(file_size_str).classes('text-xs text-gray-500')

            with ui.row().classes('gap-1'):
                download_btn = ui.button(
                    icon='download',
                    on_click=lambda f=file_path: self.download_file(f),
                ).props('flat round').classes('text-primary')
                if not file_exists or self.is_processing:
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
            ui.notify(t('file_not_found'), type='negative')
            return

        ui.download(str(file_path))
        ui.notify(t('downloading', filename=file_path.name))

    def delete_file(self, file_path: Path) -> None:
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
        files_to_delete = list(self.processed_files)
        deleted_count = 0

        for file_path in files_to_delete:
            try:
                if file_path.exists():
                    file_path.unlink()
                deleted_count += 1
            except Exception:
                continue

        self.processed_files.clear()
        self.update_file_list()

        if deleted_count > 0:
            ui.notify(t('all_files_cleared'), type='positive')
    
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
            ui.notify(t('upload_failed'), type='negative')
            return

        filename = getattr(file_obj, 'name', 'uploaded_file')

        upload_dir = Path('temp_uploads')
        upload_dir.mkdir(exist_ok=True)

        save_path = upload_dir / filename
        data = await file_obj.read()
        with open(save_path, 'wb') as f:
            f.write(data)

        self.uploaded_files[filename] = str(save_path)

        ui.notify(t('file_uploaded', filename=filename))
    
    async def handle_watermark_image_upload(self, e: UploadEventArguments):
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
        
        self.watermark_image_path = str(save_path)
        ui.notify(t('watermark_image_uploaded', filename=filename))
    
    async def generate_watermark_only(self):
        """Generate watermark image only (watermark_only mode)."""
        try:
            # Build configuration
            try:
                config = self.build_config()
            except ValueError as e:
                ui.notify(str(e), type='negative')
                return
            
            # Force text watermark type for watermark_only mode
            config['type'] = 'text'
            config['text'] = self.watermark_text_input.value or 'Watermark'
            config['add_date'] = self.add_date_checkbox.value
            
            # Generate watermark
            watermark_image = setup_watermark_image(config)
            if watermark_image:
                ui.notify(t('watermark_generated_successfully'), type='positive')
            else:
                ui.notify(t('watermark_generation_failed'), type='negative')
        except Exception as e:
            ui.notify(t('error', error=str(e)), type='negative')
    
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
    
    async def process_files(self):
        try:
            if not self.uploaded_files and self.mode_radio.value != 'watermark_only':
                ui.notify(t('please_upload_files_first'), type='negative')
                return
            
            try:
                self.config = self.build_config()
            except ValueError as e:
                ui.notify(str(e), type='negative')
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
            
            # Debug: print uploaded files info
            if not selected_md_files and not selected_pdf_files:
                print(f"Debug: uploaded_files = {self.uploaded_files}")
                print(f"Debug: selected_paths = {selected_paths}")
                print(f"Debug: All file suffixes = {[p.suffix for p in selected_paths]}")

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
            
            expected_outputs: List[Path] = []
            output_dir = Path('output')
            if self.config['mode'] == 'pdf':
                if selected_pdf_files:
                    expected_outputs = [output_dir / p.name for p in selected_pdf_files]
                elif selected_md_files:
                    expected_outputs = [output_dir / f'{p.stem}.pdf' for p in selected_md_files]
            elif self.config['mode'] == 'markdown':
                expected_outputs = [output_dir / f'{p.stem}.pdf' for p in selected_md_files]
            if expected_outputs:
                self.processed_files = expected_outputs
                self.update_file_list()

            self.is_processing = True
            self.process_button.disable()
            self.update_file_list()
            
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)
            
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
                
                else:
                    watermark_image = setup_watermark_image(self.config)
                    if not watermark_image:
                        ui.notify(t('watermark_image_not_found'), type='negative')
                        return
                    
                    if self.config['mode'] == 'pdf':
                        if selected_pdf_files:
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
                    
                    if watermark_image and self.config['mode'] != 'watermark_only':
                        cleanup_generated_watermark(watermark_image, self.config)
                
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
                pass