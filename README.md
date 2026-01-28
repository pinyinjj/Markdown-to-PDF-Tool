# Markdown to PDF Tool

**English** | [中文](README.zh.md)

A secure, privacy-focused web application for converting Markdown to PDF with GitHub-style rendering, Mermaid diagrams, and automatic watermarking. Deploy locally with Docker for complete control over your data and processing environment.

## 🛡️ Why Self-Host with Docker?

**Complete Privacy & Security:**
- All processing happens on your local machine
- No data sent to external servers
- Full control over your documents and watermarks

**Reliability & Consistency:**
- Containerized environment ensures consistent results
- Isolated dependencies prevent system conflicts
- Easy backup and migration

**Simple Deployment:**
- One-command setup with Docker Compose
- No complex installation or dependency management
- Works on any platform supporting Docker

## Features

- **🔒 Local Processing**: Everything runs on your machine - your data never leaves your control
- **🌐 Web Interface**: Modern, responsive UI for easy file upload and configuration
- **📝 Markdown → PDF**: GitHub-style rendering with syntax highlighting
- **📊 Mermaid Diagrams**: Flowcharts, sequence diagrams, Gantt charts
- **💧 Smart Watermarking**: Text/image watermarks with customizable settings
- **🇨🇳 Chinese Support**: Auto-detects CJK fonts for perfect rendering
- **📦 Batch Processing**: Handle multiple files with drag-and-drop
- **🌍 Multilingual**: English/Chinese interface support
- **🐳 Docker Ready**: One-command deployment for any platform

**Perfect for:** Technical docs, API documentation, blog posts, project reports, educational materials, and secure document watermarking.



## 🚀 Quick Start with Docker

**One-command deployment - secure, private, and reliable:**

```bash
# Clone the repository
git clone https://github.com/pinyinjj/Markdown-to-PDF-Tool.git
cd md-pdf-watermark

# Start with Docker Compose
docker-compose up -d

# Open your browser
# http://localhost:8080
```

**That's it!** Your personal Markdown-to-PDF service is now running locally with complete privacy and security.

## Operation Modes

The web interface provides four main operation modes:

**📄 Process PDF with Watermark**
- Add watermarks to existing PDF files
- Support for batch processing multiple PDFs

**📝 Markdown to PDF**
- Convert Markdown files to PDF with watermarks
- Full Mermaid diagram support
- Syntax highlighting for code blocks
- GitHub-style rendering

**🎨 Generate Watermark Only**
- Create watermark images for other uses
- Supports both text and image watermarks
- Perfect for preparing watermark assets

**📖 Clean Markdown to PDF**
- Convert Markdown to PDF without watermarks
- Ideal for clean document distribution




## 🐳 Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 1.29+

### Quick Start

```bash
# Clone and start in one command
git clone https://github.com/pinyinjj/Markdown-to-PDF-Tool.git
cd md-pdf-watermark
docker-compose up -d
```

### Manual Docker Commands

If you prefer manual control:

```bash
# Build the image
docker build -t md-pdf-watermark .

# Run the container
docker run -d \
  --name md-pdf-watermark \
  -p 8080:8080 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/watermarks:/app/watermarks \
  -v $(pwd)/temp_uploads:/app/temp_uploads \
  md-pdf-watermark
```

### Access Your Service

Open your browser and navigate to: **http://localhost:8080**

### Data Persistence

The Docker setup automatically mounts these directories for data persistence:
- `./output` - Generated PDF files
- `./watermarks` - Generated watermark images
- `./temp_uploads` - Temporary upload files

### Advanced Configuration

For production deployment, custom ports, or advanced Docker options, see the [Docker Deployment Guide](README.Docker.md).

## Internationalization

### Language Settings

The web interface supports both English and Chinese:

#### Auto Detection
The application automatically detects your system language through:
- System locale settings
- `LANG` environment variable
- Browser language preferences
- Defaults to English if detection fails

#### Manual Language Switching
- Use the language toggle buttons in the top-right corner of the web interface
- Switch between English and Chinese instantly
- Language preference is saved per session

#### Interface Localization
- All UI elements are fully localized (buttons, labels, messages)
- Document content remains unaffected by language settings

## Configuration

### Web Interface Configuration

All settings are configured through the intuitive web interface:

#### Watermark Settings

**Text Watermarks:**
- Custom watermark text input
- Optional date inclusion
- Automatic font detection for CJK characters

**Image Watermarks:**
- Drag-and-drop image upload
- Support for PNG, JPG, and other common formats

**Watermark Parameters:**
- Opacity control (0-100%)
- Rotation angle adjustment
- Grid density settings
- Scale and positioning options

### Advanced Configuration

For advanced users, modify `config.py`:

