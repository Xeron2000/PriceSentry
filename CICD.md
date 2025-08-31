# PriceSentry CI/CD 简化指南

## 🔄 CI/CD 流水线概览

### 主要工作流

#### 1. 主流水线 (`.github/workflows/ci-cd.yml`)

**触发条件**：
- 推送到 `main` 或 `develop` 分支
- 创建针对 `main` 分支的 PR

**包含的作业**：
- **test**: 多 Python 版本测试 + 代码质量检查
- **security**: 安全扫描 (bandit + safety)
- **build**: Docker 镜像构建和推送 (仅 main 分支)

#### 2. 依赖分析 (`.github/workflows/dependency-analysis.yml`)

**触发条件**：
- 每周日自动运行
- 依赖文件变更时运行

**功能**：
- 依赖安全审计
- 检查过时的依赖

#### 3. 质量门禁 (`.github/workflows/quality-gate.yml`)

**触发条件**：
- PR 创建和更新
- 推送到任意分支

**检查项目**：
- 代码格式化 (ruff format)
- 代码规范检查 (ruff check)
- 类型检查 (mypy)

## 🚀 快速使用

### 本地开发

```bash
# 安装依赖
uv sync

# 代码检查
uv run ruff check .
uv run ruff format --check .

# 运行测试
uv run pytest

# 类型检查
uv run mypy utils/
```

### 提交代码

```bash
# 提交前确保所有检查通过
uv run ruff check .
uv run ruff format .
uv run pytest
uv run mypy utils/

# 提交代码
git add .
git commit -m "feat: add new feature"
git push origin main
```

### 部署到生产环境

```bash
# 使用部署脚本
./deploy.sh prod

# 或者手动部署
docker build -t pricesentry .
docker run -d pricesentry
```

## 📊 检查清单

### 代码提交前检查

- [ ] 代码格式化正确 (`ruff format`)
- [ ] 代码规范检查通过 (`ruff check`)
- [ ] 类型检查通过 (`mypy`)
- [ ] 单元测试通过 (`pytest`)
- [ ] 安全检查通过 (`bandit`, `safety`)
- [ ] 文档更新 (如果需要)

### 部署前检查

- [ ] 所有 CI/CD 流水线通过
- [ ] Docker 镜像构建成功
- [ ] 配置文件正确
- [ ] 测试环境验证通过

## 🔧 配置说明

### 环境变量

**CI/CD 环境变量**：
- `DOCKERHUB_USERNAME`: Docker Hub 用户名
- `DOCKERHUB_TOKEN`: Docker Hub 访问令牌

**应用环境变量**：
- `ENVIRONMENT`: 运行环境 (dev/staging/prod)
- `LOG_LEVEL`: 日志级别
- `PYTHONPATH`: Python 路径

### 依赖管理

**使用 uv 管理依赖**：
```bash
# 添加依赖
uv add package_name

# 移除依赖
uv remove package_name

# 更新依赖
uv update

# 导出依赖
uv pip compile requirements.in -o requirements.txt
```

## 🐳 Docker 部署

### 构建镜像

```bash
# 本地构建
docker build -t pricesentry .

# 多阶段构建
docker build --target=production -t pricesentry:prod .
```

### 运行容器

```bash
# 使用 docker-compose
docker compose up -d

# 单独运行
docker run -d \
  --name pricesentry \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  pricesentry
```

## 📈 监控和日志

### 日志查看

```bash
# 查看容器日志
docker compose logs -f pricesentry

# 查看特定时间日志
docker compose logs --since 1h pricesentry
```

### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看容器状态
docker compose ps
```

## 🛠️ 故障排除

### CI/CD 失败

1. **测试失败**
   ```bash
   # 本地重现测试
   uv run pytest --cov=utils --cov-report=term-missing
   ```

2. **代码格式化失败**
   ```bash
   # 自动格式化
   uv run ruff format .
   ```

3. **安全检查失败**
   ```bash
   # 查看安全问题
   uv run bandit -r .
   uv run safety check
   ```

### Docker 部署失败

1. **构建失败**
   ```bash
   # 查看构建日志
   docker build --no-cache -t pricesentry .
   ```

2. **容器启动失败**
   ```bash
   # 查看容器日志
   docker compose logs pricesentry
   ```

3. **依赖问题**
   ```bash
   # 检查依赖
   uv sync --frozen
   ```

## 📚 最佳实践

### 代码质量

1. **遵循 PEP 8 规范**
2. **编写类型注解**
3. **保持函数单一职责**
4. **编写单元测试**
5. **定期更新依赖**

### 部署流程

1. **先在测试环境验证**
2. **使用版本标签**
3. **滚动更新策略**
4. **备份重要数据**
5. **监控部署状态**

### 安全考虑

1. **使用非 root 用户**
2. **定期安全扫描**
3. **最小权限原则**
4. **敏感信息管理**
5. **网络隔离**

## 🔄 工作流程图

```
Git Push → CI/CD 触发 → 测试 → 安全检查 → 质量检查 → 构建镜像 → 部署
    ↓
PR 创建 → 代码审查 → 质量门禁 → 合并到 main
    ↓
定时任务 → 依赖分析 → 安全审计 → 报告生成
```

---

**注意**: 这个简化的 CI/CD 配置专注于核心功能，移除了复杂的监控服务和报告生成。如果需要更高级的功能，可以根据项目需求逐步添加。