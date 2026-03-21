from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import StrategyStatus, TradeDirection


class StrategyCreate(BaseModel):
    name: str
    description: str | None = None
    type: str
    parameters: dict[str, Any] | None = None
    status: StrategyStatus = StrategyStatus.DRAFT


class StrategyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    type: str | None = None
    parameters: dict[str, Any] | None = None


class StrategyStatusUpdate(BaseModel):
    status: StrategyStatus


class StrategyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    strategy_id: int
    name: str
    description: str | None
    type: str
    parameters: dict[str, Any] | None
    status: StrategyStatus
    version: int
    created_at: datetime
    updated_at: datetime
    cumulative_return_pct: float | None = None
    annualized_return_pct: float | None = None
    today_return_pct: float | None = None
    max_drawdown_pct: float | None = None
    cumulative_profit: float | None = None


class PaginatedStrategies(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[StrategyOut]


class TradeCreate(BaseModel):
    strategy_id: int
    symbol: str
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    commission: Decimal = Field(default=Decimal("0"), ge=0)
    trade_time: datetime | None = None
    remark: str | None = None


class TradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trade_id: int
    strategy_id: int
    symbol: str
    direction: TradeDirection
    quantity: Decimal
    price: Decimal
    amount: Decimal
    commission: Decimal
    realized_pnl: Decimal | None
    trade_time: datetime
    remark: str | None


class PaginatedTrades(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TradeOut]


class TradeStats(BaseModel):
    total_trades: int
    total_amount: Decimal
    total_commission: Decimal
    total_realized_pnl: Decimal
    by_symbol: list[dict[str, Any]]
    by_strategy: list[dict[str, Any]]


class PositionPriceUpdateItem(BaseModel):
    symbol: str
    current_price: Decimal = Field(gt=0)
    strategy_id: int | None = None


class PositionPriceUpdate(BaseModel):
    items: list[PositionPriceUpdateItem]


class PositionManualAdjustmentItem(BaseModel):
    symbol: str
    strategy_id: int | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    market_value: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_payload(self):
        if self.quantity is None and self.market_value is None:
            raise ValueError("?????????????")
        return self


class PositionManualAdjustment(BaseModel):
    items: list[PositionManualAdjustmentItem]


class PositionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position_id: int
    strategy_id: int
    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    current_price: Decimal | None
    market_value: Decimal | None
    unrealized_pnl: Decimal | None
    open_time: datetime
    updated_at: datetime


class PositionOverview(BaseModel):
    total_market_value: Decimal
    total_unrealized_pnl: Decimal
    invested_cost: Decimal
    estimated_total_assets: Decimal
    positions: int


class EvaluationCreate(BaseModel):
    strategy_id: int
    start_date: date
    end_date: date
    initial_capital: Decimal = Field(gt=0)
    risk_free_rate: Decimal = Decimal("0.02")
    benchmark_annual_return: Decimal = Decimal("0.03")


class EvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    eval_id: int
    strategy_id: int
    start_date: date
    end_date: date
    initial_capital: Decimal
    final_value: Decimal | None
    metrics: dict[str, Any] | None
    created_at: datetime


class EquityPoint(BaseModel):
    curve_date: date
    equity_value: Decimal
    drawdown: Decimal | None


class StrategyPositionHistory(BaseModel):
    trade_id: int
    symbol: str
    direction: TradeDirection
    quantity_change: Decimal
    position_quantity: Decimal
    avg_cost: Decimal
    market_price: Decimal | None
    unrealized_pnl: Decimal
    trade_time: datetime


class StrategyDetail(BaseModel):
    strategy: StrategyOut
    evaluation_metrics: dict[str, Any]
    current_positions: list[PositionOut]
    position_history: list[StrategyPositionHistory]
    equity_curve: list[EquityPoint]
    recent_trades: list[TradeOut]
