from __future__ import annotations

import csv
import io
import math
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import ClosedPosition, Position, Strategy, StrategyStatus, Trade, TradeDirection

TWO = Decimal("0.01")
FOUR = Decimal("0.0001")
SIX = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")
DEFAULT_INITIAL_CAPITAL = Decimal("100000")
DEFAULT_BENCHMARK_ANNUAL_RETURN = Decimal("0.03")
SHORT_PERIOD_THRESHOLD_DAYS = 30
EPSILON = Decimal("0.0000000001")
MAX_RATIO_VALUE = Decimal("9999.9999")


def now_utc_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(TWO, rounding=ROUND_HALF_UP)


def clip_ratio(value: Decimal) -> Decimal:
    if value > MAX_RATIO_VALUE:
        return MAX_RATIO_VALUE
    if value < -MAX_RATIO_VALUE:
        return -MAX_RATIO_VALUE
    return value


def quantize_four(value: Decimal) -> Decimal:
    return clip_ratio(value).quantize(FOUR, rounding=ROUND_HALF_UP)


def quantize_qty(value: Decimal) -> Decimal:
    return value.quantize(SIX, rounding=ROUND_HALF_UP)


def quantize_commission(value: Decimal) -> Decimal:
    return value.quantize(FOUR, rounding=ROUND_HALF_UP)


def safe_decimal(value: Any, default: Decimal = ZERO) -> Decimal:
    if value is None:
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def ratio_to_pct(value: Decimal) -> Decimal:
    return value * HUNDRED


def pct_to_ratio(value: Decimal) -> Decimal:
    return value / HUNDRED


def clip_percent(value: Decimal) -> Decimal:
    if value < Decimal("-100"):
        return Decimal("-100")
    if value > Decimal("99999.99"):
        return Decimal("99999.99")
    return value


def get_strategy_initial_capital(strategy: Strategy) -> Decimal:
    parameters = strategy.parameters or {}
    initial_capital = safe_decimal(parameters.get("initial_capital"), DEFAULT_INITIAL_CAPITAL)
    return initial_capital if initial_capital > ZERO else DEFAULT_INITIAL_CAPITAL


def get_strategy_benchmark_annual_return(strategy: Strategy, override: Decimal | None = None) -> Decimal:
    if override is not None:
        value = safe_decimal(override, DEFAULT_BENCHMARK_ANNUAL_RETURN)
    else:
        parameters = strategy.parameters or {}
        value = safe_decimal(parameters.get("benchmark_annual_return"), DEFAULT_BENCHMARK_ANNUAL_RETURN)
    if value <= Decimal("-0.99"):
        return Decimal("-0.99")
    return value


def annualize_return(total_return_ratio: Decimal, days: int) -> Decimal:
    if days <= 0:
        return ZERO
    if total_return_ratio <= -ONE:
        return Decimal("-100")
    if days < SHORT_PERIOD_THRESHOLD_DAYS:
        annualized_ratio = total_return_ratio * Decimal(365) / Decimal(days)
    else:
        annualized_ratio = Decimal(str(float(ONE + total_return_ratio) ** (365 / days) - 1))
    return clip_percent(quantize_money(ratio_to_pct(annualized_ratio)))


def serialize_strategy(strategy: Strategy, metrics: dict[str, float] | None = None) -> dict[str, Any]:
    metrics = metrics or {}
    return {
        "strategy_id": strategy.strategy_id,
        "name": strategy.name,
        "description": strategy.description,
        "type": strategy.type,
        "parameters": strategy.parameters,
        "status": strategy.status,
        "version": strategy.version,
        "created_at": strategy.created_at,
        "updated_at": strategy.updated_at,
        "cumulative_return_pct": metrics.get("cumulative_return_pct"),
        "annualized_return_pct": metrics.get("annualized_return_pct"),
        "today_return_pct": metrics.get("today_return_pct"),
        "max_drawdown_pct": metrics.get("max_drawdown_pct"),
        "cumulative_profit": metrics.get("cumulative_profit"),
    }


def mean(values: list[Decimal]) -> Decimal:
    return sum(values, start=ZERO) / Decimal(len(values)) if values else ZERO


