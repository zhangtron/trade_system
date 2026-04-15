from __future__ import annotations

import argparse
import random
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import requests
from requests import RequestException

try:
    from fastapi.testclient import TestClient
    from app.main import app

    HAS_INPROCESS = True
except Exception:
    HAS_INPROCESS = False


def now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def assert_ok(response, step: str) -> dict:
    if response.status_code != 200:
        raise AssertionError(f"{step} failed: {response.status_code} {response.text}")
    return response.json() if response.headers.get("content-type", "").startswith("application/json") else {}


class HttpApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def get(self, path: str):
        return self.session.get(f"{self.base_url}{path}", timeout=30)

    def post(self, path: str, json: dict):
        return self.session.post(f"{self.base_url}{path}", json=json, timeout=30)

    def put(self, path: str, json: dict):
        return self.session.put(f"{self.base_url}{path}", json=json, timeout=30)

    def close(self) -> None:
        self.session.close()


@contextmanager
def build_client(mode: str, base_url: str):
    if mode in {"auto", "inprocess"} and HAS_INPROCESS:
        with TestClient(app) as client:
            yield client
        return

    if mode == "inprocess" and not HAS_INPROCESS:
        raise RuntimeError("inprocess mode unavailable: fastapi not installed")

    client = HttpApiClient(base_url)
    try:
        yield client
    finally:
        client.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Long volatile full-flow smoke test")
    parser.add_argument("--mode", choices=["auto", "inprocess", "http"], default="auto")
    parser.add_argument("--base-url", default="http://127.0.0.1:8899")
    parser.add_argument("--symbol", default="RB9999")
    parser.add_argument("--days", type=int, default=180, help="回放天数，默认 180 天")
    parser.add_argument("--volatility", type=float, default=0.06, help="日波动标准差，默认 6%")
    parser.add_argument("--seed", type=int, default=20260415, help="随机种子，便于复现")
    parser.add_argument("--min-trades", type=int, default=40, help="最少成交笔数校验")
    parser.add_argument("--keep-open", action="store_true", help="结束时不强平")
    return parser.parse_args()


def generate_price(prev: float, rng: random.Random, volatility: float) -> float:
    daily_ret = rng.gauss(0, volatility)
    return round(max(5.0, prev * (1.0 + daily_ret)), 2)


