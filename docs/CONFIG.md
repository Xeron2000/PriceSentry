# PriceSentry 配置说明文档

## 概述

PriceSentry 使用 YAML 配置文件来管理所有设置。配置文件分为基础配置和高级配置两个部分。

## 快速开始

1. 复制配置文件模板：
```bash
cp config/config.yaml.example config/config.yaml
```

2. 编辑配置文件，填入你的设置：
```bash
nano config/config.yaml
```

3. 验证配置文件：
```bash
python -c "from utils.config_validator import config_validator; print(config_validator.validate_config('config/config.yaml'))"
```

## 基础配置

### 交易所配置

```yaml
# 主要交易所
exchange: "okx"  # 选择主要监控的交易所

# 获取市场数据的交易所列表
exchanges:
  - "binance"
  - "okx"
  - "bybit"
```

### 监控设置

```yaml
# 时间周期
defaultTimeframe: "5m"  # 5分钟K线

# 价格变化阈值
defaultThreshold: 0.01  # 1%变化触发通知

# 交易对文件
symbolsFilePath: "config/symbols.txt"
```

### 通知设置

```yaml
# 通知渠道
notificationChannels: 
  - "telegram"
  # - "dingding"

# Telegram配置
telegram:
  token: "YOUR_TELEGRAM_BOT_TOKEN"
  chatId: "YOUR_CHAT_ID"

# 钉钉配置
dingding:
  webhook: "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
  secret: "YOUR_SECRET"
```

## 高级配置

### 缓存系统

```yaml
cache:
  enabled: true                    # 启用缓存
  max_size: 1000                   # 最大缓存条目
  default_ttl: 300                 # 缓存过期时间（秒）
  strategy: "lru"                  # 缓存策略
  cleanup_interval: 60             # 清理间隔
```

**缓存策略说明**：
- `lru`: 最近最少使用 - 淘汰最久未使用的数据
- `lfu`: 最少使用频率 - 淘汰使用次数最少的数据
- `fifo`: 先进先出 - 按添加顺序淘汰数据
- `ttl`: 生存时间 - 基于过期时间淘汰数据

### 错误处理

```yaml
error_handling:
  max_retries: 3                   # 最大重试次数
  base_delay: 1.0                  # 基础延迟（秒）
  max_delay: 60.0                  # 最大延迟（秒）
  circuit_breaker_threshold: 5     # 熔断器阈值
  circuit_breaker_timeout: 60      # 熔断器超时（秒）
```

**重试机制**：
- 使用指数退避算法：`delay = base_delay * (2 ** attempt)`
- 最大延迟限制：不会超过 `max_delay`
- 熔断器保护：连续失败 `threshold` 次后熔断

### 性能监控

```yaml
performance_monitoring:
  enabled: true                    # 启用性能监控
  collect_interval: 60             # 收集间隔（秒）
  log_performance: true            # 记录性能日志
  alert_thresholds:                # 告警阈值
    cpu: 80.0                      # CPU使用率(%)
    memory: 80.0                   # 内存使用率(%)
    response_time: 5.0             # 响应时间(秒)
```

### 图表配置

```yaml
# 图表设置
chartTimeframe: "1m"           # K线图时间周期
chartLookbackMinutes: 60        # 历史数据分钟数
chartTheme: "dark"              # 主题
chartIncludeMA: [7, 25]         # 移动平均线
chartImageWidth: 1600           # 图片宽度
chartImageHeight: 1200          # 图片高度
```

## 安全配置

### 数据加密

```yaml
security:
  enable_encryption: false       # 启用加密
  encryption_key: ""             # 加密密钥
  sanitize_logs: true            # 日志脱敏
```

### API限制

```yaml
api_limits:
  binance:
    requests_per_minute: 1200    # 币安限制
    requests_per_second: 10
  okx:
    requests_per_second: 20      # OKX限制
  bybit:
    requests_per_second: 100     # Bybit限制
```

## 数据库配置

```yaml
database:
  enabled: false                 # 启用数据库
  type: "sqlite"                 # 数据库类型
  connection_string: ""          # 连接字符串
  table_prefix: "pricesentry_"    # 表名前缀
```

## 开发者配置

