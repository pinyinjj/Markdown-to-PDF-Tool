#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
from nicegui import ui, app

sys.path.insert(0, str(Path(__file__).parent))

try:
    from ui.web_ui import WebUI
    from i18n import t
except ImportError as e:
    print(f"Error: Failed to import required modules: {e}")
    sys.exit(1)

# --- 全局 UI 初始化 ---
# 必须放在全局作用域，确保页面被正确构建
web_ui = WebUI()
web_ui.build_ui()


def main():
    parser = argparse.ArgumentParser(description='Launch Markdown/PDF Watermark Tool Web UI')
    
    parser.add_argument('--port', '-p', type=int, default=8080, help='Web server port (default: 8080)')
    parser.add_argument('--no-open', action='store_true', help='Don\'t automatically open browser')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    
    args = parser.parse_args()

    ui.run(
        port=args.port, 
        show=not args.no_open, 
        title=t('app_title'), 
        host=args.host,
        # reload=False 
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()