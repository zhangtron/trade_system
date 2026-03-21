async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: "请求失败" }));
    throw new Error(data.detail || "请求失败");
  }
  return response.json();
}

function formatDate(value) {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "--";
  return Number(value).toFixed(digits);
}

function formatPercent(value) {
  if (value === null || value === undefined) return "--";
  return `${Number(value).toFixed(2)}%`;
}

function metricClass(value, inverse = false) {
  const num = Number(value || 0);
  if (num === 0 || Number.isNaN(num)) return "metric-flat";
  const positive = inverse ? num < 0 : num > 0;
  return positive ? "metric-positive" : "metric-negative";
}

function statusLabel(status) {
  return {
    draft: "草稿",
    active: "激活",
    archived: "归档",
  }[status] || status;
}

function fillRows(tbodyId, columns, rowsHtml, emptyText) {
  document.getElementById(tbodyId).innerHTML = rowsHtml || `<tr><td colspan="${columns}" class="empty-state">${emptyText}</td></tr>`;
}

function renderStrategyMetrics(strategy) {
  const container = document.getElementById("testerStrategyMetrics");
  container.innerHTML = [
    ["累计收益", formatPercent(strategy.cumulative_return_pct), metricClass(strategy.cumulative_return_pct)],
    ["年化收益", formatPercent(strategy.annualized_return_pct), metricClass(strategy.annualized_return_pct)],
    ["今日收益", formatPercent(strategy.today_return_pct), metricClass(strategy.today_return_pct)],
    ["最大回撤", formatPercent(strategy.max_drawdown_pct), metricClass(strategy.max_drawdown_pct, true)],
  ]
    .map(
      ([label, value, cls]) => `
        <div class="metric-tile compact-tile">
          <span>${label}</span>
          <strong class="${cls}">${value}</strong>
        </div>
      `,
    )
    .join("");
}

function renderPositions(positions) {
  const rows = positions
    .map(
      (item) => `
        <tr>
          <td>${item.symbol}</td>
          <td>${formatNumber(item.quantity, 6)}</td>
          <td>${formatNumber(item.avg_cost, 6)}</td>
          <td>${formatNumber(item.current_price, 6)}</td>
          <td>${formatNumber(item.market_value)}</td>
          <td class="${metricClass(item.unrealized_pnl)}">${formatNumber(item.unrealized_pnl)}</td>
        </tr>
      `,
    )
    .join("");
  fillRows("testerPositionsBody", 6, rows, "当前策略暂无持仓");
}

function renderTrades(trades) {
  const rows = trades
    .map(
      (item) => `
        <tr>
          <td>${formatDate(item.trade_time)}</td>
          <td>${item.symbol}</td>
          <td>${item.direction}</td>
          <td>${formatNumber(item.quantity, 6)}</td>
          <td>${formatNumber(item.price, 6)}</td>
          <td class="${metricClass(item.realized_pnl)}">${formatNumber(item.realized_pnl)}</td>
        </tr>
      `,
    )
    .join("");
  fillRows("testerTradesBody", 6, rows, "当前策略暂无成交记录");
}

function requireStrategyAndSymbol() {
  const strategyId = document.getElementById("strategySelect").value;
  if (!strategyId) {
    throw new Error("请先选择策略");
  }
  const symbol = document.getElementById("priceSymbolInput").value.trim();
  if (!symbol) {
    throw new Error("请先输入标的代码");
  }
  return { strategyId: Number(strategyId), symbol };
}

async function loadStrategies() {
  const data = await fetchJson("/api/strategies?page=1&page_size=100");
  const select = document.getElementById("strategySelect");
  select.innerHTML = "";
  if (!data.items.length) {
    select.innerHTML = '<option value="">暂无策略</option>';
    return;
  }
  data.items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.strategy_id;
    option.textContent = `${item.name}（${statusLabel(item.status)}）`;
    select.appendChild(option);
  });
  const active = data.items.find((item) => item.status === "active");
  if (active) {
    select.value = active.strategy_id;
  }
}