```yaml
development:
  debug_mode: false              # 调试模式
  enable_profiler: false         # 性能分析
  mock_api: false               # 模拟API
  test_mode: false              # 测试模式
```

## 配置验证

系统启动时会自动验证配置文件，检查以下内容：

1. **必需字段**: 确保所有必需字段都已填写
2. **数据类型**: 验证字段值的数据类型
3. **范围检查**: 检查数值是否在合理范围内
4. **格式验证**: 验证URL、邮箱等格式
5. **依赖检查**: 检查字段间的依赖关系

### 常见配置错误

1. **Telegram配置错误**：
   - Token格式错误：应该是 `bot_token`
   - Chat ID格式错误：应该是数字或 `@channel_name`

2. **网络连接问题**：
   - API密钥错误
   - 网络连接超时
   - 交易所API限制

3. **文件路径问题**：
   - 交易对文件不存在
   - 日志目录无写入权限

## 性能优化建议

### 缓存优化

```yaml
# 高频率交易监控
cache:
  enabled: true
  max_size: 2000           # 增加缓存大小
  default_ttl: 120         # 缩短缓存时间
  strategy: "lru"          # 使用LRU策略
```

### 错误处理优化

```yaml
# 不稳定网络环境
error_handling:
  max_retries: 5           # 增加重试次数
  base_delay: 2.0         # 增加基础延迟
  max_delay: 120.0        # 增加最大延迟
```

### 监控优化

```yaml
# 生产环境监控
performance_monitoring:
  collect_interval: 30     # 更频繁的监控
  alert_thresholds:
    cpu: 70.0             # 降低告警阈值
    memory: 70.0
    response_time: 3.0
```

## 故障排除

### 配置验证失败

```bash
# 检查配置文件语法
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# 运行配置验证
python -c "from utils.config_validator import config_validator; print(config_validator.validate_config('config/config.yaml'))"
```

### 性能问题

```bash
# 查看性能统计
python -c "from utils.performance_monitor import performance_monitor; print(performance_monitor.get_stats())"

# 查看缓存统计
python -c "from utils.cache_manager import price_cache; print(price_cache.get_stats())"
```

### 缓存问题

```bash
# 清理缓存
python -c "from utils.cache_manager import price_cache; price_cache.clear()"

# 重置缓存策略
python -c "from utils.cache_manager import price_cache; price_cache.set_strategy('lru')"
```

## 最佳实践

1. **生产环境配置**：
   - 关闭调试模式
   - 启用缓存系统
   - 设置合理的错误重试参数
   - 启用性能监控

2. **开发环境配置**：
   - 启用调试模式
   - 使用模拟API
   - 降低性能监控频率
   - 启用详细日志

3. **安全配置**：
   - 使用环境变量存储敏感信息
   - 启用日志脱敏
   - 设置合理的API限制
   - 定期更新API密钥

## 配置示例

### 最小配置

```yaml
exchange: "okx"
defaultTimeframe: "5m"
defaultThreshold: 0.01
notificationChannels: ["telegram"]
telegram:
  token: "YOUR_TOKEN"
  chatId: "YOUR_CHAT_ID"
```

### 完整配置

```yaml
exchange: "okx"
exchanges: ["binance", "okx", "bybit"]
defaultTimeframe: "5m"
defaultThreshold: 0.01
symbolsFilePath: "config/symbols.txt"
notificationChannels: ["telegram", "dingding"]
telegram:
  token: "YOUR_TOKEN"
  chatId: "YOUR_CHAT_ID"
dingding:
  webhook: "YOUR_WEBHOOK"
  secret: "YOUR_SECRET"

# 高级配置
cache:
  enabled: true
  max_size: 1000
  default_ttl: 300
  strategy: "lru"

error_handling:
  max_retries: 3
  base_delay: 1.0
  max_delay: 60.0
  circuit_breaker_threshold: 5

performance_monitoring:
  enabled: true
  collect_interval: 60
  alert_thresholds:
    cpu: 80.0
    memory: 80.0
    response_time: 5.0
```

## 获取帮助

- **配置问题**: 查看错误日志 `logs/app.log`
- **性能问题**: 使用性能监控工具
- **API问题**: 检查交易所API文档
- **其他问题**: 提交GitHub Issue

更多详细信息请参考 [项目文档](../README.md)。