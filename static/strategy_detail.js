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

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function toNumber(value, fallback = 0) {
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
}

function formatDate(value) {
  if (!value) return "--";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "--";
  return d.toLocaleString("zh-CN", { hour12: false });
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "--";
  const num = Number(value);
  return Number.isFinite(num) ? num.toFixed(digits) : "--";
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "--";
  const num = Number(value);
  return Number.isFinite(num) ? `${num.toFixed(2)}%` : "--";
}

function formatRatio(value) {
  if (value === null || value === undefined || value === "") return "--";
  const num = Number(value);
  return Number.isFinite(num) ? num.toFixed(3) : "--";
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
  }[status] || status || "--";
}

function renderEmptyRow(tbodyId, columns, text) {
  const tbody = document.getElementById(tbodyId);
  tbody.innerHTML = `<tr><td colspan="${columns}" class="empty-state">${text}</td></tr>`;
}

function renderCurve(pointsRaw) {
  const points = asArray(pointsRaw);
  const container = document.getElementById("curveChart");
  if (!points.length) {
    container.innerHTML = '<div class="empty-state">暂无收益曲线数据</div>';
    return;
  }

  const width = 900;
  const height = 300;
  const padding = 28;
  const values = points.map((point) => toNumber(point.equity_value));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = points.length > 1 ? (width - padding * 2) / (points.length - 1) : 0;

  const plotted = points.map((point, index) => {
    const x = points.length === 1 ? width / 2 : padding + step * index;
    const y = height - padding - ((toNumber(point.equity_value) - min) / range) * (height - padding * 2);
    return { x, y, value: point.equity_value, date: point.curve_date };
  });

  const polyline = plotted.map((point) => `${point.x},${point.y}`).join(" ");
  const areaPath = [
    `M ${plotted[0].x} ${height - padding}`,
    ...plotted.map((point) => `L ${point.x} ${point.y}`),
    `L ${plotted[plotted.length - 1].x} ${height - padding}`,
    "Z",
  ].join(" ");
  const dots = plotted
    .map((point) => `<circle cx="${point.x}" cy="${point.y}" r="4.5" class="curve-point"></circle>`)
    .join("");
  const latest = plotted[plotted.length - 1];

  container.innerHTML = `
    <div class="curve-meta">
      <span>起点：${points[0].curve_date || "--"}</span>
      <span>终点：${points[points.length - 1].curve_date || "--"}</span>
      <span>最新净值：${formatNumber(latest.value)}</span>
    </div>
    <svg viewBox="0 0 ${width} ${height}" class="curve-svg" preserveAspectRatio="none">
      <defs>
        <linearGradient id="curveFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="rgba(255, 157, 97, 0.42)"></stop>
          <stop offset="100%" stop-color="rgba(255, 157, 97, 0.02)"></stop>
        </linearGradient>
      </defs>
      <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" class="grid-line"></line>
      <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" class="grid-line"></line>
      <path d="${areaPath}" class="curve-area"></path>
      <polyline points="${polyline}" class="curve-line"></polyline>
      ${dots}
    </svg>
    <div class="curve-meta">
      <span>最高：${formatNumber(max)}</span>
      <span>最低：${formatNumber(min)}</span>
      <span>区间振幅：${formatNumber(max - min)}</span>
    </div>
  `;
}

function renderSummaryMetrics(summary) {
  const container = document.getElementById("detailMetrics");
  if (!container) return;
  const items = [
    ["累计收益", formatPercent(summary.cumulative_return_pct), metricClass(summary.cumulative_return_pct)],
    ["年化收益", formatPercent(summary.annualized_return_pct), metricClass(summary.annualized_return_pct)],
    ["今日收益", formatPercent(summary.today_return_pct), metricClass(summary.today_return_pct)],
    ["最大回撤", formatPercent(summary.max_drawdown_pct), metricClass(summary.max_drawdown_pct, true)],
    ["持仓股票数量", String(summary.position_symbols_count), "metric-flat"],
    ["持仓金额", formatNumber(summary.total_market_value), metricClass(summary.total_market_value)],
    ["累计盈利金额", formatNumber(summary.cumulative_profit), metricClass(summary.cumulative_profit)],
  ];
  container.innerHTML = items
    .map(
      ([label, value, cls]) => `
        <div class="metric-tile">
          <span>${label}</span>
          <strong class="${cls}">${value}</strong>
        </div>
      `,
    )
    .join("");
}