async function refreshTester() {
  const strategyId = document.getElementById("strategySelect").value;
  if (!strategyId) return;
  const [dashboard, stats, overview, trades] = await Promise.all([
    fetchJson(`/api/strategies/${strategyId}/dashboard`),
    fetchJson(`/api/trades/stats?strategy_id=${strategyId}`),
    fetchJson(`/api/positions/overview?strategy_id=${strategyId}`),
    fetchJson(`/api/trades?strategy_id=${strategyId}&page=1&page_size=15`),
  ]);
  document.getElementById("testerTotalTrades").textContent = stats.total_trades;
  document.getElementById("testerRealizedPnl").textContent = formatNumber(stats.total_realized_pnl);
  document.getElementById("testerFloatingPnl").textContent = formatNumber(overview.total_unrealized_pnl);
  renderStrategyMetrics(dashboard.strategy);
  renderPositions(dashboard.current_positions);
  renderTrades(trades.items);
}

async function submitTrade(direction) {
  const strategyId = document.getElementById("strategySelect").value;
  if (!strategyId) {
    alert("请先创建或选择策略");
    return;
  }
  const payload = {
    strategy_id: Number(strategyId),
    symbol: document.getElementById("symbolInput").value.trim(),
    quantity: Number(document.getElementById("quantityInput").value),
    price: Number(document.getElementById("priceInput").value),
    commission: Number(document.getElementById("commissionInput").value || 0),
    remark: document.getElementById("remarkInput").value.trim() || null,
  };
  try {
    await fetchJson(`/api/trades/${direction}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await refreshTester();
  } catch (error) {
    alert(error.message);
  }
}

async function updateCurrentPrice(event) {
  event.preventDefault();
  try {
    const { strategyId, symbol } = requireStrategyAndSymbol();
    const currentPrice = Number(document.getElementById("currentPriceInput").value);
    if (!Number.isFinite(currentPrice) || currentPrice <= 0) {
      throw new Error("请输入大于 0 的最新价格");
    }
    await fetchJson("/api/positions/update-prices", {
      method: "PUT",
      body: JSON.stringify({
        items: [{ strategy_id: strategyId, symbol, current_price: currentPrice }],
      }),
    });
    await refreshTester();
  } catch (error) {
    alert(error.message);
  }
}

async function updateManualField(field) {
  try {
    const { strategyId, symbol } = requireStrategyAndSymbol();
    const payload = { strategy_id: strategyId, symbol };

    if (field === "quantity") {
      const quantity = Number(document.getElementById("positionQuantityInput").value);
      if (!Number.isFinite(quantity) || quantity <= 0) {
        throw new Error("请输入大于 0 的持仓数量");
      }
      payload.quantity = quantity;
    }

    if (field === "market_value") {
      const marketValue = Number(document.getElementById("positionMarketValueInput").value);
      if (!Number.isFinite(marketValue) || marketValue < 0) {
        throw new Error("请输入大于等于 0 的持仓市值");
      }
      payload.market_value = marketValue;
    }

    await fetchJson("/api/positions/manual-adjustments", {
      method: "PUT",
      body: JSON.stringify({ items: [payload] }),
    });
    await refreshTester();
  } catch (error) {
    alert(error.message);
  }
}

document.getElementById("buyButton").addEventListener("click", () => submitTrade("buy"));
document.getElementById("sellButton").addEventListener("click", () => submitTrade("sell"));
document.getElementById("priceForm").addEventListener("submit", updateCurrentPrice);
document.getElementById("updateQuantityButton").addEventListener("click", () => updateManualField("quantity"));
document.getElementById("updateMarketValueButton").addEventListener("click", () => updateManualField("market_value"));
document.getElementById("strategySelect").addEventListener("change", refreshTester);

Promise.resolve()
  .then(loadStrategies)
  .then(refreshTester)
  .catch((error) => {
    console.error(error);
    alert(error.message);
  });
