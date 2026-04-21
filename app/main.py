from __future__ import annotations

from pathlib import Path
from datetime import timedelta, UTC

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import ClosedPosition, Position, Strategy, StrategyStatus, Trade, TradeDirection, User, UserRole
from app.schemas import (
    ClosedPositionOut,
    PaginatedStrategies,
    PaginatedTrades,
    PositionManualAdjustment,
    PositionOut,
    PositionOverview,
    PositionPriceUpdate,
    StrategyCreate,
    StrategyDetail,
    StrategyOut,
    StrategyStatusUpdate,
    StrategyUpdate,
    TradeSignalCreate,
    TradeOut,
    TradeStats,
)
from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REMEMBER_ME_EXPIRE_DAYS,
    UserCreate,
    UserLogin,
    UserOut,
    UserUpdate,
    authenticate_user,
    create_access_token,
    get_admin_user,
    get_current_active_user,
    get_password_hash,
)
from app.services import (
    ZERO,
    apply_buy,
    apply_sell,
    build_strategy_dashboard,
    build_strategy_snapshot,
    export_trades_csv,
    paginate,
    position_overview,
    recalc_position,
    apply_position_manual_adjustment,
    serialize_strategy,
)

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="模拟交易系统", version="1.2.0", lifespan=lifespan)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8899", "http://127.0.0.1:8899"],  # 生产环境请限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全响应头中间件
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # 防止点击劫持
    response.headers["X-Frame-Options"] = "DENY"
    # 防止MIME类型嗅探
    response.headers["X-Content-Type-Options"] = "nosniff"
    # 启用浏览器XSS过滤
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # 内容安全策略（可根据需要调整）
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    # 推荐传输安全
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # 推荐器策略
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# ==================== Exception Handlers ====================

@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def forbidden_handler(request: Request, exc: HTTPException):
    """Handle 403 Forbidden errors with custom page."""
    if request.url.path.startswith("/api/"):
        return PlainTextResponse("需要管理员权限", status_code=403)
    return templates.TemplateResponse("403.html", {"request": request}, status_code=403)


@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_handler(request: Request, exc: HTTPException):
    """Handle 401 Unauthorized errors."""
    if request.url.path.startswith("/api/"):
        return PlainTextResponse("请先登录", status_code=401)
    # 对于页面请求的401，也返回403页面（避免重定向循环）
    return templates.TemplateResponse("403.html", {"request": request}, status_code=403)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/user-management", response_class=HTMLResponse)
def user_management_page(request: Request):
    return templates.TemplateResponse(request, "user_management.html")


@app.get("/strategies/{strategy_id}", response_class=HTMLResponse)
def strategy_detail_page(strategy_id: int, request: Request):
    return templates.TemplateResponse(request, "strategy_detail.html", {"strategy_id": strategy_id})


@app.get("/manual-order", response_class=HTMLResponse)
def manual_order_page(request: Request):
    """Manual order page (admin check done by frontend)."""
    return templates.TemplateResponse(request, "manual_order.html")


@app.get("/health")
def health():
    return {"status": "ok"}


# ==================== Authentication APIs ====================

