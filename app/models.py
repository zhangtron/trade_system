from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import JSON, Date, DateTime, Enum as SqlEnum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def now_utc_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class StrategyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class TradeDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Strategy(Base):
    __tablename__ = "strategies"

    strategy_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[StrategyStatus] = mapped_column(SqlEnum(StrategyStatus), default=StrategyStatus.DRAFT, nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive, onupdate=now_utc_naive, nullable=False)

    trades: Mapped[list["Trade"]] = relationship(back_populates="strategy")
    positions: Mapped[list["Position"]] = relationship(back_populates="strategy")
    evaluations: Mapped[list["Evaluation"]] = relationship(back_populates="strategy")


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index("ix_trades_strategy_id", "strategy_id"),
        Index("ix_trades_symbol", "symbol"),
        Index("ix_trades_trade_time", "trade_time"),
    )

    trade_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.strategy_id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    direction: Mapped[TradeDirection] = mapped_column(SqlEnum(TradeDirection), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    commission: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("0"))
    realized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    trade_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive, nullable=False)
    remark: Mapped[str | None] = mapped_column(String(255))

    strategy: Mapped["Strategy"] = relationship(back_populates="trades")


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        Index("ix_positions_strategy_id", "strategy_id"),
        Index("ix_positions_symbol", "symbol"),
    )

    position_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.strategy_id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    market_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    unrealized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    open_time: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive, onupdate=now_utc_naive, nullable=False)

    strategy: Mapped["Strategy"] = relationship(back_populates="positions")


class Evaluation(Base):
    __tablename__ = "evaluations"

    eval_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.strategy_id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    initial_capital: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    final_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    metrics: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive, nullable=False)

    strategy: Mapped["Strategy"] = relationship(back_populates="evaluations")
    equity_curve: Mapped[list["EquityCurve"]] = relationship(back_populates="evaluation", cascade="all, delete-orphan")


class EquityCurve(Base):
    __tablename__ = "equity_curve"

    curve_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    eval_id: Mapped[int] = mapped_column(ForeignKey("evaluations.eval_id"), nullable=False)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.strategy_id"), nullable=False)
    curve_date: Mapped[date] = mapped_column(Date, nullable=False)
    equity_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    drawdown: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))

    evaluation: Mapped["Evaluation"] = relationship(back_populates="equity_curve")
