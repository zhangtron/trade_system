"""
聚宽平台专用的 TradeApi
简化版本，便于在聚宽策略中直接使用
"""
import requests
from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime


class TradeApi:
    """聚宽交易平台API客户端"""

    def __init__(self, base_url: str = "http://101.132.136.153:8899", timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """统一请求处理"""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(
                method,
                url,
                json=payload,
                timeout=self.timeout
            )
            if response.status_code >= 400:
                raise RuntimeError(f"请求失败: {method} {path} - {response.text}")
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"网络请求异常: {e}")

    def buy(self, strategy_id: int, symbol: str, quantity: Decimal, price: Decimal,
            trade_time: str, commission: Decimal = Decimal("0"), remark: str = "") -> Dict[str, Any]:
        """买入"""
        return self._request(
            "POST", "/api/trades",
            {
                "strategy_id": strategy_id,
                "symbol": symbol,
                "direction": "BUY",
                "quantity": float(quantity),
                "price": float(price),
                "commission": float(commission),
                "trade_time": trade_time,
                "remark": remark,
            }
        )

    def sell(self, strategy_id: int, symbol: str, quantity: Decimal, price: Decimal,
             trade_time: str, commission: Decimal = Decimal("0"), remark: str = "") -> Dict[str, Any]:
        """卖出"""
        return self._request(
            "POST", "/api/trades",
            {
                "strategy_id": strategy_id,
                "symbol": symbol,
                "direction": "SELL",
                "quantity": float(quantity),
                "price": float(price),
                "commission": float(commission),
                "trade_time": trade_time,
                "remark": remark,
            }
        )

    def get_positions(self, strategy_id: int) -> List[Dict[str, Any]]:
        """获取策略持仓"""
        return self._request("GET", f"/api/positions?strategy_id={strategy_id}")

    def get_qty(self, strategy_id: int, symbol: str) -> Decimal:
        """获取指定股票的持仓数量"""
        positions = self.get_positions(strategy_id)
        for pos in positions:
            if pos["symbol"] == symbol.upper():
                return Decimal(str(pos["quantity"]))
        return Decimal("0")


# ────────────────────────────────────────────────────────────
# 聚宽平台集成函数
# ────────────────────────────────────────────────────────────
def report_joinquant_order(context, order_obj, side: str, trade_api: TradeApi, strategy_id: int):
    """
    将聚宽订单上报到交易系统

    Args:
        context: 聚宽上下文对象
        order_obj: 聚宽订单对象 (order_target/order_value 返回的 Order 对象)
        side: 'buy' 或 'sell'
        trade_api: TradeApi 实例
        strategy_id: 策略ID

    Usage:
        # 在策略初始化中
        def init(context):
            g.trade_api = TradeApi()
            g.strategy_id = 1  # 设置你的策略ID

        # 在交易逻辑中
        order = order_target(security, 100)
        report_joinquant_order(context, order, 'buy', g.trade_api, g.strategy_id)
    """
    if order_obj is None:
        return

    # 获取订单成交信息
    filled_qty = Decimal(str(getattr(order_obj, 'filled', 0)))  # 已成交数量
    if filled_qty <= 0:
        return

    price = Decimal(str(getattr(order_obj, 'price', 0)))       # 成交价格
    commission = Decimal(str(getattr(order_obj, 'commission', 0)))  # 佣金
    symbol = getattr(order_obj, 'security', '')                # 股票代码
    trade_time = str(context.current_dt)                       # 交易时间

    try:
        if side == 'sell':
            trade_api.sell(
                strategy_id=strategy_id,
                symbol=symbol,
                quantity=filled_qty,
                price=price,
                trade_time=trade_time,
                commission=commission,
            )
        else:
            trade_api.buy(
                strategy_id=strategy_id,
                symbol=symbol,
                quantity=filled_qty,
                price=price,
                trade_time=trade_time,
                commission=commission,
            )
        print(f'[TradeApi] 上报成功: {side} {symbol} 数量={filled_qty} 价格={price}')
    except Exception as e:
        print(f'[TradeApi] 上报失败: {side} {symbol} - {e}')


# ────────────────────────────────────────────────────────────
# 使用示例
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 测试API连接
    api = TradeApi()

    # 测试买入
    try:
        result = api.buy(
            strategy_id=3,
            symbol="600696.XSHG",
            quantity=Decimal("100"),
            price=Decimal("1.03"),
            trade_time="2026-04-16 11:26:00",
            commission=Decimal("5.0")
        )
        print("买入成功:", result)
    except Exception as e:
        print("买入失败:", e)

    # 测试获取持仓
    try:
        positions = api.get_positions(strategy_id=1)
        print("当前持仓:", positions)
    except Exception as e:
        print("获取持仓失败:", e)