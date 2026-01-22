#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path
from nicegui import ui

sys.path.insert(0, str(Path(__file__).parent))

try:
    from ui.web_ui import WebUI
    from i18n import t
except ImportError as e:
    print(f"Error: Failed to import required modules: {e}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Launch Markdown/PDF Watermark Tool Web UI')
    
    parser.add_argument('--port', '-p', type=int, default=8080, help='Web server port (default: 8080)')
    parser.add_argument('--no-open', action='store_true', help='Don\'t automatically open browser')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Markdown/PDF Watermark Tool Web UI")
    print("=" * 60)
    print(f"Port: {args.port}")
    print(f"Host: {args.host}")
    print(f"Auto-open: {not args.no_open}")
    print("=" * 60)
    
    web_ui = WebUI()
    web_ui.build_ui()
    
    ui.run(port=args.port, show=not args.no_open, title=t('app_title'), host=args.host)


if __name__ in {"__main__", "__mp_main__"}:
    main()