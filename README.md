# Markdown to PDF Tool

**English** | [中文](README.zh.md)

A powerful Markdown-to-PDF tool with GitHub-styled rendering, Mermaid diagrams, syntax highlighting, and automatic PDF watermarking. Designed for technical docs and code projects with robust Chinese font rendering and batch processing.

## Features

- **Markdown → PDF (GitHub style)**: tables, code blocks, links, images; multi-language syntax highlighting
- **Mermaid support**: flowcharts, sequence diagrams, Gantt charts
- **Watermarking**: text/image watermarks with adjustable opacity/angle/density; generate clean PDFs as needed
- **Chinese fonts**: auto-detects common CJK fonts for stable rendering
- **Batch processing**: process the entire `input/` directory, outputs to `output/`
- **Interactive/Default modes**: minimal prompts in interactive mode; quick default mode
- **Multilingual UI**: English/Chinese auto/manual switch

Use cases: README/architecture (Mermaid), API and code docs, blog archiving, project reports and teaching handouts; batch watermarking or clean PDF export for easy distribution.



## Quick Start

### Run the project

```bash
git clone https://github.com/pinyinjj/Markdown-to-PDF-Tool.git
cd md-pdf-watermark
python main.py
```

The program will guide you through the modes:

**1. Process PDF files (add watermark)**
- Add watermarks to existing PDFs
- Batch-process multiple PDFs

**2. Convert Markdown to PDF (add watermark)**
- Convert Markdown to PDF and add a watermark
- Mermaid and code highlighting supported
- Auto-detect Chinese fonts

**3. Generate watermark image only**
- Only generate watermark images, no file processing
- Great for preparing watermark assets in bulk
- Supports text and image watermarks

**4. Convert Markdown to PDF (no watermark)**
- Convert Markdown to PDF without adding a watermark
- Mermaid and code highlighting supported
- For clean PDF scenarios




## Detailed Installation

### Windows

1. **Install Python**
   - Get Python 3.8+ from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH" during installation

2. **Install dependencies**
   ```cmd
   pip install -r requirements.txt
   playwright install
   ```

3. **System dependencies** (if needed)
   ```cmd
   playwright install-deps
   ```

### macOS

1. **Install Python**
   ```bash
   # Using Homebrew
   brew install python

   # Or download from python.org
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. **System dependencies** (if needed)
   ```bash
   playwright install-deps
   ```

### Linux

1. **Install Python**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-venv

   # CentOS/RHEL
   sudo yum install python3 python3-pip
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. **System dependencies**
   ```bash
   sudo playwright install-deps
   ```

## Internationalization

### Language settings

English and Chinese UI are supported:

#### Auto detection
The program detects system language via:
- System `locale`
- `LANG` environment variable
- Defaults to English as fallback

#### Manual setting
```bash
# Use English UI
python main.py --lang en --interactive

# Use Chinese UI
python main.py --lang zh --interactive

# Auto-detect (default)
python main.py --interactive
```

#### Switching language
- Affects all UI text in interactive mode (menus, prompts, errors)
- Does not affect your document contents

## Configuration

### Watermark configuration

All configuration is managed by the `WatermarkConfig` class:

```python
class WatermarkConfig:
    # Text watermark settings
    GENERATE_IMAGE_FROM_TEXT = True      # Generate image from text
    TEXT_WATERMARK_FILE = "watermarks/text_watermark.png"  # Text watermark image path
    FONT_SIZE = 36                       # Font size
    TEXT_COLOR = (68, 68, 68, 220)      # RGBA text color
    PADDING = 20                         # Padding
    
    # PDF watermark parameters
    WATERMARK_TYPE = "grid"              # grid or insert
    OPACITY = 0.2                        # Opacity
    ANGLE = 45                           # Rotation angle
    IMAGE_SCALE = 1.0                    # Image scale
    HORIZONTAL_BOXES = 3                 # Grid columns
    VERTICAL_BOXES = 6                   # Grid rows
```

### Fonts

Common CJK fonts are auto-detected on:

- **Windows**: Microsoft YaHei, SimHei, SimSun, Kai, FangSong, etc.
- **macOS**: PingFang, Hiragino Sans GB, etc.
- **Linux**: Noto Sans CJK, etc.

Specify a custom font via env var:
```bash
export WATERMARK_FONT="/path/to/your/font.ttf"
```

## Usage

### Basic

1. Put PDF/Markdown files into the `input/` directory
2. Run `python main.py`
3. Find results in `output/`



#### Adjust watermark style

Modify relevant fields in `WatermarkConfig`:

```python
# Adjust opacity
OPACITY = 0.3

# Adjust angle
ANGLE = 30

# Adjust grid density
HORIZONTAL_BOXES = 4
VERTICAL_BOXES = 8
```

## Troubleshooting

### Common issues

1. **Playwright not installed**
   ```bash
   playwright install
   ```

2. **Chinese font not found**
- Ensure system has a CJK font installed
- Or set `WATERMARK_FONT`

3. **watermark command not found**
- Ensure `pdf-watermark` is installed
- Check your virtual environment activation

4. **Permissions**
   ```bash
   # Linux/macOS
   sudo playwright install-deps
   ```

### Debug mode

Verbose output shows:
- File processing status
- Watermark generation steps
- Error messages

## Dependencies

| Package | Version | Purpose |
|------|------|------|
| Pillow | >=9.0.0 | Image processing for text watermark image |
| markdown | >=3.4.0 | Markdown processing |
| playwright | >=1.30.0 | Browser automation, PDF rendering |
| pdf-watermark | >=0.1.0 | Add watermarks to PDF |

## License

This project is licensed under GPL-3.0-or-later.

---

**Note**: On first run Playwright may download a browser; ensure network connectivity.