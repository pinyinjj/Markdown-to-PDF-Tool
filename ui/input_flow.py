"""
Interactive user input flow for watermark configuration.
"""

import os
from typing import Optional, Dict, Any

from i18n import t
from config import WatermarkConfig


def _prompt_mode() -> Dict[str, Any]:
    print(t('operation_mode_title'))
    print(f"   [1] {t('process_pdf_with_watermark')}")
    print(f"   [2] {t('convert_md_to_pdf_with_watermark')}")
    print(f"   [3] {t('generate_watermark_only')}")
    print(f"   [4] {t('convert_md_to_pdf_no_watermark')}")
    print(f"   [0] {t('exit_program')}")
    while True:
        choice = input(t('invalid_choice') + " 0-4: ").strip()
        if choice == "0":
            print(t('program_exited'))
            exit(0)
        if choice == "1":
            return {"mode": "pdf"}
        if choice == "2":
            return {"mode": "markdown"}
        if choice == "3":
            return {"mode": "watermark_only"}
        if choice == "4":
            return {"mode": "markdown_no_watermark"}
        print(t('invalid_choice') + " 0-4")


def _prompt_watermark_type() -> str:
    print()
    print(t('watermark_type_title'))
    print(f"   [1] {t('text_watermark_recommended')}")
    print(f"   [2] {t('image_watermark')}")
    print(f"   [0] {t('back_to_previous')}")
    while True:
        choice = input(t('invalid_choice') + " 0-2: ").strip()
        if choice == "0":
            return "back"
        if choice == "1":
            return "text"
        if choice == "2":
            return "image"
        print(t('invalid_choice') + " 0-2")


def _prompt_text_config(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    print()
    print(t('text_watermark_config'))
    print(f"   [0] {t('back_to_previous')}")
    while True:
        red = "\033[31m"
        reset = "\033[0m"
        prompt = f"\n{red}{t('enter_watermark_text')}{reset}\n> "
        text = input(prompt).strip()
        if text == "0":
            return None
        if text:
            config["text"] = text
            break
        print(t('watermark_text_cannot_be_empty'))
    while True:
        add_date = input(t('add_date_to_watermark')).strip().lower()
        if add_date == "0":
            return None
        if add_date in ["", "y", "n"]:
            config["add_date"] = add_date != "n"
            break
        print(t('enter_y_n_or_0'))
    return config


def _prompt_image_config(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    print()
    print(t('image_watermark_config'))
    print(f"   [0] {t('back_to_previous')}")
    while True:
        image_path = input(t('enter_watermark_image_path')).strip()
        if image_path == "0":
            return None
        if image_path and os.path.exists(image_path):
            config["image"] = image_path
            return config
        if image_path:
            print(t('image_file_not_found') + f": {image_path}")
        else:
            print(t('image_path_cannot_be_empty'))


def _apply_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
    config.update({
        "font_size": WatermarkConfig.FONT_SIZE,
        "text_color": WatermarkConfig.TEXT_COLOR,
        "padding": WatermarkConfig.PADDING,
        "watermark_type": WatermarkConfig.WATERMARK_TYPE,
        "opacity": WatermarkConfig.OPACITY,
        "angle": WatermarkConfig.ANGLE,
        "image_scale": WatermarkConfig.IMAGE_SCALE,
        "horizontal_boxes": WatermarkConfig.HORIZONTAL_BOXES,
        "vertical_boxes": WatermarkConfig.VERTICAL_BOXES,
        "input_dir": "input",
        "output_dir": "output",
        "verbose": False
    })
    return config


def get_user_input() -> Optional[Dict[str, Any]]:
    """
    Get user input for watermark configuration.

    Returns:
        dict: User configuration dictionary or None to go back.
    """
    while True:
        print(t('app_title'))
        print("=" * 50)
        print(t('select_operation_mode'))
        print()

        config: Dict[str, Any] = {}

        # Operation mode selection
        config.update(_prompt_mode())

        # If no watermark mode, skip watermark configuration
        if config.get("mode") == "markdown_no_watermark":
            config["type"] = "none"
            break

        # Watermark type selection
        wtype = _prompt_watermark_type()
        if wtype == "back":
            continue
        config["type"] = wtype

        # If watermark type is selected, continue configuration
        if config.get("type"):
            break

    # Continue configuring watermark parameters
    if config.get("type") == "none":
        config = _apply_defaults(config)
    elif config["type"] == "text":
        if _prompt_text_config(config) is None:
            return None
    else:
        if _prompt_image_config(config) is None:
            return None

    # Use default configuration to fill other parameters
    config = _apply_defaults(config)

    return config