function renderEvaluationMetrics(metricsRaw) {
  const metrics = metricsRaw || {};
  const container = document.getElementById("detailEvaluationMetrics");
  const items = [
    ["策略收益", formatPercent(metrics.strategy_return_pct), metricClass(metrics.strategy_return_pct)],
    ["策略年化收益", formatPercent(metrics.strategy_annualized_return_pct), metricClass(metrics.strategy_annualized_return_pct)],
    ["基准收益", formatPercent(metrics.benchmark_return_pct), metricClass(metrics.benchmark_return_pct)],
    ["超额收益", formatPercent(metrics.excess_return_pct), metricClass(metrics.excess_return_pct)],
    ["阿尔法", formatRatio(metrics.alpha), metricClass(metrics.alpha)],
    ["贝塔", formatRatio(metrics.beta), metricClass(metrics.beta)],
    ["夏普比率", formatRatio(metrics.sharpe_ratio), metricClass(metrics.sharpe_ratio)],
    ["索提诺比率", formatRatio(metrics.sortino_ratio), metricClass(metrics.sortino_ratio)],
    ["信息比率", formatRatio(metrics.information_ratio), metricClass(metrics.information_ratio)],
    ["胜率", formatRatio(metrics.win_rate), metricClass(metrics.win_rate)],
    ["盈亏比", formatRatio(metrics.profit_loss_ratio), metricClass(metrics.profit_loss_ratio)],
    ["日胜率", formatRatio(metrics.daily_win_rate), metricClass(metrics.daily_win_rate)],
    ["盈利次数", formatNumber(metrics.profit_trade_count, 0), "metric-flat"],
    ["亏损次数", formatNumber(metrics.loss_trade_count, 0), "metric-flat"],
    ["策略波动率", formatPercent(metrics.strategy_volatility_pct), metricClass(metrics.strategy_volatility_pct, true)],
    ["基准波动率", formatPercent(metrics.benchmark_volatility_pct), metricClass(metrics.benchmark_volatility_pct, true)],
    ["日均超额收益", formatPercent(metrics.avg_daily_excess_return_pct), metricClass(metrics.avg_daily_excess_return_pct)],
    ["超额收益最大回撤", formatPercent(metrics.excess_return_max_drawdown_pct), metricClass(metrics.excess_return_max_drawdown_pct, true)],
    ["超额收益夏普比率", formatRatio(metrics.excess_return_sharpe_ratio), metricClass(metrics.excess_return_sharpe_ratio)],
    ["最大回撤区间", metrics.max_drawdown_period || "--", "metric-flat metric-text"],
  ];
  container.innerHTML = items
    .map(
      ([label, value, cls]) => `
        <div class="metric-tile">
          <span>${label}</span>
          <strong class="${cls}">${value}</strong>
        </div>
      `,
    )
    .join("");
}

function fillCurrentPositions(positionsRaw) {
  const positions = asArray(positionsRaw);
  if (!positions.length) {
    renderEmptyRow("currentPositionsBody", 7, "当前没有持仓");
    return;
  }

  document.getElementById("currentPositionsBody").innerHTML = positions
    .map(
      (item, index) => `
        <tr>
          <td>${index + 1}</td>
          <td>${item.symbol || "--"}</td>
          <td>${formatNumber(item.quantity, 6)}</td>
          <td>${formatNumber(item.avg_cost, 6)}</td>
          <td>${formatNumber(item.current_price, 6)}</td>
          <td>${formatNumber(item.market_value)}</td>
          <td class="${metricClass(item.unrealized_pnl)}">${formatNumber(item.unrealized_pnl)}</td>
        </tr>
      `,
    )
    .join("");
}

