from __future__ import annotations

from decimal import Decimal

from examples.http_backtest_template import Bar, SimpleMaStrategy, TradeApi


class ResponseBridge:
    def __init__(self, response):
        self._response = response
        self.status_code = response.status_code
        self.text = response.text

    def json(self):
        return self._response.json()


class SessionBridge:
    def __init__(self, client):
        self.client = client

    def request(self, method, url, json=None, timeout=None):
        path = url.split("//", 1)[-1]
        path = "/" + path.split("/", 1)[1]
        return ResponseBridge(self.client.request(method, path, json=json))


def create_active_strategy(client, name: str):
    response = client.post(
        "/api/strategies",
        json={
            "name": name,
            "description": "test",
            "type": "template",
            "parameters": {"initial_capital": 100000, "benchmark_annual_return": 0.03},
            "status": "active",
        },
    )
    assert response.status_code == 200
    return response.json()["strategy_id"]


def build_api(client):
    return TradeApi("http://testserver", session=SessionBridge(client))


def test_trade_api_buy_sell_and_positions(client):
    strategy_id = create_active_strategy(client, "minimal-api")
    api = build_api(client)

    api.buy(strategy_id, "300308.SZ", Decimal("100"), Decimal("10"), "2025-01-06T15:00:00")
    positions = api.get_positions(strategy_id)
    assert len(positions) == 1
    assert api.get_qty(strategy_id, "300308.SZ") == Decimal("100.000000")

    api.sell(strategy_id, "300308.SZ", Decimal("100"), Decimal("11"), "2025-01-07T15:00:00")
    assert api.get_positions(strategy_id) == []
    assert api.get_qty(strategy_id, "300308.SZ") == Decimal("0")


def test_simple_ma_strategy_runs_with_minimal_http_calls(client, capsys):
    strategy_id = create_active_strategy(client, "minimal-strategy")
    api = build_api(client)
    bars = [
        Bar("2025-01-01T15:00:00", "2025-01-01", Decimal("10")),
        Bar("2025-01-02T15:00:00", "2025-01-02", Decimal("11")),
        Bar("2025-01-03T15:00:00", "2025-01-03", Decimal("12")),
        Bar("2025-01-06T15:00:00", "2025-01-06", Decimal("13")),
        Bar("2025-01-07T15:00:00", "2025-01-07", Decimal("16")),
        Bar("2025-01-08T15:00:00", "2025-01-08", Decimal("14")),
    ]

    summary = SimpleMaStrategy(
        api=api,
        strategy_id=strategy_id,
        symbol="300308.SZ",
        initial_cash=Decimal("100000"),
        lot_size=Decimal("100"),
        ma_window=3,
        close_last=True,
    ).run(bars)
    captured = capsys.readouterr()

    assert len(summary["orders"]) == 2
    assert summary["positions"] == []
    assert summary["total_asset"] > Decimal("100000")
    assert "Summary" in captured.out

    stats = client.get(f"/api/trades/stats?strategy_id={strategy_id}")
    assert stats.status_code == 200
    assert stats.json()["total_trades"] == 2
