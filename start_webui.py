#!/usr/bin/env python3
"""
Web UI启动脚本 / Web UI Launcher Script
专门用于启动 NiceGUI Web 界面 / Dedicated script for launching NiceGUI Web interface
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from nicegui import ui
    from ui.web_ui import WebUI
    from i18n import t
except ImportError as e:
    print("✗ Error: Failed to import required modules")
    print(f"  {e}")
    print("\nPlease make sure NiceGUI is installed:")
    print("  pip install nicegui")
    sys.exit(1)


def main():
    """Main entry point for Web UI launcher"""
    parser = argparse.ArgumentParser(
        description='启动 Markdown/PDF 水印工具 Web 界面 / Launch Markdown/PDF Watermark Tool Web UI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例 / Examples:
  python start_webui.py              # 使用默认端口 8080 / Use default port 8080
  python start_webui.py --port 3000  # 使用端口 3000 / Use port 3000
  python start_webui.py --no-open    # 不自动打开浏览器 / Don't auto-open browser
        """
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8080,
        help='Web服务器端口 / Web server port (default: 8080)'
    )
    
    parser.add_argument(
        '--no-open',
        action='store_true',
        help='不自动打开浏览器 / Don\'t automatically open browser'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='绑定主机地址 / Host to bind to (default: 0.0.0.0)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Markdown/PDF 水印工具 Web 界面")
    print("Markdown/PDF Watermark Tool Web UI")
    print("=" * 60)
    print(f"端口 / Port: {args.port}")
    print(f"主机 / Host: {args.host}")
    print(f"自动打开浏览器 / Auto-open browser: {not args.no_open}")
    print("=" * 60)
    print("\n正在启动 Web 服务器... / Starting web server...")
    print(f"访问地址 / Access URL: http://localhost:{args.port}")
    print("\n按 Ctrl+C 停止服务器 / Press Ctrl+C to stop the server\n")
    
    # Build UI
    web_ui = WebUI()
    web_ui.build_ui()
    
    # Run NiceGUI server - must be called at module level
    ui.run(port=args.port, show=not args.no_open, title=t('app_title'), host=args.host)


if __name__ in {"__main__", "__mp_main__"}:
    main()
