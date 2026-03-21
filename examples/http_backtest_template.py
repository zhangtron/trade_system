from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

import requests
from tqdm import tqdm
from xtquant import xtdata


ZERO = Decimal("0")


@dataclass
class Bar:
    trade_time: str
    trade_date: str
    close: Decimal


def get_history_data(stock_list, start_date, end_date, download=True):
    if download:
        print("Downloading history...")
        for symbol in tqdm(stock_list):
            xtdata.download_history_data(symbol, "1d", start_date, end_date)

    print("Loading market data...")
    return xtdata.get_market_data_ex(
        field_list=["close", "high", "low", "open", "volume", "amount"],
        stock_list=stock_list,
        period="1d",
        start_time=start_date,
        end_time=end_date,
        fill_data=True,
    )


def parse_index(value: Any) -> datetime:
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()
    text = str(value)
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt)
        except ValueError:
            pass
    raise ValueError(f"Unsupported date index: {value}")


def load_bars(symbol: str, start_date: str, end_date: str, download: bool = True) -> list[Bar]:
    data = get_history_data([symbol], start_date, end_date, download=download)
    frame = data.get(symbol)
    if frame is None or getattr(frame, "empty", True):
        raise ValueError(f"No K-line data returned for {symbol}")

    bars = []
    for index, row in frame.iterrows():
        dt = parse_index(index).replace(hour=15, minute=0, second=0, microsecond=0)
        bars.append(Bar(trade_time=dt.isoformat(), trade_date=dt.strftime("%Y-%m-%d"), close=Decimal(str(row["close"]))))
    return bars


class TradeApi:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: int = 15, session=None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None):
        response = self.session.request(method, f"{self.base_url}{path}", json=payload, timeout=self.timeout)
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {path} failed: {response.text}")
        return response.json()

    def buy(self, strategy_id: int, symbol: str, quantity: Decimal, price: Decimal, trade_time: str, commission: Decimal = ZERO, remark: str = ""):
        return self._request(
            "POST",
            "/api/trades/buy",
            {
                "strategy_id": strategy_id,
                "symbol": symbol,
                "quantity": float(quantity),
                "price": float(price),
                "commission": float(commission),
                "trade_time": trade_time,
                "remark": remark,
            },
        )

    def sell(self, strategy_id: int, symbol: str, quantity: Decimal, price: Decimal, trade_time: str, commission: Decimal = ZERO, remark: str = ""):
        return self._request(
            "POST",
            "/api/trades/sell",
            {
                "strategy_id": strategy_id,
                "symbol": symbol,
                "quantity": float(quantity),
                "price": float(price),
                "commission": float(commission),
                "trade_time": trade_time,
                "remark": remark,
            },
        )

    def get_positions(self, strategy_id: int):
        return self._request("GET", f"/api/positions?strategy_id={strategy_id}")

    def get_qty(self, strategy_id: int, symbol: str) -> Decimal:
        for position in self.get_positions(strategy_id):
            if position["symbol"] == symbol.upper():
                return Decimal(str(position["quantity"]))
        return ZERO


class SimpleMaStrategy:
    def __init__(
        self,
        api: TradeApi,
        strategy_id: int,
        symbol: str,
        initial_cash: Decimal = Decimal("100000"),
        lot_size: Decimal = Decimal("100"),
        ma_window: int = 5,
        commission_rate: Decimal = Decimal("0.0003"),
        close_last: bool = True,
    ):
        self.api = api
        self.strategy_id = strategy_id
        self.symbol = symbol.upper()
        self.initial_cash = Decimal(str(initial_cash))
        self.lot_size = Decimal(str(lot_size))
        self.ma_window = ma_window
        self.commission_rate = Decimal(str(commission_rate))
        self.close_last = close_last

    def fee(self, quantity: Decimal, price: Decimal) -> Decimal:
        return (quantity * price * self.commission_rate).quantize(Decimal("0.0001"))

    def run(self, bars: list[Bar]):
        cash = self.initial_cash
        closes: list[Decimal] = []
        orders = []

        for bar in bars:
            closes.append(bar.close)
            qty = self.api.get_qty(self.strategy_id, self.symbol)
            action = "HOLD"

            if len(closes) >= self.ma_window:
                ma = sum(closes[-self.ma_window :], start=ZERO) / Decimal(self.ma_window)
                if qty <= ZERO and bar.close > ma:
                    fee = self.fee(self.lot_size, bar.close)
                    self.api.buy(self.strategy_id, self.symbol, self.lot_size, bar.close, bar.trade_time, fee, "ma_buy")
                    cash -= self.lot_size * bar.close + fee
                    orders.append((bar.trade_date, "BUY", self.lot_size, bar.close))
                    action = f"BUY {self.lot_size}"
                elif qty > ZERO and bar.close < ma:
                    fee = self.fee(qty, bar.close)
                    self.api.sell(self.strategy_id, self.symbol, qty, bar.close, bar.trade_time, fee, "ma_sell")
                    cash += qty * bar.close - fee
                    orders.append((bar.trade_date, "SELL", qty, bar.close))
                    action = f"SELL {qty}"
                else:
                    action = f"HOLD qty={qty}"
            print(f"[{bar.trade_date}] close={bar.close:.2f} action={action}")

        last_price = bars[-1].close
        final_qty = self.api.get_qty(self.strategy_id, self.symbol)
        if self.close_last and final_qty > ZERO:
            fee = self.fee(final_qty, last_price)
            self.api.sell(self.strategy_id, self.symbol, final_qty, last_price, bars[-1].trade_time, fee, "close_last")
            cash += final_qty * last_price - fee
            orders.append((bars[-1].trade_date, "SELL", final_qty, last_price))
            final_qty = ZERO

        market_value = final_qty * last_price
        total_asset = cash + market_value
        return_pct = ((total_asset - self.initial_cash) / self.initial_cash * Decimal("100")).quantize(Decimal("0.01"))
        positions = self.api.get_positions(self.strategy_id)

        print("\nSummary")
        print(f"cash={cash:.2f}")
        print(f"market_value={market_value:.2f}")
        print(f"total_asset={total_asset:.2f}")
        print(f"return_pct={return_pct}%")
        print(f"server_positions={positions}")

        return {
            "orders": orders,
            "cash": cash,
            "market_value": market_value,
            "total_asset": total_asset,
            "return_pct": return_pct,
            "positions": positions,
        }


def parse_args():
    parser = argparse.ArgumentParser(description="Minimal HTTP strategy template")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--strategy-id", type=int, required=True, help="Existing strategy_id")
    parser.add_argument("--symbol", default="300308.SZ")
    parser.add_argument("--start-date", default="20250101")
    parser.add_argument("--end-date", default="20251230")
    parser.add_argument("--ma-window", type=int, default=5)
    parser.add_argument("--lot-size", type=Decimal, default=Decimal("100"))
    parser.add_argument("--initial-cash", type=Decimal, default=Decimal("100000"))
    parser.add_argument("--commission-rate", type=Decimal, default=Decimal("0.0003"))
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--keep-position", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    bars = load_bars(args.symbol, args.start_date, args.end_date, download=not args.skip_download)
    api = TradeApi(args.base_url)
    strategy = SimpleMaStrategy(
        api=api,
        strategy_id=args.strategy_id,
        symbol=args.symbol,
        initial_cash=args.initial_cash,
        lot_size=args.lot_size,
        ma_window=args.ma_window,
        commission_rate=args.commission_rate,
        close_last=not args.keep_position,
    )
    strategy.run(bars)


if __name__ == "__main__":
    main()
