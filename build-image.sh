#!/bin/bash
# Docker image build script
# Usage: ./build-image.sh [tag]

set -e

# Default tag
TAG=${1:-"md-pdf-watermark:latest"}

echo "=========================================="
echo "Building Docker image: $TAG"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker not found, please install Docker first"
    exit 1
fi

# Build image
echo "Starting image build..."
docker build -t "$TAG" .

echo ""
echo "=========================================="
echo "Image build completed!"
echo "=========================================="
echo ""
echo "Image name: $TAG"
echo ""
echo "View image with:"
echo "  docker images | grep md-pdf-watermark"
echo ""
echo "Run container:"
echo "  docker run -d -p 8080:8080 --name md-pdf-watermark $TAG"
echo ""
echo "Or use docker-compose:"
echo "  docker-compose up -d"
echo ""
