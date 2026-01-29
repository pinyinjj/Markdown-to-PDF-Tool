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
    libgtk-3-0 fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium && \
    # Clean Python cache (But KEEP .dist-info)
    find /usr/local/lib/python3.12/site-packages -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.12/site-packages -name "*.pyc" -delete && \
    find /usr/local/lib/python3.12/site-packages -name "*.pyo" -delete

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

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0 \
    libgtk-3-0 fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean && \
    mkdir -p output temp_uploads watermarks input

# Copy packages (Metadata included now)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /ms-playwright /ms-playwright

COPY . .

# Clean project cache
RUN find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find . -name "*.pyc" -delete && \
    find . -name "*.pyo" -delete && \
    find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080')" || exit 1

CMD ["python", "start_webui.py", "--host", "0.0.0.0", "--port", "8080", "--no-open"]