@app.post("/api/auth/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """User login endpoint."""
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # Set token expiration based on remember_me
    if payload.remember_me:
        access_token_expires = timedelta(days=REMEMBER_ME_EXPIRE_DAYS)
    else:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": str(user.user_id)}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserOut.model_validate(user)
    }


@app.get("/api/auth/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return UserOut.model_validate(current_user)


@app.post("/api/auth/logout")
def logout():
    """Logout endpoint (client-side token removal)."""
    return {"message": "登出成功"}


@app.get("/api/users", response_model=list[UserOut])
def list_users(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    users = db.execute(select(User).order_by(User.created_at.desc())).scalars().all()
    return [UserOut.model_validate(u) for u in users]


@app.post("/api/users", response_model=UserOut)
def create_user(
    payload: UserCreate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    # Check if username already exists
    existing_user = db.execute(
        select(User).where(User.username == payload.username)
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # Check if email already exists
    if payload.email:
        existing_email = db.execute(
            select(User).where(User.email == payload.email)
        ).scalar_one_or_none()
        if existing_email:
            raise HTTPException(status_code=400, detail="邮箱已被使用")

    # Create new user
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@app.put("/api/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update a user (admin only)."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # Update fields
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@app.delete("/api/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)."""
    if user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    if user_id == 1:
        raise HTTPException(status_code=400, detail="不能删除系统管理员")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    db.delete(user)
    db.commit()
    return {"message": "用户删除成功"}


# ==================== Strategy APIs ====================


@app.get("/api/strategies", response_model=PaginatedStrategies)
def list_strategies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    status: StrategyStatus | None = Query(default=None),
    exclude_status: StrategyStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Strategy)
    count_query = select(func.count()).select_from(Strategy)
    if status is not None:
        query = query.where(Strategy.status == status)
        count_query = count_query.where(Strategy.status == status)
    if exclude_status is not None:
        query = query.where(Strategy.status != exclude_status)
        count_query = count_query.where(Strategy.status != exclude_status)

    total = db.scalar(count_query) or 0
    strategies = db.execute(paginate(query.order_by(desc(Strategy.updated_at)), page, page_size)).scalars().all()
    items = []
    for strategy in strategies:
        snapshot = build_strategy_snapshot(db, strategy)
        items.append(snapshot["strategy"])
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@app.post("/api/strategies", response_model=StrategyOut)
def create_strategy(payload: StrategyCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    strategy = Strategy(**payload.model_dump())
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return serialize_strategy(strategy)


@app.get("/api/strategies/{strategy_id}", response_model=StrategyOut)
def get_strategy(strategy_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    strategy = db.get(Strategy, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    snapshot = build_strategy_snapshot(db, strategy)
    return snapshot["strategy"]


@app.get("/api/strategies/{strategy_id}/dashboard", response_model=StrategyDetail)
def get_strategy_dashboard(strategy_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        return build_strategy_dashboard(db, strategy_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/api/strategies/{strategy_id}", response_model=StrategyOut)
def update_strategy(strategy_id: int, payload: StrategyUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    strategy = db.get(Strategy, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    if strategy.status == StrategyStatus.ARCHIVED:
        raise HTTPException(status_code=400, detail="归档策略只读")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(strategy, key, value)
    strategy.version += 1
    db.commit()
    db.refresh(strategy)
    snapshot = build_strategy_snapshot(db, strategy)
    return snapshot["strategy"]


@app.put("/api/strategies/{strategy_id}/status", response_model=StrategyOut)
def update_strategy_status(strategy_id: int, payload: StrategyStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    strategy = db.get(Strategy, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    strategy.status = payload.status
    db.commit()
    db.refresh(strategy)
    snapshot = build_strategy_snapshot(db, strategy)
    return snapshot["strategy"]


@app.post("/api/trades", response_model=TradeOut)
def create_trade_signal(payload: TradeSignalCreate, db: Session = Depends(get_db), current_user: User = Depends(get_admin_user)):
    try:
        if payload.direction == TradeDirection.BUY:
            return apply_buy(db, payload)
        if payload.direction == TradeDirection.SELL:
            return apply_sell(db, payload)
        raise ValueError("不支持的交易方向")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/trades/stats", response_model=TradeStats)
def trade_stats(strategy_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    query = select(Trade)
    if strategy_id is not None:
        query = query.where(Trade.strategy_id == strategy_id)
    trades = db.execute(query).scalars().all()
    by_symbol = grouped_trade_stats(trades, "symbol")
    by_strategy = grouped_trade_stats(trades, "strategy_id")
    return {
        "total_trades": len(trades),
        "total_amount": sum((trade.amount for trade in trades), start=ZERO),
        "total_commission": sum((trade.commission for trade in trades), start=ZERO),
        "total_realized_pnl": sum(((trade.realized_pnl or ZERO) for trade in trades), start=ZERO),
        "by_symbol": by_symbol,
        "by_strategy": by_strategy,
    }


@app.get("/api/trades", response_model=PaginatedTrades)
def list_trades(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    symbol: str | None = None,
    strategy_id: int | None = None,
    direction: str | None = None,
    export: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Trade)
    if symbol:
        query = query.where(Trade.symbol == symbol.upper())
    if strategy_id is not None:
        query = query.where(Trade.strategy_id == strategy_id)
    if direction:
        query = query.where(Trade.direction == direction)
    query = query.order_by(desc(Trade.trade_time))
    trades = db.execute(query).scalars().all()
    if export == "csv":
        return PlainTextResponse(export_trades_csv(trades), media_type="text/csv")
    total = len(trades)
    start = (page - 1) * page_size
    items = trades[start : start + page_size]
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@app.get("/api/trades/{trade_id}", response_model=TradeOut)
def get_trade(trade_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    trade = db.get(Trade, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="成交记录不存在")
    return trade


def grouped_trade_stats(trades: list[Trade], attr: str) -> list[dict]:
    grouped: dict[str, dict] = {}
    for trade in trades:
        key = str(getattr(trade, attr))
        item = grouped.setdefault(key, {"key": key, "count": 0, "amount": 0.0, "realized_pnl": 0.0})
        item["count"] += 1
        item["amount"] += float(trade.amount)
        item["realized_pnl"] += float(trade.realized_pnl or 0)
    return list(grouped.values())


@app.get("/api/positions/overview", response_model=PositionOverview)
def get_positions_overview(strategy_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return position_overview(db, strategy_id=strategy_id)


@app.get("/api/positions", response_model=list[PositionOut])
def list_positions(strategy_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    query = select(Position)
    if strategy_id is not None:
        query = query.where(Position.strategy_id == strategy_id)
    query = query.order_by(desc(Position.updated_at))
    return db.execute(query).scalars().all()


@app.put("/api/positions/update-prices", response_model=list[PositionOut])
def update_position_prices(payload: PositionPriceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    updated = []
    for item in payload.items:
        query = select(Position).where(
            Position.symbol == item.symbol.upper(),
            Position.strategy_id == item.strategy_id,
        )
        positions = db.execute(query).scalars().all()
        for position in positions:
            position.current_price = item.current_price
            recalc_position(position)
            updated.append(position)
    db.commit()
    return updated


@app.put("/api/positions/manual-adjustments", response_model=list[PositionOut])
def manual_adjust_positions(payload: PositionManualAdjustment, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    updated = []
    for item in payload.items:
        query = select(Position).where(
            Position.symbol == item.symbol.upper(),
            Position.strategy_id == item.strategy_id,
        )
        positions = db.execute(query).scalars().all()
        if not positions:
            raise HTTPException(status_code=404, detail=f"?????: {item.symbol.upper()}")
        for position in positions:
            try:
                apply_position_manual_adjustment(position, quantity=item.quantity, market_value=item.market_value)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            updated.append(position)
    db.commit()
    return updated


@app.get("/api/positions/history", response_model=list[ClosedPositionOut])
def list_closed_positions(strategy_id: int | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    query = select(ClosedPosition)
    if strategy_id is not None:
        query = query.where(ClosedPosition.strategy_id == strategy_id)
    query = query.order_by(desc(ClosedPosition.close_time))
    return db.execute(query).scalars().all()


@app.get("/api/positions/{position_id}", response_model=PositionOut)
def get_position(position_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="持仓不存在")
    return position