function fillRecentTrades(tradesRaw) {
  const trades = asArray(tradesRaw);
  if (!trades.length) {
    renderEmptyRow("recentTradesBody", 6, "暂无成交记录");
    return;
  }

  document.getElementById("recentTradesBody").innerHTML = trades
    .map(
      (item) => `
        <tr>
          <td>${formatDate(item.trade_time)}</td>
          <td>${item.symbol || "--"}</td>
          <td>${item.direction || "--"}</td>
          <td>${formatNumber(item.quantity, 6)}</td>
          <td>${formatNumber(item.price, 6)}</td>
          <td class="${metricClass(item.realized_pnl)}">${formatNumber(item.realized_pnl)}</td>
        </tr>
      `,
    )
    .join("");
}

function fillPositionHistory(historyRaw) {
  const history = asArray(historyRaw);
  if (!history.length) {
    renderEmptyRow("positionHistoryBody", 8, "暂无已平仓历史");
    return;
  }

  document.getElementById("positionHistoryBody").innerHTML = history
    .map(
      (item) => `
        <tr>
          <td>${formatDate(item.close_time)}</td>
          <td>${item.symbol || "--"}</td>
          <td>${formatDate(item.open_time)}</td>
          <td>${formatNumber(item.entry_quantity, 6)}</td>
          <td>${formatNumber(item.avg_cost, 6)}</td>
          <td>${formatNumber(item.close_price, 6)}</td>
          <td>${formatNumber(item.total_commission, 4)}</td>
          <td class="${metricClass(item.realized_pnl)}">${formatNumber(item.realized_pnl)}</td>
        </tr>
      `,
    )
    .join("");
}

function buildPositionSummary(strategy, currentPositionsRaw) {
  const currentPositions = asArray(currentPositionsRaw);
  const positionSymbolsCount = currentPositions.length;
  const totalMarketValue = currentPositions.reduce((acc, item) => acc + toNumber(item.market_value), 0);
  const cumulativeProfit = toNumber(strategy && strategy.cumulative_profit);
  return {
    cumulative_return_pct: strategy ? strategy.cumulative_return_pct : null,
    annualized_return_pct: strategy ? strategy.annualized_return_pct : null,
    today_return_pct: strategy ? strategy.today_return_pct : null,
    max_drawdown_pct: strategy ? strategy.max_drawdown_pct : null,
    cumulative_profit: cumulativeProfit,
    position_symbols_count: positionSymbolsCount,
    total_market_value: totalMarketValue,
  };
}

function fillHeaderStats(summary) {
  document.getElementById("detailPositionSymbols").textContent = String(summary.position_symbols_count || 0);
  document.getElementById("detailPositionMarketValue").textContent = formatNumber(summary.total_market_value);
  document.getElementById("detailCumulativeProfit").textContent = formatNumber(summary.cumulative_profit);
}

function setTextIfExists(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

async function loadDashboard() {
  const strategyId = document.body.dataset.strategyId;
  const data = (await fetchJson(`/api/strategies/${strategyId}/dashboard`)) || {};

  const strategy = data.strategy || {};
  const currentPositions = asArray(data.current_positions);
  const recentTrades = asArray(data.recent_trades);
  const closedPositions = asArray(data.closed_positions);
  const equityCurve = asArray(data.equity_curve);

  setTextIfExists("detailTitle", strategy.name || "策略详情");
  setTextIfExists("detailDesc", strategy.description || "暂无策略描述");

  const typeText = strategy.type ? `${strategy.type} · ${statusLabel(strategy.status)}` : statusLabel(strategy.status);
  const versionText = strategy.version !== undefined && strategy.version !== null ? `v${strategy.version}` : "--";
  setTextIfExists("detailType", typeText);
  setTextIfExists("detailVersion", versionText);
  setTextIfExists("detailStatus", statusLabel(strategy.status));

  const summary = buildPositionSummary(strategy, currentPositions);
  fillHeaderStats(summary);
  renderSummaryMetrics(summary);
  renderEvaluationMetrics(data.evaluation_metrics || {});
  renderCurve(equityCurve);
  fillCurrentPositions(currentPositions);
  fillRecentTrades(recentTrades);
  fillPositionHistory(closedPositions);
}

loadDashboard().catch((error) => {
  console.error(error);
  alert(error.message || "加载失败");
});