def population_std(values: list[Decimal]) -> Decimal:
    if not values:
        return ZERO
    avg = mean(values)
    variance = sum(((value - avg) ** 2 for value in values), start=ZERO) / Decimal(len(values))
    return Decimal(str(math.sqrt(float(variance))))


def annualized_volatility(daily_returns: list[Decimal]) -> Decimal:
    if not daily_returns:
        return ZERO
    return population_std(daily_returns) * Decimal(str(math.sqrt(252)))


def sharpe_ratio(daily_returns: list[Decimal], risk_free_rate: Decimal) -> Decimal:
    if not daily_returns:
        return ZERO
    rf_daily = risk_free_rate / Decimal("252")
    excess = [value - rf_daily for value in daily_returns]
    std = population_std(daily_returns)
    if std <= EPSILON:
        return ZERO
    return mean(excess) / std * Decimal(str(math.sqrt(252)))


def sortino_ratio(daily_returns: list[Decimal], risk_free_rate: Decimal) -> Decimal:
    if not daily_returns:
        return ZERO
    rf_daily = risk_free_rate / Decimal("252")
    downside = [min(value - rf_daily, ZERO) for value in daily_returns]
    downside_only = [abs(value) for value in downside if value < ZERO]
    if not downside_only:
        return ZERO
    downside_std = population_std(downside_only)
    if downside_std <= EPSILON:
        return ZERO
    return mean([value - rf_daily for value in daily_returns]) / downside_std * Decimal(str(math.sqrt(252)))


def daily_returns_from_curve(curve: list[dict[str, Any]]) -> list[Decimal]:
    returns: list[Decimal] = []
    for index in range(1, len(curve)):
        prev = safe_decimal(curve[index - 1]["equity_value"])
        current = safe_decimal(curve[index]["equity_value"])
        if prev > ZERO:
            returns.append((current - prev) / prev)
    return returns


def max_drawdown_stats(curve: list[dict[str, Any]]) -> tuple[Decimal, tuple[date, date]]:
    if not curve:
        today = now_utc_naive().date()
        return ZERO, (today, today)

    peak_value = safe_decimal(curve[0]["equity_value"])
    peak_date = curve[0]["curve_date"]
    max_drawdown = ZERO
    drawdown_period = (peak_date, peak_date)

    for point in curve:
        equity = safe_decimal(point["equity_value"])
        curve_date = point["curve_date"]
        if equity > peak_value:
            peak_value = equity
            peak_date = curve_date
        drawdown = ZERO if peak_value == ZERO else (peak_value - equity) / peak_value
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            drawdown_period = (peak_date, curve_date)
    return max_drawdown, drawdown_period


def build_benchmark_curve(start_date: date, end_date: date, initial_capital: Decimal, benchmark_annual_return: Decimal) -> list[dict[str, Any]]:
    if end_date < start_date:
        return []

    daily_ratio = Decimal(str(float(ONE + benchmark_annual_return) ** (1 / 365) - 1)) if benchmark_annual_return > Decimal("-0.99") else Decimal("-0.99")
    curve: list[dict[str, Any]] = []
    value = initial_capital
    current_day = start_date
    is_first = True
    while current_day <= end_date:
        if not is_first:
            value = quantize_money(value * (ONE + daily_ratio))
        curve.append({"curve_date": current_day, "equity_value": value})
        is_first = False
        current_day += timedelta(days=1)
    return curve


