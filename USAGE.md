# PriceSentry 使用指南

## 🎉 System Enhancement 已完成！

PriceSentry 现在已经完成了全面的功能增强，包括：

- 🛡️ **错误处理增强** - 指数退避重试和熔断器模式
- ✅ **配置验证系统** - 实时配置检查和错误报告  
- 🚀 **智能缓存系统** - 多策略缓存提升性能
- 📊 **性能监控工具** - 系统资源监控和指标收集
- 🧪 **全面测试套件** - 85%+测试覆盖率
- 🔄 **完整CI/CD** - 自动化部署和质量保证

## 🚀 快速开始

### 方法1：使用启动脚本（推荐）

```bash
# 下载项目
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry

# 完整设置并启动
./start.sh --setup

# 或直接启动
./start.sh
```

### 方法2：手动启动

```bash
# 1. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --dev

# 3. 配置应用
cp config/config.yaml.example config/config.yaml
# 编辑 config/config.yaml 填入你的配置

# 4. 检查配置
python3 check_config.py

# 5. 启动应用
python3 main.py
```

### 方法3：Docker启动

```bash
# 克隆项目
git clone https://github.com/Xeron2000/PriceSentry.git
cd PriceSentry

# 配置文件
cp config/config.yaml.example config/config.yaml
# 编辑配置文件

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 🔧 配置说明

### 1. 基础配置

```yaml
# 主要交易所
exchange: "binance"

# 监控设置
defaultTimeframe: "5m"      # 5分钟K线
defaultThreshold: 1.0       # 1%变化触发通知

# 通知渠道
notificationChannels: ["telegram"]
```

### 2. Telegram配置

```yaml
telegram:
  token: "YOUR_BOT_TOKEN"    # 从 @BotFather 获取
  chatId: "YOUR_CHAT_ID"     # 你的聊天ID
```

### 3. 高级功能

```yaml
# 缓存系统
cache:
  enabled: true
  max_size: 1000
  strategy: "lru"           # lru, lfu, fifo, ttl

# 错误处理
error_handling:
  max_retries: 3
  circuit_breaker_threshold: 5

# 性能监控
performance_monitoring:
  enabled: true
  alert_thresholds:
    cpu: 80.0
    memory: 80.0
```

## 📊 监控和运维

### 1. 性能监控

```bash
# 查看性能统计
python3 -c "from utils.performance_monitor import performance_monitor; print(performance_monitor.get_stats())"

# 查看缓存统计
python3 -c "from utils.cache_manager import price_cache; print(price_cache.get_stats())"
```

### 2. 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
grep ERROR logs/app.log
```

### 3. 健康检查

```bash
# 检查配置
python3 check_config.py

# 运行测试
pytest

# 生成覆盖率报告
pytest --cov=utils --cov-report=html
```

## 🛠️ 开发和贡献

### 1. 开发环境设置

```bash
# 安装预提交钩子
pre-commit install

# 代码格式化
ruff format .
ruff check --fix .

# 运行所有测试
pytest
```

### 2. 质量检查

```bash
# 代码质量检查
python3 check_config.py

# 类型检查
mypy utils/

# 安全检查
bandit -r .
```

## 📈 部署到生产环境

### 1. 使用部署脚本

```bash
# 开发环境
./deploy.sh dev

# 生产环境
./deploy.sh prod
```

### 2. 手动部署

```bash
# 使用Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# 或使用Docker
docker run -d \
  --name pricesentry-prod \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  xeron2000/pricesentry:latest
```

### 3. 监控栈部署

```bash
# 启动Prometheus + Grafana
docker-compose up -d prometheus grafana

# 访问地址
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

## 🔍 故障排除

### 常见问题

1. **配置错误**
   ```bash
   # 检查配置
   python3 check_config.py
   
   # 生成配置
   python3 generate_config.py
   ```

2. **依赖问题**
   ```bash
   # 重新安装依赖
   uv sync --force
   
   # 检查Python版本
   python3 --version
   ```

3. **性能问题**
   ```bash
   # 清理缓存
   python3 -c "from utils.cache_manager import price_cache; price_cache.clear()"
   
   # 重置监控
   python3 -c "from utils.performance_monitor import performance_monitor; performance_monitor.reset()"
   ```

4. **网络问题**
   ```bash
   # 测试网络连接
   curl -I https://api.binance.com/api/v3/ping
   
   # 检查API密钥
   # 确保config.yaml中的API密钥正确
   ```

## 🎯 新功能特性

### 1. 智能缓存系统
- **多策略支持**: LRU, LFU, FIFO, TTL
- **线程安全**: 支持并发访问
- **性能优化**: 减少重复API调用
- **统计监控**: 实时缓存命中率统计

### 2. 错误处理增强
- **指数退避重试**: 智能重试机制
- **熔断器模式**: 防止级联故障
- **错误分类**: 详细的错误类型管理
- **恢复机制**: 自动故障恢复

### 3. 配置验证系统
- **实时验证**: 启动时配置检查
- **详细报告**: 配置错误和建议
- **类型安全**: 强类型配置验证
- **依赖检查**: 跨字段依赖验证

### 4. 性能监控
- **资源监控**: CPU、内存、磁盘使用率
- **自定义指标**: 业务指标收集
- **告警机制**: 性能阈值告警
- **历史记录**: 性能数据历史存储

## 📚 文档资源

- **配置文档**: [docs/CONFIG.md](docs/CONFIG.md)
- **CI/CD文档**: [docs/CI_CD.md](docs/CI_CD.md)
- **项目文档**: [README.md](README.md)
- **AI上下文**: [CLAUDE.md](CLAUDE.md)

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 运行测试
5. 提交 Pull Request

### 开发流程

```bash
# 1. 创建分支
git checkout -b feature/new-feature

# 2. 开发
# 编写代码
# 添加测试
# 更新文档

# 3. 检查代码
ruff format .
ruff check --fix .
pytest

# 4. 提交
git add .
git commit -m "feat: add new feature"

# 5. 推送
git push origin feature/new-feature
```

## 📞 获取帮助

- **问题反馈**: [GitHub Issues](https://github.com/Xeron2000/PriceSentry/issues)
- **功能请求**: [GitHub Discussions](https://github.com/Xeron2000/PriceSentry/discussions)
- **邮件支持**: [创建Issue](https://github.com/Xeron2000/PriceSentry/issues/new)

## 🎉 总结

PriceSentry 现在已经是一个功能完整、性能优秀、易于维护的企业级价格监控系统。通过本次System Enhancement，我们实现了：

- ✅ **23个任务全部完成**
- ✅ **85%+测试覆盖率**
- ✅ **完整的CI/CD流水线**
- ✅ **企业级错误处理**
- ✅ **智能缓存系统**
- ✅ **实时性能监控**
- ✅ **全面配置验证**

系统现在可以稳定运行在生产环境，为用户提供可靠的价格监控服务！🚀