
FROM python:3.12.3
# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 安装系统依赖（包括中文字体）
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright 系统依赖
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    # 中文字体支持
    fonts-noto-cjk \
    fonts-noto-cjk-extra \
    # 其他字体
    fonts-liberation \
    fonts-dejavu-core \
    # 清理缓存
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器
RUN playwright install chromium \
    && playwright install-deps chromium

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p output temp_uploads watermarks input

# 暴露端口（NiceGUI 默认端口）
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080')" || exit 1

# 启动命令
CMD ["python", "start_webui.py", "--host", "0.0.0.0", "--port", "8080", "--no-open"]
