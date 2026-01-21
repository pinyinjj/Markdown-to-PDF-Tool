# Docker 部署指南

本文档介绍如何使用 Docker 部署 Markdown/PDF 水印工具。

## 前置要求

- Docker 20.10+ 
- Docker Compose 1.29+（可选，推荐）

## 快速开始

### 方式一：使用 Docker Compose（推荐）

1. **构建并启动容器**
   ```bash
   docker-compose up -d
   ```

2. **查看日志**
   ```bash
   docker-compose logs -f
   ```

3. **停止容器**
   ```bash
   docker-compose down
   ```

4. **访问应用**
   打开浏览器访问：http://localhost:8080

### 方式二：使用 Docker 命令

1. **构建镜像**
   ```bash
   docker build -t md-pdf-watermark:latest .
   ```

2. **运行容器**
   ```bash
   docker run -d \
     --name md-pdf-watermark \
     -p 8080:8080 \
     -v $(pwd)/output:/app/output \
     -v $(pwd)/temp_uploads:/app/temp_uploads \
     -v $(pwd)/watermarks:/app/watermarks \
     -v $(pwd)/input:/app/input \
     md-pdf-watermark:latest
   ```

3. **查看日志**
   ```bash
   docker logs -f md-pdf-watermark
   ```

4. **停止容器**
   ```bash
   docker stop md-pdf-watermark
   docker rm md-pdf-watermark
   ```

## 配置说明

### 端口配置

默认端口为 8080。如需修改端口：

**使用 Docker Compose：**
```yaml
ports:
  - "3000:8080"  # 主机端口:容器端口
```

**使用 Docker 命令：**
```bash
docker run -p 3000:8080 ...
```

### 数据持久化

以下目录已配置为数据卷，确保数据在容器重启后仍然保留：

- `./output` - 输出文件
- `./temp_uploads` - 临时上传文件
- `./watermarks` - 生成的水印文件
- `./input` - 输入文件（可选）

### 环境变量

可以通过环境变量配置应用行为：

```yaml
environment:
  - PYTHONUNBUFFERED=1
  # 添加其他环境变量
```

## 常见问题

### 1. 容器启动失败

检查日志：
```bash
docker-compose logs md-pdf-watermark
```

或
```bash
docker logs md-pdf-watermark
```

### 2. 端口被占用

修改 `docker-compose.yml` 中的端口映射，或停止占用端口的其他服务。

### 3. 权限问题

确保 Docker 有权限访问挂载的目录：
```bash
sudo chown -R $USER:$USER output temp_uploads watermarks input
```

### 4. 中文字体显示问题

镜像已包含 Noto CJK 字体。如果仍有问题，可以：

1. 检查容器内字体安装：
   ```bash
   docker exec md-pdf-watermark fc-list | grep -i cjk
   ```

2. 通过环境变量指定字体路径：
   ```bash
   export WATERMARK_FONT="/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
   ```

## 生产环境部署建议

1. **使用反向代理**（如 Nginx）处理 HTTPS 和域名
2. **配置资源限制**：
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```
3. **定期备份** `output` 和 `watermarks` 目录
4. **监控容器健康状态**：容器已配置健康检查
5. **使用 Docker Swarm 或 Kubernetes** 进行多实例部署

## 更新应用

```bash
# 停止旧容器
docker-compose down

# 重新构建镜像
docker-compose build --no-cache

# 启动新容器
docker-compose up -d
```

## 故障排查

查看容器状态：
```bash
docker-compose ps
```

进入容器调试：
```bash
docker exec -it md-pdf-watermark /bin/bash
```

检查 Playwright 浏览器安装：
```bash
docker exec md-pdf-watermark playwright --version
```
