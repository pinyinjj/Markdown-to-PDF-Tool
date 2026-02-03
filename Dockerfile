# ============================================
# Stage 1: Builder - Install dependencies and browsers
# ============================================
FROM python:3.12.3-slim AS builder

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

# ============================================
# Stage 2: Runtime - Final image
# ============================================
FROM python:3.12.3-slim AS runtime

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PATH="/usr/local/bin:${PATH}"

# Install runtime system dependencies + fontconfig for font management
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    fontconfig \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/* && \
    mkdir -p output temp_uploads watermarks input

# Copy packages and playwright from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /ms-playwright /ms-playwright

# Copy project files
COPY . .

# --- 关键修改：注册自定义字体到系统 ---
# 1. 创建系统字体目录
# 2. 将项目中的 VF 字体拷贝到系统目录
# 3. 刷新系统字体缓存
RUN mkdir -p /usr/share/fonts/truetype/custom && \
    cp assets/fonts/NotoSansMonoCJKsc-VF.otf /usr/share/fonts/truetype/custom/ 2>/dev/null || true && \
    fc-cache -fv
# ----------------------------------

# Clean project cache
RUN find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find . -name "*.pyc" -delete

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080')" || exit 1

CMD ["python", "start_webui.py", "--host", "0.0.0.0", "--port", "8080", "--no-open"]