def build_excess_curve(strategy_curve: list[dict[str, Any]], benchmark_curve: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not strategy_curve or not benchmark_curve:
        return []
    curve: list[dict[str, Any]] = []
    base = Decimal("1")
    for index, point in enumerate(strategy_curve):
        benchmark_value = safe_decimal(benchmark_curve[index]["equity_value"], ONE)
        strategy_value = safe_decimal(point["equity_value"], ONE)
        ratio = base if benchmark_value == ZERO else strategy_value / benchmark_value
        curve.append({"curve_date": point["curve_date"], "equity_value": quantize_four(ratio)})
    return curve


def recalc_position(position: Position) -> None:
    if position.current_price is not None:
        position.market_value = quantize_money(position.current_price * position.quantity)
        position.unrealized_pnl = quantize_money((position.current_price - position.avg_cost) * position.quantity)
    else:
        position.market_value = None
        position.unrealized_pnl = None


def apply_position_manual_adjustment(
    position: Position,
    quantity: Decimal | None = None,
    market_value: Decimal | None = None,
) -> Position:
    original_cost_basis = safe_decimal(position.avg_cost) * safe_decimal(position.quantity)

    if quantity is not None:
        new_quantity = quantize_qty(safe_decimal(quantity))
        if new_quantity <= ZERO:
            raise ValueError("???????? 0")
        position.quantity = new_quantity
        position.avg_cost = quantize_qty(original_cost_basis / new_quantity) if original_cost_basis > ZERO else ZERO

    adjusted_market_value = None
    if market_value is not None:
        adjusted_market_value = quantize_money(safe_decimal(market_value))
        if position.quantity <= ZERO:
            raise ValueError("???????? 0")
        position.current_price = quantize_qty(adjusted_market_value / position.quantity)

    position.updated_at = now_utc_naive()
    recalc_position(position)

    if adjusted_market_value is not None:
        position.market_value = adjusted_market_value
        position.unrealized_pnl = quantize_money(adjusted_market_value - (position.avg_cost * position.quantity))

    return position


def ensure_strategy_tradeable(db: Session, strategy_id: int) -> Strategy:
    strategy = db.get(Strategy, strategy_id)
    if not strategy:
        raise ValueError("策略不存在")
    if strategy.status != StrategyStatus.ACTIVE:
        raise ValueError("仅激活状态的策略可进行交易")
    return strategy


def apply_buy(db: Session, payload) -> Trade:
    ensure_strategy_tradeable(db, payload.strategy_id)
    quantity = Decimal(payload.quantity)
    price = Decimal(payload.price)
    commission = Decimal(payload.commission)
    amount = quantize_money(quantity * price)
    trade = Trade(
        strategy_id=payload.strategy_id,
        symbol=payload.symbol.upper(),
        direction=TradeDirection.BUY,
        quantity=quantize_qty(quantity),
        price=quantize_qty(price),
        amount=amount,
        commission=commission,
        realized_pnl=ZERO,
        trade_time=payload.trade_time or now_utc_naive(),
        remark=payload.remark,
        exec_status="NEW",
        exec_try_count=0,
    )
    position = db.execute(
        select(Position).where(Position.strategy_id == payload.strategy_id, Position.symbol == payload.symbol.upper())
    ).scalar_one_or_none()
    if position:
        total_qty = position.quantity + quantity
        total_cost = (position.avg_cost * position.quantity) + amount + commission
        position.avg_cost = quantize_qty(total_cost / total_qty)
        position.quantity = quantize_qty(total_qty)
        position.updated_at = now_utc_naive()
        if position.current_price is None:
            position.current_price = price
    else:
        position = Position(
            strategy_id=payload.strategy_id,
            symbol=payload.symbol.upper(),
            quantity=quantize_qty(quantity),
            avg_cost=quantize_qty((amount + commission) / quantity),
            current_price=quantize_qty(price),
            open_time=payload.trade_time or now_utc_naive(),
        )
        db.add(position)
    recalc_position(position)
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade


def apply_sell(db: Session, payload) -> Trade:
    ensure_strategy_tradeable(db, payload.strategy_id)
    quantity = Decimal(payload.quantity)
    price = Decimal(payload.price)
    commission = Decimal(payload.commission)
    position = db.execute(
        select(Position).where(Position.strategy_id == payload.strategy_id, Position.symbol == payload.symbol.upper())
    ).scalar_one_or_none()
    if not position or position.quantity < quantity:
        raise ValueError("持仓数量不足")

    closing_open_time = position.open_time
    closing_symbol = position.symbol
    closing_strategy_id = position.strategy_id

    amount = quantize_money(quantity * price)
    cost_basis = quantize_money(position.avg_cost * quantity)
    realized_pnl = quantize_money(amount - cost_basis - commission)
    trade = Trade(
        strategy_id=payload.strategy_id,
        symbol=payload.symbol.upper(),
        direction=TradeDirection.SELL,
        quantity=quantize_qty(quantity),
        price=quantize_qty(price),
        amount=amount,
        commission=commission,
        realized_pnl=realized_pnl,
        trade_time=payload.trade_time or now_utc_naive(),
        remark=payload.remark,
        exec_status="NEW",
        exec_try_count=0,
    )
    position.quantity = quantize_qty(position.quantity - quantity)
    position.current_price = quantize_qty(price)
    position.updated_at = now_utc_naive()
    db.add(trade)
    db.flush()
    if position.quantity == ZERO:
        lifecycle_trades = db.execute(
            select(Trade)
            .where(
                Trade.strategy_id == closing_strategy_id,
                Trade.symbol == closing_symbol,
                Trade.trade_time >= closing_open_time,
                Trade.trade_time <= trade.trade_time,
                Trade.trade_id <= trade.trade_id,
            )
            .order_by(Trade.trade_time.asc(), Trade.trade_id.asc())
        ).scalars().all()
        buy_qty = sum((item.quantity for item in lifecycle_trades if item.direction == TradeDirection.BUY), start=ZERO)
        sell_qty = sum((item.quantity for item in lifecycle_trades if item.direction == TradeDirection.SELL), start=ZERO)
        buy_cost = sum(
            ((item.amount + item.commission) for item in lifecycle_trades if item.direction == TradeDirection.BUY),
            start=ZERO,
        )
        sell_amount = sum((item.amount for item in lifecycle_trades if item.direction == TradeDirection.SELL), start=ZERO)
        realized_total = sum(((item.realized_pnl or ZERO) for item in lifecycle_trades if item.direction == TradeDirection.SELL), start=ZERO)
        total_commission = sum((item.commission for item in lifecycle_trades), start=ZERO)
        db.add(
            ClosedPosition(
                strategy_id=closing_strategy_id,
                symbol=closing_symbol,
                open_time=closing_open_time,
                close_time=trade.trade_time,
                entry_quantity=quantize_qty(buy_qty if buy_qty > ZERO else quantity),
                exit_quantity=quantize_qty(sell_qty if sell_qty > ZERO else quantity),
                avg_cost=quantize_qty(buy_cost / buy_qty) if buy_qty > ZERO else quantize_qty(position.avg_cost),
                close_price=quantize_qty(sell_amount / sell_qty) if sell_qty > ZERO else quantize_qty(price),
                realized_pnl=quantize_money(realized_total),
                total_commission=quantize_commission(total_commission),
                close_trade_id=trade.trade_id,
                created_at=now_utc_naive(),
            )
        )
        db.delete(position)
    else:
        recalc_position(position)
    db.commit()
    db.refresh(trade)
    return trade


def paginate(query: Select, page: int, page_size: int):
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size)


