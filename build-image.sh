#!/bin/bash
# Docker 镜像构建脚本
# Usage: ./build-image.sh [tag]

set -e

# 默认标签
TAG=${1:-"md-pdf-watermark:latest"}

echo "=========================================="
echo "构建 Docker 镜像: $TAG"
echo "=========================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: 未找到 Docker，请先安装 Docker"
    exit 1
fi

# 构建镜像
echo "开始构建镜像..."
docker build -t "$TAG" .

echo ""
echo "=========================================="
echo "镜像构建完成！"
echo "=========================================="
echo ""
echo "镜像名称: $TAG"
echo ""
echo "使用以下命令查看镜像:"
echo "  docker images | grep md-pdf-watermark"
echo ""
echo "运行容器:"
echo "  docker run -d -p 8080:8080 --name md-pdf-watermark $TAG"
echo ""
echo "或使用 docker-compose:"
echo "  docker-compose up -d"
echo ""
