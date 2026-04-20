# TradeApi 聚宽平台集成指南

## 📁 文件说明

### 1. `trade_api.py`
精简的 TradeApi 客户端，适配新的交易系统API。

### 2. `joinquant_strategy_template.py`
聚宽策略完整模板，包含 TradeApi 集成。

## 🚀 快速开始

### 步骤1: 配置 TradeApi

```python
from trade_api import TradeApi

# 创建 API 客户端
api = TradeApi(
    base_url="http://101.132.136.153:8899",  # 你的API地址
    timeout=15
)
```

### 步骤2: 在聚宽策略中使用

```python
def init(context):
    # 初始化 TradeApi
    g.trade_api = TradeApi()
    g.strategy_id = 1  # 你的策略ID

def handle_bar(context, bar_dict):
    # 执行交易
    order = order_target('600519.XSHG', 100)

    # 上报交易
    from trade_api import report_joinquant_order
    report_joinquant_order(context, order, 'buy', g.trade_api, g.strategy_id)
```

## 📊 主要功能

### 1. 买入交易
```python
api.buy(
    strategy_id=1,
    symbol="600519.XSHG",
    quantity=Decimal("100"),
    price=Decimal("1800.50"),
    trade_time="2026-04-16 09:30:00",
    commission=Decimal("5.0")
)
```

### 2. 卖出交易
```python
api.sell(
    strategy_id=1,
    symbol="600519.XSHG",
    quantity=Decimal("100"),
    price=Decimal("1850.00"),
    trade_time="2026-04-16 14:30:00",
    commission=Decimal("5.0")
)
```

### 3. 查询持仓
```python
positions = api.get_positions(strategy_id=1)
for pos in positions:
    print(f"{pos['symbol']}: {pos['quantity']}")

# 获取特定股票数量
qty = api.get_qty(strategy_id=1, symbol="600519.XSHG")
```

## 🔧 API 变更说明

### 旧版 API (已弃用)
```python
# ❌ 旧版使用不同端点
api.buy(strategy_id, symbol, quantity, price, ...)
api.sell(strategy_id, symbol, quantity, price, ...)
```

### 新版 API (当前)
```python
# ✅ 新版使用统一端点
api._request("POST", "/api/trades", {
    "direction": "BUY",  # 或 "SELL"
    # ... 其他参数
})
```

## 📝 聚宽平台部署

### 完整配置步骤

1. **复制文件到聚宽**
   - 将 `trade_api.py` 的内容复制到聚宽策略编辑器
   - 或使用 `joinquant_strategy_template.py` 作为起点

2. **修改配置参数**
```python
def init(context):
    # 修改为你的配置
    g.trade_api = TradeApi(
        base_url="http://你的服务器地址:8899"
    )
    g.strategy_id = 1  # 你的策略ID
```

3. **启用网络权限**
   - 聚宽平台需要开启网络请求权限
   - 确保能够访问你的API服务器

4. **测试连接**
```python
# 测试API连接
def test_connection():
    api = TradeApi()
    positions = api.get_positions(strategy_id=1)
    print("连接成功，持仓:", positions)
```

## ⚠️ 注意事项

### 1. 网络稳定性
- 确保聚宽平台能稳定访问你的API服务器
- 考虑添加重试机制处理网络异常

### 2. 异常处理
```python
try:
    api.buy(...)
except Exception as e:
    log.error(f"交易上报失败: {e}")
    # 继续执行策略逻辑
```

### 3. 数据一致性
- 确保策略ID正确
- 检查股票代码格式（聚宽使用 "600519.XSHG" 格式）

### 4. 性能考虑
- 避免频繁查询持仓
- 可以考虑缓存持仓数据

## 🔄 迁移指南

### 从旧版迁移到新版

**旧代码:**
```python
# 旧版 API
api.buy(strategy_id, symbol, quantity, price, trade_time, commission)
api.sell(strategy_id, symbol, quantity, price, trade_time, commission)
```

**新代码:**
```python
# 新版 API (接口相同，内部实现适配)
api.buy(strategy_id, symbol, quantity, price, trade_time, commission)
api.sell(strategy_id, symbol, quantity, price, trade_time, commission)
```

好消息：**接口保持不变**，只需替换 `trade_api.py` 文件即可！

## 📞 技术支持

如有问题，请检查：
1. API服务器是否正常运行
2. 网络连接是否稳定
3. 策略ID是否正确
4. 股票代码格式是否正确

## 🎯 最佳实践

1. **错误处理**: 始终包含异常处理，避免策略因API错误中断
2. **日志记录**: 记录所有交易上报，便于调试
3. **连接测试**: 在策略开始时测试API连接
4. **数据验证**: 验证API返回的数据格式
5. **性能优化**: 批量处理交易，避免频繁API调用