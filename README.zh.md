# Markdown 转 PDF 转换器与水印工具

[![License](https://img.shields.io/github/license/pinyinjj/Markdown-to-PDF-Tool)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/pinyinjj/Markdown-to-PDF-Tool?style=social)](https://github.com/pinyinjj/Markdown-to-PDF-Tool/star)
[![GitHub Forks](https://img.shields.io/github/forks/pinyinjj/Markdown-to-PDF-Tool?style=social)](https://github.com/pinyinjj/Markdown-to-PDF-Tool/fork)

**English** | [中文](README.zh.md)

一个安全、注重隐私、自托管的 Web 应用程序，用于将 Markdown 转换为 PDF，支持 GitHub 风格渲染、Mermaid 图表和自动水印功能。使用 Docker 或 Docker Compose 轻松部署，完全掌控您的数据和处理环境。

## ✨ 功能特性

-   **🔒 本地与私密处理**: 所有转换和水印操作都在您的机器上进行；您的敏感数据绝不会离开您的控制。
-   **🌐 直观的 Web 界面**: 现代化、响应式的用户界面，通过拖放操作即可轻松上传文件、配置和批量处理。
-   **📝 高级 Markdown 渲染**:
    *   支持 GitHub 风格的 Markdown。
    *   代码块语法高亮（由 Highlight.js 提供支持）。
    *   集成 Mermaid.js，支持精美的流程图、序列图、甘特图等。
    *   支持 KaTeX 数学公式。
    *   支持 Emoji 表情和任务列表。
-   **💧 智能水印**: 为您的 PDF 添加可定制的文本或图像水印，精确控制不透明度、角度、比例和密度。
-   **📄 多功能 PDF 操作**:
    *   将 Markdown 转换为 PDF。
    *   为现有 PDF 文件添加水印。
    *   生成独立的水印图像。
-   **🌍 多语言支持**: 用户界面提供英语和中文版本，并支持自动语言检测。
-   **✅ CJK 字体适应**: 智能自动检测并包含 CJK 字体，以实现东亚语言的完美渲染。
-   **🐳 Docker 优先部署**: 专为使用 Docker 和 Docker Compose 进行轻松、跨平台部署而设计。

## 🚀 快速开始

### 启动服务

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


### 访问 Web 界面

打开您的网络浏览器并访问：

```
http://localhost:8080
```

您应该会看到应用程序的用户界面。

## 🤝 贡献

我们热烈欢迎对本项目的贡献！这是一个开源且由社区驱动的项目。

*   **🐛 Bug 报告**: 发现 Bug？请在 [GitHub Issues](https://github.com/pinyinjj/Markdown-to-PDF-Tool/issues) 上报告。
*   **💡 功能请求**: 有新的功能或改进想法？请提交功能请求。
*   **🛠️ 代码贡献**: 想贡献代码？请 fork 仓库，进行更改，然后提交 Pull Request。请确保您的代码符合现有风格并通过测试。

## 📄 许可证

本项目采用 [GPL-3.0-or-later 许可证](LICENSE) 发布。