def export_trades_csv(trades: list[Trade]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "trade_id",
        "strategy_id",
        "symbol",
        "direction",
        "quantity",
        "price",
        "amount",
        "commission",
        "realized_pnl",
        "trade_time",
        "remark",
        "exec_status",
        "claimed_by",
        "claimed_at",
        "submit_entrust_no",
        "submit_price",
        "submit_quantity",
        "last_submit_at",
        "exec_try_count",
        "fail_reason",
        "filled_at",
        "filled_amount",
    ])
    for trade in trades:
        writer.writerow([
            trade.trade_id,
            trade.strategy_id,
            trade.symbol,
            trade.direction.value,
            trade.quantity,
            trade.price,
            trade.amount,
            trade.commission,
            trade.realized_pnl,
            trade.trade_time.isoformat(),
            trade.remark or "",
            trade.exec_status or "",
            trade.claimed_by or "",
            trade.claimed_at.isoformat() if trade.claimed_at else "",
            trade.submit_entrust_no or "",
            trade.submit_price if trade.submit_price is not None else "",
            trade.submit_quantity if trade.submit_quantity is not None else "",
            trade.last_submit_at.isoformat() if trade.last_submit_at else "",
            trade.exec_try_count,
            trade.fail_reason or "",
            trade.filled_at.isoformat() if trade.filled_at else "",
            trade.filled_amount if trade.filled_amount is not None else "",
        ])
    return buf.getvalue()