```python
class WatermarkConfig:
    # Text watermark generation
    FONT_SIZE = 36
    TEXT_COLOR = (68, 68, 68, 220)  # RGBA
    PADDING = 20

    # PDF watermark application
    WATERMARK_TYPE = "grid"
    OPACITY = 0.2
    ANGLE = 45
    IMAGE_SCALE = 1.0
    HORIZONTAL_BOXES = 3
    VERTICAL_BOXES = 6
```

### Font Support

**Automatic Detection:**
- **Windows**: Microsoft YaHei, SimHei, SimSun
- **Linux**: Noto Sans CJK fonts
- **macOS**: System CJK fonts

**Custom Fonts:**
```bash
export WATERMARK_FONT="/path/to/your/font.ttf"
```

## 📱 Using Your Local Service

### Web Interface

1. **Access your service:** Open `http://localhost:8080` in your browser

2. **Choose operation mode:**
   - **Process PDF with Watermark** - Add watermarks to existing PDFs
   - **Markdown to PDF** - Convert Markdown files with watermarks
   - **Generate Watermark Only** - Create watermark images
   - **Clean Markdown to PDF** - Convert without watermarks

3. **Configure settings:**
   - Select watermark type (text or image)
   - Customize watermark appearance
   - Adjust processing options

4. **Upload & process:**
   - Drag and drop files or click to browse
   - Click "Process Files" to start conversion
   - Download results when complete

### 🔧 Docker Management

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop the service
docker-compose down

# Restart the service
docker-compose restart

# Update to latest version
docker-compose pull && docker-compose up -d
```

### 📁 File Management

Your Docker setup automatically manages:
- **Input files:** Uploaded through the web interface
- **Output files:** Stored in `./output/` directory
- **Watermarks:** Generated in `./watermarks/` directory
- **Temporary files:** Auto-cleaned in container

**🔒 Privacy Note:** All files are processed locally - nothing is sent to external servers.


## 🔧 Troubleshooting

### 🚫 Service Won't Start

**Check if Docker is running:**
```bash
docker --version
docker-compose --version
```

**Check container status:**
```bash
docker-compose ps
```

**View startup logs:**
```bash
docker-compose logs
```

**Common issues:**
- Port 8080 already in use: `docker-compose up -d --scale md-pdf-watermark=0` then change port in `docker-compose.yml`
- Insufficient disk space: `docker system df`
- Permission issues: `sudo chown -R $USER:$USER .`

### 🌐 Can't Access Web Interface

- **Port blocked by firewall:** Check firewall settings for port 8080
- **Wrong URL:** Ensure you're using `http://localhost:8080` (not HTTPS)
- **Container not healthy:** `docker-compose ps` should show "Up" status
- **Port conflict:** Change port in `docker-compose.yml` if 8080 is busy

### 📄 File Processing Issues

**Upload fails:**
- Check file size limits (default: 100MB)
- Supported formats: PDF, MD, PNG, JPG
- Ensure write permissions on host directories

**Processing errors:**
- View container logs: `docker-compose logs -f md-pdf-watermark`
- Check available disk space
- Verify Docker has enough memory allocated

### 🔤 Chinese Font Issues

**Text rendering problems:**
- Container includes Noto CJK fonts by default
- For custom fonts, mount font directory: `-v /path/to/fonts:/usr/share/fonts`

**Watermark generation fails:**
- Check container logs for font loading errors
- Ensure sufficient container memory (>512MB recommended)

### 🔄 Updates & Maintenance

**Update to latest version:**
```bash
docker-compose pull
docker-compose up -d
```

**Reset everything:**
```bash
docker-compose down -v  # Removes volumes too
docker-compose up -d
```

### 📋 Getting Help

1. **Check logs:** `docker-compose logs -f`
2. **Test with sample files:** Use files from `input/` directory
3. **Verify Docker resources:** Ensure adequate CPU/memory allocation
4. **Network issues:** `docker network ls` and check connectivity

For detailed Docker troubleshooting, see [Docker Deployment Guide](README.Docker.md).

## 🤝 Contributing

We welcome contributions! This project is open source and community-driven.

- **🐛 Bug reports:** [GitHub Issues](https://github.com/pinyinjj/Markdown-to-PDF-Tool/issues)
- **💡 Feature requests:** [GitHub Issues](https://github.com/pinyinjj/Markdown-to-PDF-Tool/issues)
- **🛠️ Code contributions:** Pull requests are welcome!

## 📄 License

This project is licensed under GPL-3.0-or-later.

## ✨ Key Benefits Summary

- **🔒 Complete Privacy:** All processing happens locally on your machine
- **🚀 One-Command Setup:** `docker-compose up -d` gets you running
- **🛡️ No External Dependencies:** Everything is containerized and isolated
- **📱 Modern Web UI:** Intuitive interface for all operations
- **🌍 Multilingual:** English and Chinese language support
- **📦 Batch Processing:** Handle multiple files efficiently
- **🎨 Flexible Watermarking:** Text and image watermarks with full customization

**Ready to get started?** Just run `docker-compose up -d` and visit `http://localhost:8080`!