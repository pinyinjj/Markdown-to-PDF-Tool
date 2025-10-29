# Markdown to PDF Tool

[English](README.md) | **中文**

一个功能强大的Markdown转PDF工具，支持GitHub风格的Markdown语法、代码文档、Mermaid图表等，并自动添加水印。专为技术文档和代码项目设计，支持中文字体渲染和批量处理。

## 功能特性

- **Markdown → PDF（GitHub样式）**：表格、代码块、链接、图片；多语言代码高亮
- **Mermaid 支持**：流程图、时序图、甘特图自动渲染
- **水印能力**：文本/图片水印、透明度/角度/密度可调，亦可输出无水印
- **中文字体**：自动识别常见中文字体，渲染稳定
- **批量处理**：`input/` 全目录一键处理，结果输出至 `output/`
- **交互/默认双模式**：交互式最少参数配置；快速模式开箱即用
- **多语言界面**：中英自动/手动切换

适用：README/设计与架构（Mermaid）/API与代码文档、技术博客归档、项目报告与教学讲义；支持批量加水印或生成纯净PDF，便于团队分发协作。

## 快速开始

### 运行项目

```bash
git clone <repository-url>
cd md-pdf-watermark
python main.py
```

程序会引导您选择操作模式：

**1. 处理PDF文件（添加水印）**
- 为现有PDF文件添加水印
- 支持批量处理多个PDF文件

**2. 转换Markdown到PDF（添加水印）**
- 将Markdown文件转换为PDF并添加水印
- 支持Mermaid图表和代码高亮
- 自动检测中文字体

**3. 仅生成图片水印**
- 只生成水印图片，不处理任何文件
- 适合批量生成水印素材
- 支持文本和图片两种水印类型

**4. 转换Markdown到PDF（无水印）**
- 将Markdown文件转换为PDF，不添加水印
- 支持Mermaid图表和代码高亮
- 适合需要纯净PDF的场景

## 详细安装说明

### Windows 安装

1. **安装Python**
   - 从 [python.org](https://www.python.org/downloads/) 下载Python 3.8+
   - 安装时勾选"Add Python to PATH"

2. **安装依赖**
   ```cmd
   pip install -r requirements.txt
   playwright install
   ```

3. **系统依赖**（如果需要）
   ```cmd
   playwright install-deps
   ```

### macOS 安装

1. **安装Python**
   ```bash
   # 使用Homebrew
   brew install python
   
   # 或从python.org下载
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. **系统依赖**（如果需要）
   ```bash
   playwright install-deps
   ```

### Linux 安装

1. **安装Python**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   
   # CentOS/RHEL
   sudo yum install python3 python3-pip
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. **系统依赖**
   ```bash
   sudo playwright install-deps
   ```

## 国际化支持

### 语言设置

程序支持英文和中文两种界面语言：

#### 自动语言检测
程序会自动检测系统语言环境：
- 检测系统 `locale` 设置
- 检查环境变量 `LANG`
- 默认使用英文作为后备语言

#### 手动语言设置
```bash
# 使用英文界面
python main.py --lang en --interactive

# 使用中文界面
python main.py --lang zh --interactive

# 自动检测（默认）
python main.py --interactive
```

#### 语言切换
- 在交互式模式中，语言设置会影响所有界面文本
- 包括菜单选项、提示信息、错误消息等
- 不影响处理的文件内容

## 配置说明

### 水印配置

程序使用`WatermarkConfig`类管理所有配置：

```python
class WatermarkConfig:
    # 文本水印设置
    GENERATE_IMAGE_FROM_TEXT = True      # 是否从文本生成图片水印
    TEXT_WATERMARK_FILE = "watermarks/text_watermark.png"  # 文本水印图片文件名
    FONT_SIZE = 36                       # 字体大小
    TEXT_COLOR = (68, 68, 68, 220)      # 文本颜色RGBA
    PADDING = 20                         # 内边距
    
    # PDF水印参数
    WATERMARK_TYPE = "grid"              # 水印类型：grid/insert
    OPACITY = 0.2                        # 透明度
    ANGLE = 45                           # 旋转角度
    IMAGE_SCALE = 1.0                    # 图片缩放
    HORIZONTAL_BOXES = 3                 # 水平网格数
    VERTICAL_BOXES = 6                   # 垂直网格数
```

### 字体配置

程序会自动检测系统中文字体，支持：

- **Windows**: 微软雅黑、黑体、宋体、楷体、仿宋等
- **macOS**: PingFang、Hiragino Sans GB等  
- **Linux**: Noto Sans CJK等

如需指定字体，可设置环境变量：
```bash
export WATERMARK_FONT="/path/to/your/font.ttf"
```

## 使用方法

### 基本使用

1. **准备文件**：将PDF或Markdown文件放入`input/`目录
2. **运行程序**：执行`python main.py`
3. **查看结果**：处理后的文件在`output/`目录

#### 调整水印样式

修改`WatermarkConfig`中的相关参数：

```python
# 调整透明度
OPACITY = 0.3

# 调整角度
ANGLE = 30

# 调整网格密度
HORIZONTAL_BOXES = 4
VERTICAL_BOXES = 8
```

## 故障排除

### 常见问题

1. **Playwright浏览器未安装**
   ```bash
   playwright install
   ```

2. **中文字体未找到**
   - 确保系统已安装中文字体
   - 或设置`WATERMARK_FONT`环境变量

3. **watermark命令未找到**
   - 确保已安装`pdf-watermark`包
   - 检查虚拟环境是否正确激活

4. **权限问题**
   ```bash
   # Linux/macOS
   sudo playwright install-deps
   ```

### 调试模式

程序会输出详细的处理信息，包括：
- 文件处理状态
- 水印生成过程
- 错误信息

## 依赖包说明

| 包名 | 版本 | 用途 |
|------|------|------|
| Pillow | >=9.0.0 | 图像处理，生成文本水印图片 |
| markdown | >=3.4.0 | Markdown文件处理 |
| playwright | >=1.30.0 | 浏览器自动化，PDF渲染 |
| pdf-watermark | >=0.1.0 | PDF水印添加 |

## 许可证

本项目采用 GPL-3.0-or-later 许可证发布。

---

**注意**：首次运行可能需要下载Playwright浏览器，请确保网络连接正常。