def position_overview(db: Session, strategy_id: int | None = None) -> dict:
    query = select(Position)
    if strategy_id is not None:
        query = query.where(Position.strategy_id == strategy_id)
    positions = db.execute(query).scalars().all()
    total_market_value = sum(((position.market_value or ZERO) for position in positions), start=ZERO)
    total_unrealized_pnl = sum(((position.unrealized_pnl or ZERO) for position in positions), start=ZERO)
    invested_cost = sum(((position.avg_cost * position.quantity) for position in positions), start=ZERO)
    return {
        "total_market_value": quantize_money(total_market_value),
        "total_unrealized_pnl": quantize_money(total_unrealized_pnl),
        "invested_cost": quantize_money(invested_cost),
        "estimated_total_assets": quantize_money(total_market_value),
        "positions": len(positions),
    }


def load_strategy_trades(db: Session, strategy_id: int, descending: bool = False) -> list[Trade]:
    query = select(Trade).where(Trade.strategy_id == strategy_id)
    query = query.order_by(Trade.trade_time.desc() if descending else Trade.trade_time.asc())
    return db.execute(query).scalars().all()


def load_strategy_positions(db: Session, strategy_id: int) -> list[Position]:
    query = select(Position).where(Position.strategy_id == strategy_id).order_by(Position.updated_at.desc())
    return db.execute(query).scalars().all()


def load_strategy_closed_positions(db: Session, strategy_id: int) -> list[ClosedPosition]:
    query = select(ClosedPosition).where(ClosedPosition.strategy_id == strategy_id).order_by(ClosedPosition.close_time.desc())
    return db.execute(query).scalars().all()


def build_strategy_equity_curve(
    strategy: Strategy,
    trades: list[Trade],
    current_positions: list[Position],
    initial_capital_override: Decimal | None = None,
) -> list[dict[str, Any]]:
    initial_capital = initial_capital_override if initial_capital_override is not None else get_strategy_initial_capital(strategy)
    start_date = trades[0].trade_time.date() if trades else strategy.created_at.date()
    end_date = now_utc_naive().date()
    if end_date < start_date:
        end_date = start_date

    trades_by_day: dict[date, list[Trade]] = defaultdict(list)
    for trade in trades:
        trades_by_day[trade.trade_time.date()].append(trade)

    live_prices = {position.symbol: position.current_price for position in current_positions if position.current_price is not None}
    states: dict[str, dict[str, Decimal | None]] = {}
    running_realized = ZERO
    curve: list[dict[str, Any]] = []

    current_day = start_date
    while current_day <= end_date:
        for trade in trades_by_day[current_day]:
            state = states.setdefault(trade.symbol, {"quantity": ZERO, "avg_cost": ZERO, "last_price": None})
            quantity = safe_decimal(state["quantity"])
            avg_cost = safe_decimal(state["avg_cost"])
            if trade.direction == TradeDirection.BUY:
                total_qty = quantity + trade.quantity
                total_cost = (avg_cost * quantity) + trade.amount + trade.commission
                quantity = quantize_qty(total_qty)
                avg_cost = quantize_qty(total_cost / total_qty) if total_qty > ZERO else ZERO
            else:
                quantity = quantize_qty(quantity - trade.quantity)
                if quantity <= ZERO:
                    quantity = ZERO
                    avg_cost = ZERO
            state["quantity"] = quantity
            state["avg_cost"] = avg_cost
            state["last_price"] = Decimal(trade.price)
            running_realized += trade.realized_pnl or ZERO

        if current_day == end_date:
            for symbol, current_price in live_prices.items():
                state = states.setdefault(symbol, {"quantity": ZERO, "avg_cost": ZERO, "last_price": None})
                if current_price is not None:
                    state["last_price"] = Decimal(current_price)

        unrealized = ZERO
        for state in states.values():
            quantity = safe_decimal(state["quantity"])
            last_price = state["last_price"]
            avg_cost = safe_decimal(state["avg_cost"])
            if quantity > ZERO and last_price is not None:
                unrealized += (Decimal(last_price) - avg_cost) * quantity

        equity = quantize_money(initial_capital + running_realized + quantize_money(unrealized))
        curve.append({"curve_date": current_day, "equity_value": equity, "drawdown": ZERO})
        current_day += timedelta(days=1)

    max_drawdown_ratio, _ = max_drawdown_stats(curve)
    _ = max_drawdown_ratio
    peak_value = safe_decimal(curve[0]["equity_value"], initial_capital) if curve else initial_capital
    for point in curve:
        equity = safe_decimal(point["equity_value"], initial_capital)
        if equity > peak_value:
            peak_value = equity
        drawdown = ZERO if peak_value == ZERO else (peak_value - equity) / peak_value
        point["drawdown"] = quantize_money(ratio_to_pct(drawdown))
    return curve