def trade_time_for_day(base: datetime, day: int, minute_jitter: int = 0) -> str:
    dt = (base + timedelta(days=day)).replace(hour=15, minute=minute_jitter, second=0, microsecond=0)
    return dt.isoformat()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    started_at = now_naive()
    begin = started_at - timedelta(days=args.days)
    strategy_name = f"volatile-flow-{started_at.strftime('%Y%m%d-%H%M%S')}"

    with build_client(args.mode, args.base_url) as client:
        try:
            assert_ok(client.get("/health"), "health check")
        except RequestException as exc:
            raise RuntimeError(
                "无法连接测试服务。请先执行 `python run.py` 启动服务，"
                "或安装依赖后执行 `python full_flow_test.py --mode inprocess`。"
            ) from exc

        strategy = assert_ok(
            client.post(
                "/api/strategies",
                json={
                    "name": strategy_name,
                    "description": "长周期高波动回放，用于调试评估指标和收益曲线",
                    "type": "volatile_full_flow",
                    "status": "active",
                    "parameters": {"initial_capital": 100000, "benchmark_annual_return": 0.03},
                },
            ),
            "create strategy",
        )
        strategy_id = strategy["strategy_id"]

        price = 100.0
        qty = 0
        buy_count = 0
        sell_count = 0
        price_min = price
        price_max = price

        # 第一天强制开仓，确保收益曲线从长周期开始
        first_qty = 20
        assert_ok(
            client.post(
                "/api/trades",
                json={
                    "strategy_id": strategy_id,
                    "symbol": args.symbol,
                    "direction": "BUY",
                    "quantity": first_qty,
                    "price": price,
                    "commission": round(first_qty * price * 0.0005, 4),
                    "trade_time": trade_time_for_day(begin, 0),
                    "remark": "seed_buy_day0",
                },
            ),
            "seed buy day0",
        )
        qty += first_qty
        buy_count += 1

        for day in range(1, args.days):
            price = generate_price(price, rng, args.volatility)
            price_min = min(price_min, price)
            price_max = max(price_max, price)

            # 定期刷新持仓现价，增强净值曲线波动
            if qty > 0 and day % 3 == 0:
                assert_ok(
                    client.put(
                        "/api/positions/update-prices",
                        json={"items": [{"strategy_id": strategy_id, "symbol": args.symbol, "current_price": price}]},
                    ),
                    f"update price day{day}",
                )

            # 动态交易：波动大时更倾向减仓，趋势上行时允许加仓
            action_roll = rng.random()
            if qty == 0:
                buy_qty = rng.randint(5, 30)
                assert_ok(
                    client.post(
                        "/api/trades",
                        json={
                            "strategy_id": strategy_id,
                            "symbol": args.symbol,
                            "direction": "BUY",
                            "quantity": buy_qty,
                            "price": price,
                            "commission": round(buy_qty * price * 0.0005, 4),
                            "trade_time": trade_time_for_day(begin, day, minute_jitter=1),
                            "remark": f"reopen_day{day}",
                        },
                    ),
                    f"buy day{day}",
                )
                qty += buy_qty
                buy_count += 1
                continue

            if action_roll < 0.45:
                sell_qty = min(qty, rng.randint(3, 25))
                assert_ok(
                    client.post(
                        "/api/trades",
                        json={
                            "strategy_id": strategy_id,
                            "symbol": args.symbol,
                            "direction": "SELL",
                            "quantity": sell_qty,
                            "price": price,
                            "commission": round(sell_qty * price * 0.0005, 4),
                            "trade_time": trade_time_for_day(begin, day, minute_jitter=2),
                            "remark": f"reduce_day{day}",
                        },
                    ),
                    f"sell day{day}",
                )
                qty -= sell_qty
                sell_count += 1
            elif action_roll < 0.78:
                buy_qty = rng.randint(2, 20)
                assert_ok(
                    client.post(
                        "/api/trades",
                        json={
                            "strategy_id": strategy_id,
                            "symbol": args.symbol,
                            "direction": "BUY",
                            "quantity": buy_qty,
                            "price": price,
                            "commission": round(buy_qty * price * 0.0005, 4),
                            "trade_time": trade_time_for_day(begin, day, minute_jitter=3),
                            "remark": f"add_day{day}",
                        },
                    ),
                    f"buy add day{day}",
                )
                qty += buy_qty
                buy_count += 1

        if qty > 0 and not args.keep_open:
            assert_ok(
                client.post(
                    "/api/trades",
                    json={
                        "strategy_id": strategy_id,
                        "symbol": args.symbol,
                        "direction": "SELL",
                        "quantity": qty,
                        "price": price,
                        "commission": round(qty * price * 0.0005, 4),
                        "trade_time": started_at.replace(hour=15, minute=59, second=0, microsecond=0).isoformat(),
                        "remark": "final_close",
                    },
                ),
                "final close",
            )
            sell_count += 1
            qty = 0

        stats = assert_ok(client.get(f"/api/trades/stats?strategy_id={strategy_id}"), "query trade stats")
        total_trades = stats["total_trades"]
        if total_trades < args.min_trades:
            raise AssertionError(f"expected total_trades >= {args.min_trades}, got {total_trades}")

        dashboard = assert_ok(client.get(f"/api/strategies/{strategy_id}/dashboard"), "query strategy dashboard")
        curve_len = len(dashboard["equity_curve"])
        if curve_len < max(60, int(args.days * 0.6)):
            raise AssertionError(f"equity_curve too short: {curve_len}")
        if not dashboard["evaluation_metrics"]:
            raise AssertionError("evaluation_metrics should not be empty")

        # 核心指标存在性校验（用于调试评估与曲线）
        for key in [
            "strategy_return_pct",
            "strategy_annualized_return_pct",
            "sharpe_ratio",
            "sortino_ratio",
            "information_ratio",
            "max_drawdown_period",
        ]:
            if key not in dashboard["evaluation_metrics"]:
                raise AssertionError(f"missing metric key: {key}")

        history = assert_ok(client.get(f"/api/positions/history?strategy_id={strategy_id}"), "query closed history")
        if not args.keep_open and len(history) < 1:
            raise AssertionError("expected closed position history after final close")

        csv_resp = client.get(f"/api/trades?strategy_id={strategy_id}&export=csv")
        if csv_resp.status_code != 200:
            raise AssertionError(f"csv export failed: {csv_resp.status_code} {csv_resp.text}")
        if "trade_id" not in csv_resp.text or "exec_status" not in csv_resp.text:
            raise AssertionError("csv export missing expected headers")

        print("PASS volatile full flow test")
        print(f"strategy_id={strategy_id}")
        print(f"days={args.days}")
        print(f"total_trades={total_trades} (buy={buy_count}, sell={sell_count})")
        print(f"price_range=[{price_min}, {price_max}]")
        print(f"equity_curve_points={curve_len}")
        print(f"closed_positions={len(history)}")
        print(f"final_open_qty={qty}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL volatile full flow test: {exc}")
        raise
