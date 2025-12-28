#!/bin/bash
# 快速启动测试脚本

echo "🚀 PriceSentry 快速启动测试"
echo ""

# 1. 清理旧配置
echo "📁 清理旧配置文件..."
rm -rf config/ 2>/dev/null
echo "✅ 旧配置已删除"
echo ""

# 2. 创建配置目录
echo "📂 创建配置目录..."
mkdir -p config
echo "✅ 配置目录已创建"
echo ""

# 3. 创建配置文件（使用 OKX，避免 Binance 地区限制）
echo "📝 创建配置文件..."
cat > config/config.yaml << 'EOF'
exchange: okx
defaultTimeframe: 5m
checkInterval: 1m
defaultThreshold: 1
notificationChannels:
  - telegram
notificationSymbols:
  - "BTC/USDT:USDT"
  - "ETH/USDT:USDT"
notificationTimezone: Asia/Shanghai
telegram:
  token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
  chatId: "123456789"
attachChart: true
chartTimeframe: 5m
chartLookbackMinutes: 500
chartTheme: dark
chartIncludeMA:
  - 7
  - 25
chartImageWidth: 1600
chartImageHeight: 1200
chartImageScale: 2
EOF
echo "✅ 配置文件已创建: config/config.yaml"
echo ""

# 4. 运行市场数据更新脚本
echo "📊 更新市场数据..."
PYTHONPATH=src uv run python tools/update_markets.py --exchanges okx
echo ""

# 5. 检查结果
echo "📋 检查结果..."
if [ -f "config/supported_markets.json" ]; then
    echo "✅ 市场数据文件已创建"
    echo ""
    echo "📂 数据目录结构:"
    ls -lh config/
    echo ""
    echo "📊 市场数据概览:"
    echo "   交易所:"
    python3 -c "import json; d=json.load(open('config/supported_markets.json')); [print(f'     - {k}: {len(v)} 个交易对') for k,v in d.items()]"
    echo ""
    echo "✅ 测试完成！"
    echo ""
    echo "💡 下一步:"
    echo "   1. 编辑配置文件: vi config/config.yaml"
    echo "   2. 设置真实的 Telegram Token 和 Chat ID"
    echo "   3. 运行 PriceSentry: PYTHONPATH=src uv run python -m app.cli"
else
    echo "❌ 市场数据文件未创建"
    echo ""
    echo "💡 可能的原因:"
    echo "   1. 网络问题"
    echo "   2. OKX API 暂时不可用"
    echo "   3. 需要配置代理"
    echo ""
    echo "📋 解决方案:"
    echo "   手动运行: PYTHONPATH=src uv run python tools/update_markets.py --exchanges okx"
    echo "   或使用其他交易所: bybit"
fi