def calculate_strategy_metrics(strategy: Strategy, equity_curve: list[dict[str, Any]]) -> dict[str, float]:
    initial_capital = get_strategy_initial_capital(strategy)
    if not equity_curve or initial_capital <= ZERO:
        return {
            "cumulative_return_pct": 0.0,
            "annualized_return_pct": 0.0,
            "today_return_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "cumulative_profit": 0.0,
        }

    final_equity = safe_decimal(equity_curve[-1]["equity_value"], initial_capital)
    cumulative_profit = quantize_money(final_equity - initial_capital)
    cumulative_return_ratio = (final_equity - initial_capital) / initial_capital
    days = max((equity_curve[-1]["curve_date"] - equity_curve[0]["curve_date"]).days + 1, 1)
    annualized_return_pct = annualize_return(cumulative_return_ratio, days)

    today_return = ZERO
    if len(equity_curve) > 1:
        prev_equity = safe_decimal(equity_curve[-2]["equity_value"], initial_capital)
        if prev_equity > ZERO:
            today_return = (final_equity - prev_equity) / prev_equity

    max_drawdown_ratio, _ = max_drawdown_stats(equity_curve)

    return {
        "cumulative_return_pct": round(float(quantize_money(ratio_to_pct(cumulative_return_ratio))), 4),
        "annualized_return_pct": round(float(annualized_return_pct), 4),
        "today_return_pct": round(float(quantize_money(ratio_to_pct(today_return))), 4),
        "max_drawdown_pct": round(float(quantize_money(ratio_to_pct(max_drawdown_ratio))), 4),
        "cumulative_profit": round(float(cumulative_profit), 4),
    }




def build_live_evaluation_metrics(strategy: Strategy, trades: list[Trade], current_positions: list[Position]) -> dict[str, Any]:
    initial_capital = get_strategy_initial_capital(strategy)
    equity_curve = build_strategy_equity_curve(strategy, trades, current_positions, initial_capital_override=initial_capital)
    if not equity_curve:
        return {}
    benchmark_return = get_strategy_benchmark_annual_return(strategy)
    benchmark_curve = build_benchmark_curve(
        equity_curve[0]["curve_date"],
        equity_curve[-1]["curve_date"],
        quantize_money(initial_capital),
        benchmark_return,
    )
    return build_evaluation_metrics(
        strategy=strategy,
        equity_curve=equity_curve,
        benchmark_curve=benchmark_curve,
        trades=trades,
        risk_free_rate=Decimal("0.02"),
        benchmark_annual_return=benchmark_return,
        initial_capital=quantize_money(initial_capital),
    )

def build_strategy_snapshot(db: Session, strategy: Strategy) -> dict[str, Any]:
    trades = load_strategy_trades(db, strategy.strategy_id)
    positions = load_strategy_positions(db, strategy.strategy_id)
    closed_positions = load_strategy_closed_positions(db, strategy.strategy_id)
    equity_curve = build_strategy_equity_curve(strategy, trades, positions)
    metrics = calculate_strategy_metrics(strategy, equity_curve)
    evaluation_metrics = build_live_evaluation_metrics(strategy, trades, positions)
    return {
        "strategy": serialize_strategy(strategy, metrics),
        "evaluation_metrics": evaluation_metrics,
        "current_positions": positions,
        "closed_positions": closed_positions,
        "equity_curve": equity_curve,
        "recent_trades": list(reversed(trades[-20:])),
        "metrics": metrics,
    }


def build_strategy_dashboard(db: Session, strategy_id: int) -> dict[str, Any]:
    strategy = db.get(Strategy, strategy_id)
    if not strategy:
        raise ValueError("?????")
    snapshot = build_strategy_snapshot(db, strategy)
    return {
        "strategy": snapshot["strategy"],
        "evaluation_metrics": snapshot["evaluation_metrics"],
        "current_positions": snapshot["current_positions"],
        "closed_positions": snapshot["closed_positions"],
        "equity_curve": snapshot["equity_curve"],
        "recent_trades": snapshot["recent_trades"],
    }


