#!/usr/bin/env python3
"""
PDF Watermark Tool - WebUI Entry Point
This file is kept for backward compatibility. Use start_webui.py directly.
"""

import sys
from pathlib import Path

if __name__ == "__main__":
    # Redirect to start_webui.py
    script_path = Path(__file__).parent / "start_webui.py"
    import subprocess
    sys.exit(subprocess.run([sys.executable, str(script_path)] + sys.argv[1:]).returncode)
