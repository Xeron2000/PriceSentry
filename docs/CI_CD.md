# CI/CD 配置文档

## 概述

PriceSentry 项目配置了完整的 CI/CD 流水线，包括代码质量检查、测试、安全扫描和自动部署。

## 工作流

### 1. 主 CI/CD 流水线 (`.github/workflows/ci-cd.yml`)

**触发条件**:
- 推送到 `main` 或 `develop` 分支
- 创建针对 `main` 分支的 Pull Request

**包含阶段**:
1. **测试阶段**: 在多个 Python 版本 (3.8-3.12) 上运行测试
2. **安全扫描**: 使用 bandit 和 safety 进行安全检查
3. **性能测试**: 运行性能基准测试
4. **构建阶段**: 构建 Python 包
5. **Docker 构建**: 构建 Docker 镜像
6. **部署阶段**: 自动部署到生产环境

### 2. 代码质量门禁 (`.github/workflows/quality-gate.yml`)

**功能**:
- 代码格式化检查 (ruff format)
- 代码质量检查 (ruff check)
- 类型检查 (mypy)
- 质量分数评估 (最低 80 分)

### 3. 依赖分析 (`.github/workflows/dependency-analysis.yml`)

**功能**:
- 依赖安全审计 (pip-audit)
- 过时依赖检查
- 许可证合规检查

## 预提交钩子 (`.pre-commit-config.yaml`)

安装预提交钩子：
```bash
pre-commit install
```

包含的检查：
- 代码格式化 (ruff)
- 类型检查 (mypy)
- 导入排序 (isort)
- 基础检查 (trailing whitespace, YAML 检查等)
- 安全检查 (bandit)
- 依赖安全检查 (pip-safety)

## Docker 部署

### 本地开发
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 生产部署
```bash
# 使用部署脚本
./deploy.sh prod

# 或手动部署
docker-compose -f docker-compose.prod.yml up -d
```

### 环境配置
- `dev`: 开发环境
- `staging`: 预发布环境
- `prod`: 生产环境
- `local`: 本地环境

## 监控和日志

### Prometheus + Grafana 监控
```bash
# 启动监控栈
docker-compose up -d prometheus grafana

# 访问 Grafana: http://localhost:3000
# 访问 Prometheus: http://localhost:9090
```

### 健康检查
- 应用健康检查: 每 30 秒检查一次
- Redis 连接检查
- 自动重启策略

## 安全最佳实践

### 代码安全
- 使用 bandit 进行静态安全分析
- 使用 safety 检查已知漏洞
- 依赖许可证合规检查

### 部署安全
- 非 root 用户运行容器
- 网络隔离
- 环境变量管理
- 敏感信息加密

### 配置安全
- 配置文件验证
- 最小权限原则
- 安全的默认设置

## 性能优化

### 构建优化
- 多阶段构建
- 层缓存优化
- 并行构建

### 运行时优化
- 资源限制配置
- 内存优化
- 网络优化

## 故障排除

### 常见问题
1. **Docker 构建失败**: 检查 Dockerfile 和依赖
2. **测试失败**: 查看测试日志和覆盖率报告
3. **部署失败**: 检查环境配置和权限
4. **性能问题**: 查看性能监控报告

### 日志位置
- CI/CD 日志: GitHub Actions 页面
- 应用日志: `./logs/` 目录
- Docker 日志: `docker-compose logs`

### 监控指标
- 代码质量分数
- 测试覆盖率
- 性能基准
- 安全漏洞数量
- 部署成功率

## 扩展和定制

### 添加新的检查
1. 在相应的工作流文件中添加步骤
2. 更新预提交配置
3. 更新质量门禁标准

### 添加新的环境
1. 创建新的 docker-compose 文件
2. 更新部署脚本
3. 配置环境变量

### 集成其他服务
- 添加数据库服务
- 集成消息队列
- 添加缓存服务

## 维护和更新

### 定期维护
- 更新依赖版本
- 更新基础镜像
- 更新安全补丁
- 清理旧版本

### 版本管理
- 语义化版本控制
- 标签和发布管理
- 回滚策略

## 联系和支持

- GitHub Issues: [报告问题](https://github.com/Xeron2000/PriceSentry/issues)
- 文档: [项目文档](./README.md)
- 支持: 通过 GitHub Issues 联系