def build_evaluation_metrics(
    strategy: Strategy,
    equity_curve: list[dict[str, Any]],
    benchmark_curve: list[dict[str, Any]],
    trades: list[Trade],
    risk_free_rate: Decimal,
    benchmark_annual_return: Decimal,
    initial_capital: Decimal,
) -> dict[str, Any]:
    if not equity_curve:
        return {}

    final_equity = safe_decimal(equity_curve[-1]["equity_value"], initial_capital)
    benchmark_final = safe_decimal(benchmark_curve[-1]["equity_value"], initial_capital) if benchmark_curve else initial_capital
    days = max((equity_curve[-1]["curve_date"] - equity_curve[0]["curve_date"]).days + 1, 1)

    strategy_return_ratio = ZERO if initial_capital == ZERO else (final_equity - initial_capital) / initial_capital
    benchmark_return_ratio = ZERO if initial_capital == ZERO else (benchmark_final - initial_capital) / initial_capital
    excess_return_ratio = strategy_return_ratio - benchmark_return_ratio

    strategy_daily_returns = daily_returns_from_curve(equity_curve)
    benchmark_daily_returns = daily_returns_from_curve(benchmark_curve)
    if not benchmark_daily_returns and len(equity_curve) > 1:
        benchmark_daily = Decimal(str(float(ONE + benchmark_annual_return) ** (1 / 365) - 1))
        benchmark_daily_returns = [benchmark_daily for _ in range(len(equity_curve) - 1)]
    excess_daily_returns = [
        strategy_daily_returns[index] - benchmark_daily_returns[index]
        for index in range(min(len(strategy_daily_returns), len(benchmark_daily_returns)))
    ]

    strategy_vol_ratio = annualized_volatility(strategy_daily_returns)
    benchmark_vol_ratio = annualized_volatility(benchmark_daily_returns)
    sharpe = sharpe_ratio(strategy_daily_returns, risk_free_rate)
    sortino = sortino_ratio(strategy_daily_returns, risk_free_rate)

    max_drawdown_ratio, drawdown_period = max_drawdown_stats(equity_curve)
    excess_curve = build_excess_curve(equity_curve, benchmark_curve)
    excess_drawdown_ratio, _ = max_drawdown_stats(excess_curve)

    strategy_annualized_return_pct = annualize_return(strategy_return_ratio, days)
    benchmark_annualized_return_pct = annualize_return(benchmark_return_ratio, days)

    benchmark_var = population_std(benchmark_daily_returns) ** 2 if benchmark_daily_returns else ZERO
    if benchmark_var > EPSILON and strategy_daily_returns:
        avg_strategy = mean(strategy_daily_returns)
        avg_benchmark = mean(benchmark_daily_returns)
        covariance = sum(
            (
                (strategy_daily_returns[index] - avg_strategy)
                * (benchmark_daily_returns[index] - avg_benchmark)
                for index in range(min(len(strategy_daily_returns), len(benchmark_daily_returns)))
            ),
            start=ZERO,
        ) / Decimal(min(len(strategy_daily_returns), len(benchmark_daily_returns)))
        beta = covariance / benchmark_var
    else:
        beta = ZERO

    strategy_annualized_ratio = pct_to_ratio(strategy_annualized_return_pct)
    benchmark_annualized_ratio = pct_to_ratio(benchmark_annualized_return_pct)
    alpha = strategy_annualized_ratio - (risk_free_rate + beta * (benchmark_annualized_ratio - risk_free_rate))

    tracking_error = population_std(excess_daily_returns)
    information_ratio = ZERO if tracking_error <= EPSILON else mean(excess_daily_returns) / tracking_error * Decimal(str(math.sqrt(252)))
    excess_sharpe_ratio = None if tracking_error <= EPSILON else float(quantize_four(mean(excess_daily_returns) / tracking_error * Decimal(str(math.sqrt(252)))))

    profit_days = len([value for value in strategy_daily_returns if value > ZERO])
    loss_days = len([value for value in strategy_daily_returns if value < ZERO])
    daily_win_rate = Decimal(str(profit_days / len(strategy_daily_returns))) if strategy_daily_returns else ZERO

    winning_trades = [trade for trade in trades if (trade.realized_pnl or ZERO) > ZERO]
    losing_trades = [trade for trade in trades if (trade.realized_pnl or ZERO) < ZERO]
    avg_profit = sum(((trade.realized_pnl or ZERO) for trade in winning_trades), start=ZERO) / len(winning_trades) if winning_trades else ZERO
    avg_loss = abs(sum(((trade.realized_pnl or ZERO) for trade in losing_trades), start=ZERO) / len(losing_trades)) if losing_trades else ZERO
    trade_win_rate = Decimal(str(len(winning_trades) / len(trades))) if trades else ZERO
    profit_loss_ratio = avg_profit / avg_loss if avg_loss > ZERO else ZERO

    calmar_ratio = ZERO if max_drawdown_ratio == ZERO else strategy_annualized_ratio / max_drawdown_ratio
    avg_daily_excess_return_pct = quantize_money(ratio_to_pct(mean(excess_daily_returns))) if excess_daily_returns else ZERO

    metrics = {
        "total_return_pct": round(float(quantize_money(ratio_to_pct(strategy_return_ratio))), 4),
        "annualized_return_pct": round(float(strategy_annualized_return_pct), 4),
        "cumulative_profit": round(float(quantize_money(final_equity - initial_capital)), 4),
        "max_drawdown_pct": round(float(quantize_money(ratio_to_pct(max_drawdown_ratio))), 4),
        "volatility_pct": round(float(quantize_money(ratio_to_pct(strategy_vol_ratio))), 4),
        "downside_volatility_pct": round(float(quantize_money(ratio_to_pct(annualized_volatility([value for value in strategy_daily_returns if value < ZERO])))), 4),
        "sharpe_ratio": round(float(quantize_four(sharpe)), 4),
        "sortino_ratio": round(float(quantize_four(sortino)), 4),
        "calmar_ratio": round(float(quantize_four(calmar_ratio)), 4),
        "total_trades": len(trades),
        "win_rate_pct": round(float(quantize_money(ratio_to_pct(trade_win_rate))), 4),
        "profit_loss_ratio": round(float(quantize_four(profit_loss_ratio)), 4) if profit_loss_ratio != ZERO else 0.0,
        "total_commission": round(float(sum((trade.commission for trade in trades), start=ZERO)), 4),
        "strategy_return_pct": round(float(quantize_money(ratio_to_pct(strategy_return_ratio))), 4),
        "strategy_annualized_return_pct": round(float(strategy_annualized_return_pct), 4),
        "benchmark_return_pct": round(float(quantize_money(ratio_to_pct(benchmark_return_ratio))), 4),
        "benchmark_annualized_return_pct": round(float(benchmark_annualized_return_pct), 4),
        "excess_return_pct": round(float(quantize_money(ratio_to_pct(excess_return_ratio))), 4),
        "alpha": round(float(quantize_four(alpha)), 4),
        "beta": round(float(quantize_four(beta)), 4),
        "win_rate": round(float(quantize_four(trade_win_rate)), 4),
        "avg_daily_excess_return_pct": round(float(avg_daily_excess_return_pct), 4),
        "excess_return_max_drawdown_pct": round(float(quantize_money(ratio_to_pct(excess_drawdown_ratio))), 4),
        "excess_return_sharpe_ratio": excess_sharpe_ratio,
        "daily_win_rate": round(float(quantize_four(daily_win_rate)), 4),
        "profit_days": profit_days,
        "loss_days": loss_days,
        "profit_trade_count": len(winning_trades),
        "loss_trade_count": len(losing_trades),
        "information_ratio": round(float(quantize_four(information_ratio)), 4) if information_ratio != ZERO else 0.0,
        "strategy_volatility_pct": round(float(quantize_money(ratio_to_pct(strategy_vol_ratio))), 4),
        "benchmark_volatility_pct": round(float(quantize_money(ratio_to_pct(benchmark_vol_ratio))), 4),
        "max_drawdown_period": f"{drawdown_period[0]:%Y/%m/%d},{drawdown_period[1]:%Y/%m/%d}",
        "benchmark_annual_return_assumption": round(float(benchmark_annual_return), 6),
    }
    return metrics


