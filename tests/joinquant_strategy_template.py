"""
聚宽策略模板 - 集成 TradeApi
将策略交易数据实时上报到交易系统
"""

# 导入 TradeApi (需要将 trade_api.py 文件内容复制到聚宽平台)
# 注意：聚宽平台需要将 Python 代码放在策略编辑器中

# ────────────────────────────────────────────────────────────
# 1. 策略初始化
# ────────────────────────────────────────────────────────────
def init(context):
    """策略初始化"""
    # 设置基准
    set_benchmark('000300.XSHG')

    # 开启真实价格模拟
    set_option('use_real_price', True)

    # 设置交易手续费
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, close_today_commission=0, min_commission=5), type='stock')

    # 设置股票池
    context.stock_pool = ['600519.XSHG', '000858.XSHG', '600036.XSHG']  # 贵州茅台、五粮液、招商银行

    # 设置交易参数
    context.target_percent = 0.3  # 目标仓位
    context.hold_days = 20        # 持有天数

    # 初始化 TradeApi
    # 注意：需要在聚宽平台中配置好网络请求权限
    # 请将下面的 URL 替换为你的交易系统实际地址
    context.trade_api_base_url = "http://YOUR_SERVER_IP:8899"  # 例如：http://localhost:8899 或 http://your-server-ip:8899
    context.strategy_id = 1  # 修改为你的策略ID

    # 记录股票买入时间
    context.buy_days = {}

# ────────────────────────────────────────────────────────────
# 2. TradeApi 集成函数
# ────────────────────────────────────────────────────────────
def trade_api_request(method, path, payload=None, base_url=None, timeout=15):
    """发送交易API请求"""
    import requests
    from datetime import datetime

    if base_url is None:
        return None

    try:
        url = f"{base_url.rstrip('/')}{path}"
        response = requests.request(
            method,
            url,
            json=payload,
            timeout=timeout
        )

        if response.status_code >= 400:
            log.error(f"TradeApi请求失败: {method} {path} - {response.text}")
            return None

        return response.json()
    except Exception as e:
        log.error(f"TradeApi请求异常: {e}")
        return None

def report_trade_to_api(context, order_obj, side):
    """上报交易到API"""
    if order_obj is None or not hasattr(order_obj, 'filled') or order_obj.filled <= 0:
        return

    try:
        import requests
        from decimal import Decimal

        filled_qty = Decimal(str(order_obj.filled))
        price = Decimal(str(order_obj.price))
        commission = Decimal(str(order_obj.commission))
        symbol = order_obj.security
        trade_time = str(context.current_dt)

        payload = {
            "strategy_id": context.strategy_id,
            "symbol": symbol,
            "direction": "BUY" if side == 'buy' else "SELL",
            "quantity": float(filled_qty),
            "price": float(price),
            "commission": float(commission),
            "trade_time": trade_time,
            "remark": f"聚宽策略-{side}"
        }

        result = trade_api_request(
            "POST",
            "/api/trades",
            payload,
            context.trade_api_base_url
        )

        if result:
            log.info(f"✅ 交易上报成功: {side} {symbol} 数量={filled_qty} 价格={price}")
        else:
            log.warn(f"⚠️ 交易上报失败: {side} {symbol}")

    except Exception as e:
        log.error(f"❌ 交易上报异常: {side} - {e}")

# ────────────────────────────────────────────────────────────
# 3. 定时任务
# ────────────────────────────────────────────────────────────
def before_trading_start(context):
    """盘前运行"""
    log.info(f"=== {context.current_dt} 盘前准备 ===")

def after_trading_end(context):
    """盘后运行"""
    log.info(f"=== {context.current_dt} 盘后结算 ===")

    # 记录当日账户信息
    account = context.portfolio
    log.info(f"总资产: {account.total_value}")
    log.info(f"持仓市值: {account.positions_value}")
    log.info(f"可用资金: {account.available_cash}")

    # 上报持仓信息（可选）
    # 如果需要，可以调用持仓更新API

# ────────────────────────────────────────────────────────────
# 4. 交易逻辑
# ────────────────────────────────────────────────────────────
def handle_bar(context, bar_dict):
    """定时交易逻辑"""
    log.info(f"=== {context.current_dt} 交易信号 ===")

    # 获取当前账户信息
    account = context.portfolio
    current_value = account.total_value
    available_cash = account.available_cash

    # 遍历股票池
    for stock in context.stock_pool:
        current_price = history(stock, ['close'], 1, '1d', False)['close'].iloc[-1]
        ma_short = history(stock, ['close'], 5, '1d', False)['close'].mean()
        ma_long = history(stock, ['close'], 20, '1d', False)['close'].mean()

        # 买入信号：短期均线上穿长期均线
        if ma_short > ma_long and stock not in list(account.positions.keys()):
            # 计算买入金额
            target_value = current_value * context.target_percent

            if available_cash >= target_value:
                # 执行买入
                order_obj = order_value(stock, target_value)

                # 上报交易
                report_trade_to_api(context, order_obj, 'buy')

                # 记录买入时间
                context.buy_days[stock] = context.current_dt.date()
                log.info(f"📈 买入信号: {stock} 目标金额={target_value}")

        # 卖出信号：持有超过指定天数 或 短期均线下穿长期均线
        elif stock in account.positions:
            buy_date = context.buy_days.get(stock)
            hold_days = (context.current_dt.date() - buy_date).days if buy_date else 0

            position = account.positions[stock]

            # 卖出条件
            if hold_days >= context.hold_days or ma_short < ma_long:
                # 执行卖出
                order_obj = order_target(stock, 0)

                # 上报交易
                report_trade_to_api(context, order_obj, 'sell')

                # 清除买入时间记录
                if stock in context.buy_days:
                    del context.buy_days[stock]

                log.info(f"📉 卖出信号: {stock} 持有天数={hold_days}")

    # 显示当前持仓
    log.info(f"📊 当前持仓: {list(account.positions.keys())}")

# ────────────────────────────────────────────────────────────
# 5. 风险控制
# ────────────────────────────────────────────────────────────
def after_trading_end(context):
    """风险控制"""
    account = context.portfolio

    # 检查单个持仓占比
    for stock, position in account.positions.items():
        position_ratio = position.value / account.total_value
        if position_ratio > 0.4:  # 单只股票超过40%仓位
            log.warn(f"⚠️ 风险提示: {stock} 占比过高 {position_ratio:.2%}")

    # 检查总仓位
    position_ratio = account.positions_value / account.total_value
    if position_ratio > 0.95:  # 仓位超过95%
        log.warn(f"⚠️ 风险提示: 总仓位过高 {position_ratio:.2%}")

# ────────────────────────────────────────────────────────────
# 使用说明
# ────────────────────────────────────────────────────────────
"""
聚宽平台使用步骤：

1. 复制本文件内容到聚宽策略编辑器

2. 修改配置参数：
   - context.strategy_id = 1  # 改为你的策略ID
   - context.trade_api_base_url = "http://你的服务器地址:端口"
   - context.stock_pool = [...]  # 设置你的股票池

3. 设置网络权限：
   - 聚宽平台需要开启网络请求权限
   - 确保能够访问你的交易API服务器

4. 回测或模拟交易：
   - 点击"运行回测"查看历史表现
   - 开启"模拟交易"进行实时交易

5. 查看交易数据：
   - 所有交易都会实时上报到你的交易系统
   - 可以在交易系统界面查看持仓、收益等数据

注意事项：
- 确保网络连接稳定
- 注意处理网络请求异常
- 定期检查交易上报是否成功
"""