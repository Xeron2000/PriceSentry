# PriceSentry Docker 部署指南

## 快速开始

### 1. 本地开发环境

```bash
# 克隆项目
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry

# 创建虚拟环境
uv venv
source .venv/bin/activate

# 安装依赖
uv sync

# 配置应用
cp config/config.yaml.example config/config.yaml
# 编辑 config/config.yaml 填入你的配置

# 运行应用
python main.py
```

### 2. Docker 部署

#### 使用 Docker Compose（推荐）

```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

#### 单独构建和运行

```bash
# 构建镜像
docker build -t pricesentry .

# 运行容器
docker run -d \
  --name pricesentry \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  pricesentry
```

## 配置说明

### 环境变量

- `PYTHONPATH=/app` - Python 路径设置
- `PYTHONUNBUFFERED=1` - 禁用 Python 输出缓冲
- `LOG_LEVEL=INFO` - 日志级别

### 数据卷

- `./config:/app/config` - 配置文件目录
- `./logs:/app/logs` - 日志文件目录
- `redis_data:/data` - Redis 数据持久化

### 网络配置

- 创建了 `pricesentry-network` 专用网络
- PriceSentry 和 Redis 在同一网络中通信

## 服务架构

```
┌─────────────────┐    ┌─────────────────┐
│   PriceSentry   │    │      Redis      │
│   Container     │◄──►│    Container    │
│                 │    │                 │
│ - Python 3.11   │    │ - Redis 7       │
│ - uv 包管理     │    │ - 持久化存储    │
│ - 配置挂载      │    │ - 端口 6379     │
│ - 日志挂载      │    │                 │
└─────────────────┘    └─────────────────┘
```

## 管理命令

### 查看服务状态

```bash
# 查看所有容器
docker compose ps

# 查看 PriceSentry 日志
docker compose logs pricesentry

# 查看 Redis 日志
docker compose logs redis
```

### 进入容器

```bash
# 进入 PriceSentry 容器
docker compose exec pricesentry bash

# 进入 Redis 容器
docker compose exec redis bash
```

### 数据管理

```bash
# 备份 Redis 数据
docker compose exec redis redis-cli SAVE
docker cp pricesentry-redis:/data/dump.rdb ./redis_backup.rdb

# 恢复 Redis 数据
docker cp ./redis_backup.rdb pricesentry-redis:/data/dump.rdb
docker compose restart redis
```

## 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 检查日志
   docker compose logs pricesentry
   
   # 检查配置文件
   ls -la config/
   ```

2. **Redis 连接失败**
   ```bash
   # 检查 Redis 状态
   docker compose exec redis redis-cli ping
   
   # 检查网络连接
   docker compose exec pricesentry telnet redis 6379
   ```

3. **权限问题**
   ```bash
   # 检查文件权限
   ls -la config/ logs/
   
   # 修复权限
   sudo chown -R $USER:$USER config/ logs/
   ```

### 性能优化

1. **内存限制**
   ```bash
   # 限制容器内存使用
   docker run -m 512m pricesentry
   ```

2. **日志轮转**
   ```bash
   # 在 docker-compose.yml 中添加
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

## 生产环境建议

### 安全配置

1. **使用非 root 用户**
   - Dockerfile 中已配置
   - 运行时使用 `app` 用户

2. **网络隔离**
   - 使用专用网络
   - 不暴露不必要的端口

3. **配置管理**
   - 使用 Docker secrets 或环境变量
   - 敏感信息不写入配置文件

### 监控和日志

1. **日志收集**
   ```bash
   # 配置日志驱动
   docker compose up -d --log-driver=json-file
   ```

2. **资源监控**
   ```bash
   # 查看资源使用
   docker stats
   ```

### 备份策略

1. **配置备份**
   ```bash
   # 备份配置目录
   tar -czf config_backup.tar.gz config/
   ```

2. **数据备份**
   ```bash
   # 备份 Redis 数据
   docker exec pricesentry-redis redis-cli BGSAVE
   ```

## 升级和维护

### 应用升级

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker compose build

# 重启服务
docker compose up -d
```

### 依赖更新

```bash
# 更新 Python 依赖
uv sync

# 更新 Redis 镜像
docker pull redis:7-alpine
```

### 清理维护

```bash
# 清理未使用的镜像
docker image prune

# 清理未使用的卷
docker volume prune

# 清理未使用的网络
docker network prune
```

## 支持和反馈

如果遇到问题或需要帮助，请：

1. 查看项目文档
2. 检查 GitHub Issues
3. 提交新的 Issue

---

**注意**: 本 Docker 配置为 PriceSentry 提供了基础的生产环境部署方案。根据实际需求，你可能需要调整配置参数。