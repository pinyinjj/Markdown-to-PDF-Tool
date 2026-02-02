# Markdown to PDF Converter & Watermarker

[![Docker Image CI](https://github.com/pinyinjj/Markdown-to-PDF-Tool/actions/workflows/docker-image.yml/badge.svg)](https://github.com/pinyinjj/Markdown-to-PDF-Tool/actions/workflows/docker-image.yml)
[![License](https://img.shields.io/github/license/pinyinjj/Markdown-to-PDF-Tool)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/pinyinjj/Markdown-to-PDF-Tool?style=social)](https://github.com/pinyinjj/Markdown-to-PDF-Tool/star)
[![GitHub Forks](https://img.shields.io/github/forks/pinyinjj/Markdown-to-PDF-Tool?style=social)](https://github.com/pinyinjj/Markdown-to-PDF-Tool/fork)

**English** | [中文](README.zh.md)

A secure, privacy-focused, self-hosted web application for converting Markdown to PDF with GitHub-style rendering, Mermaid diagrams, and automatic watermarking. Deploy it effortlessly using Docker or Docker Compose for complete control over your data and processing environment.

## ✨ Features

-   **🔒 Local & Private Processing**: All conversions and watermarking happen on your machine; your sensitive data never leaves your control.
-   **🌐 Intuitive Web Interface**: A modern, responsive UI for easy file uploads, configuration, and batch processing via drag-and-drop.
-   **📝 Advanced Markdown Rendering**:
    *   GitHub-flavored Markdown support.
    *   Syntax highlighting for code blocks (powered by Highlight.js).
    *   Integrated Mermaid.js for stunning flowcharts, sequence diagrams, Gantt charts, and more.
    *   KaTeX support for mathematical equations.
    *   Emoji and Task List support.
-   **💧 Smart Watermarking**: Apply customizable text or image watermarks to your PDFs with fine-tuned control over opacity, angle, scale, and density.
-   **📄 Versatile PDF Operations**:
    *   Convert Markdown to PDF.
    *   Add watermarks to existing PDF files.
    *   Generate standalone watermark images.
-   **🌍 Multilingual Support**: User interface available in English and Chinese, with automatic language detection.
-   **✅ CJK Font Adaptation**: Intelligent auto-detection and inclusion of CJK fonts for perfect rendering of East Asian languages.
-   **🐳 Docker-First Deployment**: Designed for easy, cross-platform deployment with Docker and Docker Compose.

## 🚀 Getting Started

The quickest way to get `Markdown to PDF Converter & Watermarker` up and running is with a single Docker command.

### Prerequisites

Ensure you have [Docker](https://docs.docker.com/get-docker/) installed on your system.

### Launch the Service

```bash
docker run -d \
  --name md-pdf-watermark \
  -p 8080:8080 \
  -v "$(pwd)/output:/app/output" \
  -v "$(pwd)/watermarks:/app/watermarks" \
  -v "$(pwd)/input:/app/input" \
  -v "$(pwd)/temp_uploads:/app/temp_uploads" \
  ghcr.io/pinyinjj/markdown-to-pdf-tool:latest
```
This command will automatically download the latest Docker image (if not available locally), create a container named `md-pdf-watermark`, map port `8080` from your host to the container, and mount local directories for persistent storage of input files, generated PDFs, temporary uploads, and watermarks.

### Access the Web Interface

Open your web browser and navigate to:

```
http://localhost:8080
```

You should see the application's user interface.

## ⚙️ Configuration

The application offers flexible configuration options:

### Web Interface Settings

Most dynamic settings, such as watermark text, opacity, angle, and processing modes, are managed directly through the intuitive web interface. Your preferences are saved per session.

**Available Operations:**

*   **Markdown to PDF**: Convert Markdown files with GitHub-style rendering, code highlighting, Mermaid, and KaTeX.
*   **Process PDF with Watermark**: Add custom watermarks to existing PDF documents.
*   **Generate Watermark Only**: Create and customize text or image watermarks for later use.

### Environment Variables (Advanced)

While `config.py` defines default parameters, you can override certain aspects using environment variables for Docker deployments.
*   Currently, the application relies primarily on `config.py` for default values.
*   **To customize `config.py` settings:**
    1.  Fork the repository and modify `config.py` directly.
    2.  Build your custom Docker image.
    3.  Alternatively, you could extend the `Dockerfile` to copy your custom `config.py` or modify the entrypoint script to set environment variables that your application then reads.
    *(Future development might include direct support for common settings via environment variables.)*

**Example of a potential environment variable usage (if implemented in the application):**

```yaml
services:
  md-pdf-watermark:
    environment:
      - FONT_SIZE=48
      - WATERMARK_OPACITY=0.3
      # ... other settings
```

## 🤝 Contributing

We warmly welcome contributions to this project! It's open-source and community-driven.

*   **🐛 Bug Reports**: Found a bug? Please report it on [GitHub Issues](https://github.com/pinyinjj/Markdown-to-PDF-Tool/issues).
*   **💡 Feature Requests**: Have an idea for a new feature or improvement? Open a feature request issue.
*   **🛠️ Code Contributions**: Want to contribute code? Fork the repository, make your changes, and submit a pull request. Please ensure your code adheres to existing style and passes tests.

## 📄 License

This project is licensed under the [GPL-3.0-or-later license](LICENSE).

---
