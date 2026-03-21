from __future__ import annotations

import os
import random
import sys
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / ".vendor"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from fastapi.testclient import TestClient

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "mysql+pymysql://root:7842zc@localhost:3306/trade_system_db?charset=utf8mb4"

from app.main import app

random.seed(20260318)

SYMBOLS = ["IF8888", "IC8888", "IH8888", "RB9999", "AU9999", "CU9999", "AG9999", "ZN9999"]
STRATEGY_TYPES = ["趋势跟踪", "均值回归", "套利", "多因子"]


def now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def choose_price(base: float) -> float:
    return round(max(base * (1 + random.uniform(-0.04, 0.04)), 5), 2)


def main() -> None:
    created_strategies = []
    trade_counts: dict[int, int] = defaultdict(int)
    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        assert client.get("/trade-tester").status_code == 200

        for index in range(1, 7):
            start_days_ago = random.randint(45, 120)
            start_time = now_naive() - timedelta(days=start_days_ago)
            initial_capital = random.choice([80000, 100000, 120000, 150000])
            benchmark_annual_return = random.choice([0.03, 0.05, 0.08])
            strategy_name = f"演示策略-{datetime.now().strftime('%Y%m%d')}-{index:02d}"
            create_resp = client.post(
                "/api/strategies",
                json={
                    "name": strategy_name,
                    "description": "自动生成的演示策略，用于界面和接口联调。",
                    "type": random.choice(STRATEGY_TYPES),
                    "status": "draft",
                    "parameters": {
                        "initial_capital": initial_capital,
                        "benchmark_annual_return": benchmark_annual_return,
                        "ma_short": random.choice([5, 8, 10]),
                        "ma_long": random.choice([20, 30, 60]),
                        "stop_loss": round(random.uniform(0.03, 0.1), 3),
                    },
                },
            )
            assert create_resp.status_code == 200, create_resp.text
            strategy = create_resp.json()
            strategy_id = strategy["strategy_id"]

            update_resp = client.put(
                f"/api/strategies/{strategy_id}",
                json={"description": strategy["description"] + " 已自动补充说明。"},
            )
            assert update_resp.status_code == 200, update_resp.text

            status_resp = client.put(
                f"/api/strategies/{strategy_id}/status",
                json={"status": "active"},
            )
            assert status_resp.status_code == 200, status_resp.text
            created_strategies.append(strategy_id)

            symbols = random.sample(SYMBOLS, k=3)
            price_map = {symbol: random.uniform(50, 800) for symbol in symbols}
            positions = defaultdict(float)
            trade_time = start_time

            for _ in range(random.randint(16, 28)):
                trade_time += timedelta(days=random.randint(1, 4))
                symbol = random.choice(symbols)
                price_map[symbol] = choose_price(price_map[symbol])
                quantity = round(random.uniform(1, 10), 2)
                commission = round(random.uniform(0, 3), 2)

                do_sell = positions[symbol] > 0 and random.random() < 0.45
                if do_sell:
                    quantity = round(min(quantity, positions[symbol]), 2)
                    if quantity <= 0:
                        quantity = round(min(positions[symbol], 1), 2)
                    resp = client.post(
                        "/api/trades/sell",
                        json={
                            "strategy_id": strategy_id,
                            "symbol": symbol,
                            "quantity": quantity,
                            "price": price_map[symbol],
                            "commission": commission,
                            "trade_time": trade_time.isoformat(),
                            "remark": "自动生成卖出单",
                        },
                    )
                    assert resp.status_code == 200, resp.text
                    positions[symbol] = round(positions[symbol] - quantity, 6)
                else:
                    resp = client.post(
                        "/api/trades/buy",
                        json={
                            "strategy_id": strategy_id,
                            "symbol": symbol,
                            "quantity": quantity,
                            "price": price_map[symbol],
                            "commission": commission,
                            "trade_time": trade_time.isoformat(),
                            "remark": "自动生成买入单",
                        },
                    )
                    assert resp.status_code == 200, resp.text
                    positions[symbol] = round(positions[symbol] + quantity, 6)

                trade_counts[strategy_id] += 1

            price_updates = [
                {"strategy_id": strategy_id, "symbol": symbol, "current_price": choose_price(price_map[symbol])}
                for symbol, qty in positions.items()
                if qty > 0
            ]
            if price_updates:
                update_price_resp = client.put("/api/positions/update-prices", json={"items": price_updates})
                assert update_price_resp.status_code == 200, update_price_resp.text
                position_id = update_price_resp.json()[0]["position_id"]
                assert client.get(f"/api/positions/{position_id}").status_code == 200

            detail_resp = client.get(f"/api/strategies/{strategy_id}")
            assert detail_resp.status_code == 200, detail_resp.text
            detail = detail_resp.json()
            assert abs(detail["annualized_return_pct"]) < 1000, detail

            dashboard_resp = client.get(f"/api/strategies/{strategy_id}/dashboard")
            assert dashboard_resp.status_code == 200, dashboard_resp.text
            dashboard = dashboard_resp.json()
            assert len(dashboard["equity_curve"]) >= 10, dashboard
            assert dashboard["strategy"]["cumulative_return_pct"] is not None

            trades_resp = client.get(f"/api/trades?strategy_id={strategy_id}&page=1&page_size=5")
            assert trades_resp.status_code == 200, trades_resp.text
            first_trade = trades_resp.json()["items"][0]
            assert client.get(f"/api/trades/{first_trade['trade_id']}").status_code == 200
            assert client.get(f"/api/trades/stats?strategy_id={strategy_id}").status_code == 200
            assert client.get(f"/api/positions?strategy_id={strategy_id}").status_code == 200
            assert client.get(f"/api/positions/overview?strategy_id={strategy_id}").status_code == 200

            eval_resp = client.post(
                "/api/evaluations",
                json={
                    "strategy_id": strategy_id,
                    "start_date": start_time.date().isoformat(),
                    "end_date": now_naive().date().isoformat(),
                    "initial_capital": initial_capital,
                    "risk_free_rate": 0.02,
                    "benchmark_annual_return": benchmark_annual_return,
                },
            )
            assert eval_resp.status_code == 200, eval_resp.text
            eval_id = eval_resp.json()["eval_id"]
            metrics_resp = client.get(f"/api/evaluations/{eval_id}/metrics")
            curve_resp = client.get(f"/api/evaluations/{eval_id}/equity-curve")
            assert metrics_resp.status_code == 200, metrics_resp.text
            assert curve_resp.status_code == 200, curve_resp.text
            metrics = metrics_resp.json()
            assert "benchmark_return_pct" in metrics
            assert "max_drawdown_period" in metrics

        strategies_resp = client.get("/api/strategies?page=1&page_size=100")
        assert strategies_resp.status_code == 200
        print(f"created_demo_strategies={len(created_strategies)}")
        for strategy_id in created_strategies:
            print(f"strategy_id={strategy_id} trades={trade_counts[strategy_id]}")


if __name__ == "__main__":
    main()
