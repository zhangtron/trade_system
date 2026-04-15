from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import BigInteger, JSON, DateTime, Enum as SqlEnum, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
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
    closed_positions: Mapped[list["ClosedPosition"]] = relationship(back_populates="strategy")


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index("ix_trades_strategy_id", "strategy_id"),
        Index("ix_trades_symbol", "symbol"),
        Index("ix_trades_trade_time", "trade_time"),
        Index("idx_trades_exec_status_time", "exec_status", "trade_time"),
        Index("idx_trades_submit_entrust_no", "submit_entrust_no"),
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
    exec_status: Mapped[str | None] = mapped_column(String(20))
    claimed_by: Mapped[str | None] = mapped_column(String(64))
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime)
    submit_entrust_no: Mapped[str | None] = mapped_column(String(64))
    submit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    submit_quantity: Mapped[int | None] = mapped_column(BigInteger)
    last_submit_at: Mapped[datetime | None] = mapped_column(DateTime)
    exec_try_count: Mapped[int] = mapped_column(default=0, nullable=False)
    fail_reason: Mapped[str | None] = mapped_column(String(255))
    filled_at: Mapped[datetime | None] = mapped_column(DateTime)
    filled_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    strategy: Mapped["Strategy"] = relationship(back_populates="trades")


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        Index("ix_positions_strategy_id", "strategy_id"),
        Index("ix_positions_symbol", "symbol"),
        UniqueConstraint("strategy_id", "symbol", name="uq_positions_strategy_symbol"),
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


class ClosedPosition(Base):
    __tablename__ = "position_history"
    __table_args__ = (
        Index("ix_position_history_strategy_id", "strategy_id"),
        Index("ix_position_history_symbol", "symbol"),
        Index("ix_position_history_close_time", "close_time"),
    )

    history_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.strategy_id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(30), nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    close_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    entry_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    exit_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    close_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0"))
    total_commission: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0"))
    close_trade_id: Mapped[int | None] = mapped_column(ForeignKey("trades.trade_id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive, nullable=False)

    strategy: Mapped["Strategy"] = relationship(back_populates="closed_positions")
