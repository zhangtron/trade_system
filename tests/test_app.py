from __future__ import annotations

from datetime import UTC, datetime, timedelta


def now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def create_strategy(client, name="??A", status="active", parameters=None):
    response = client.post(
        "/api/strategies",
        json={
            "name": name,
            "description": "????",
            "type": "????",
            "parameters": parameters or {"ma_short": 5, "ma_long": 20, "initial_capital": 100000, "benchmark_annual_return": 0.03},
            "status": status,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_strategy_crud_and_status(client):
    strategy = create_strategy(client, status="draft")
    detail = client.get(f"/api/strategies/{strategy['strategy_id']}")
    assert detail.status_code == 200
    assert detail.json()["name"] == "??A"

    update = client.put(
        f"/api/strategies/{strategy['strategy_id']}",
        json={"description": "???", "parameters": {"window": 10, "initial_capital": 120000}},
    )
    assert update.status_code == 200
    assert update.json()["version"] == 2

    status_update = client.put(
        f"/api/strategies/{strategy['strategy_id']}/status",
        json={"status": "active"},
    )
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "active"


def test_strategy_list_filters_and_archive_panel(client):
    active = create_strategy(client, name="active-one", status="active")
    archived = create_strategy(client, name="archived-one", status="archived")

    visible = client.get("/api/strategies?page=1&page_size=20&exclude_status=archived")
    assert visible.status_code == 200
    assert all(item["status"] != "archived" for item in visible.json()["items"])
    assert any(item["strategy_id"] == active["strategy_id"] for item in visible.json()["items"])

    archived_only = client.get("/api/strategies?page=1&page_size=20&status=archived")
    assert archived_only.status_code == 200
    assert archived_only.json()["total"] >= 1
    assert all(item["status"] == "archived" for item in archived_only.json()["items"])
    assert any(item["strategy_id"] == archived["strategy_id"] for item in archived_only.json()["items"])

    home_page = client.get("/")
    assert home_page.status_code == 200
    assert "archivePanel" in home_page.text
    assert "archivedStrategyTableBody" in home_page.text
    assert "archiveToggle" in home_page.text


def test_trade_position_stats_and_strategy_metrics(client):
    now = now_naive()
    strategy = create_strategy(client)
    strategy_b = create_strategy(client, name="??B")

    buy = client.post(
        "/api/trades",
        json={
            "strategy_id": strategy["strategy_id"],
            "symbol": "IF8888",
            "direction": "BUY",
            "quantity": 10,
            "price": 100,
            "commission": 1.5,
            "trade_time": (now - timedelta(days=14)).isoformat(),
        },
    )
    assert buy.status_code == 200

    buy2 = client.post(
        "/api/trades",
        json={
            "strategy_id": strategy["strategy_id"],
            "symbol": "IF8888",
            "direction": "BUY",
            "quantity": 5,
            "price": 120,
            "commission": 1,
            "trade_time": (now - timedelta(days=1)).isoformat(),
        },
    )
    assert buy2.status_code == 200

    client.post(
        "/api/trades",
        json={
            "strategy_id": strategy_b["strategy_id"],
            "symbol": "AG8888",
            "direction": "BUY",
            "quantity": 2,
            "price": 50,
            "commission": 0.5,
            "trade_time": now.isoformat(),
        },
    )

    positions = client.get(f"/api/positions?strategy_id={strategy['strategy_id']}")
    assert positions.status_code == 200
    assert len(positions.json()) == 1
    assert float(positions.json()[0]["quantity"]) == 15.0
    original_avg_cost = float(positions.json()[0]["avg_cost"])

    update_prices = client.put(
        "/api/positions/update-prices",
        json={"items": [{"strategy_id": strategy["strategy_id"], "symbol": "IF8888", "current_price": 130}]},
    )
    assert update_prices.status_code == 200
    assert float(update_prices.json()[0]["unrealized_pnl"]) > 0

    quantity_update = client.put(
        "/api/positions/manual-adjustments",
        json={"items": [{"strategy_id": strategy["strategy_id"], "symbol": "IF8888", "quantity": 20}]},
    )
    assert quantity_update.status_code == 200
    adjusted_position = quantity_update.json()[0]
    assert float(adjusted_position["quantity"]) == 20.0
    assert float(adjusted_position["avg_cost"]) < original_avg_cost

    market_value_update = client.put(
        "/api/positions/manual-adjustments",
        json={"items": [{"strategy_id": strategy["strategy_id"], "symbol": "IF8888", "market_value": 2600}]},
    )
    assert market_value_update.status_code == 200
    repriced_position = market_value_update.json()[0]
    assert float(repriced_position["market_value"]) == 2600.0
    assert float(repriced_position["current_price"]) == 130.0

    sell = client.post(
        "/api/trades",
        json={
            "strategy_id": strategy["strategy_id"],
            "symbol": "IF8888",
            "direction": "SELL",
            "quantity": 8,
            "price": 135,
            "commission": 2,
            "trade_time": now.isoformat(),
        },
    )
    assert sell.status_code == 200
    assert float(sell.json()["realized_pnl"]) > 0

    stats = client.get(f"/api/trades/stats?strategy_id={strategy['strategy_id']}")
    assert stats.status_code == 200
    assert stats.json()["total_trades"] == 3

    overview = client.get(f"/api/positions/overview?strategy_id={strategy['strategy_id']}")
    assert overview.status_code == 200
    assert float(overview.json()["total_unrealized_pnl"]) >= 0

    strategy_list = client.get("/api/strategies?page=1&page_size=10")
    assert strategy_list.status_code == 200
    first = next(item for item in strategy_list.json()["items"] if item["strategy_id"] == strategy["strategy_id"])
    assert first["cumulative_return_pct"] is not None
    assert first["annualized_return_pct"] is not None
    assert first["annualized_return_pct"] < 1000
    assert first["today_return_pct"] is not None
    assert first["max_drawdown_pct"] is not None

    csv_export = client.get(f"/api/trades?strategy_id={strategy['strategy_id']}&export=csv")
    assert csv_export.status_code == 200
    assert "trade_id" in csv_export.text


def test_strategy_dashboard_and_pages(client):
    now = now_naive()
    strategy = create_strategy(client)
    client.post(
        "/api/trades",
        json={
            "strategy_id": strategy["strategy_id"],
            "symbol": "RB9999",
            "direction": "BUY",
            "quantity": 10,
            "price": 100,
            "commission": 1,
            "trade_time": (now - timedelta(days=20)).isoformat(),
        },
    )
    client.put(
        "/api/positions/update-prices",
        json={"items": [{"strategy_id": strategy["strategy_id"], "symbol": "RB9999", "current_price": 110}]},
    )
    client.put(
        "/api/positions/manual-adjustments",
        json={"items": [{"strategy_id": strategy["strategy_id"], "symbol": "RB9999", "quantity": 12, "market_value": 1320}]},
    )
    client.post(
        "/api/trades",
        json={
            "strategy_id": strategy["strategy_id"],
            "symbol": "RB9999",
            "direction": "SELL",
            "quantity": 5,
            "price": 112,
            "commission": 1,
            "trade_time": now.isoformat(),
        },
    )

    dashboard = client.get(f"/api/strategies/{strategy['strategy_id']}/dashboard")
    assert dashboard.status_code == 200
    data = dashboard.json()
    assert data["strategy"]["name"] == strategy["name"]
    assert len(data["current_positions"]) == 1
    assert len(data["closed_positions"]) == 0
    assert len(data["equity_curve"]) >= 10
    assert len(data["recent_trades"]) == 2
    assert "strategy_return_pct" in data["evaluation_metrics"]
    assert "strategy_annualized_return_pct" in data["evaluation_metrics"]
    assert "benchmark_return_pct" in data["evaluation_metrics"]
    assert "excess_return_pct" in data["evaluation_metrics"]
    assert "alpha" in data["evaluation_metrics"]
    assert "beta" in data["evaluation_metrics"]
    assert "sharpe_ratio" in data["evaluation_metrics"]
    assert "sortino_ratio" in data["evaluation_metrics"]
    assert "information_ratio" in data["evaluation_metrics"]
    assert "win_rate" in data["evaluation_metrics"]
    assert "profit_loss_ratio" in data["evaluation_metrics"]
    assert "daily_win_rate" in data["evaluation_metrics"]
    assert "profit_trade_count" in data["evaluation_metrics"]
    assert "loss_trade_count" in data["evaluation_metrics"]
    assert "strategy_volatility_pct" in data["evaluation_metrics"]
    assert "benchmark_volatility_pct" in data["evaluation_metrics"]
    assert "max_drawdown_period" in data["evaluation_metrics"]

    detail_page = client.get(f"/strategies/{strategy['strategy_id']}")
    assert detail_page.status_code == 200
    assert "策略详情" in detail_page.text

    manual_order_page = client.get("/manual-order")
    assert manual_order_page.status_code == 200
    assert "manualOrderForm" in manual_order_page.text
    assert "/static/manual_order.js" in manual_order_page.text



def test_closed_position_history_flow(client):
    strategy = create_strategy(client)
    client.post(
        "/api/trades",
        json={
            "strategy_id": strategy["strategy_id"],
            "symbol": "RB9999",
            "direction": "BUY",
            "quantity": 10,
            "price": 100,
            "commission": 1,
            "trade_time": "2026-02-01T09:30:00",
        },
    )
    client.put(
        "/api/positions/update-prices",
        json={"items": [{"strategy_id": strategy["strategy_id"], "symbol": "RB9999", "current_price": 110}]},
    )
    client.post(
        "/api/trades",
        json={
            "strategy_id": strategy["strategy_id"],
            "symbol": "RB9999",
            "direction": "SELL",
            "quantity": 5,
            "price": 112,
            "commission": 1,
            "trade_time": "2026-03-05T09:30:00",
        },
    )
    client.post(
        "/api/trades",
        json={
            "strategy_id": strategy["strategy_id"],
            "symbol": "RB9999",
            "direction": "SELL",
            "quantity": 5,
            "price": 115,
            "commission": 1,
            "trade_time": "2026-03-07T09:30:00",
        },
    )

    positions = client.get(f"/api/positions?strategy_id={strategy['strategy_id']}")
    assert positions.status_code == 200
    assert positions.json() == []

    history = client.get(f"/api/positions/history?strategy_id={strategy['strategy_id']}")
    assert history.status_code == 200
    rows = history.json()
    assert len(rows) == 1
    assert rows[0]["symbol"] == "RB9999"
    assert float(rows[0]["realized_pnl"]) != 0.0

