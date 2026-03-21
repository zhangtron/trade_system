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

function formatRatio(value) {
  if (value === null || value === undefined || value === "") return "--";
  return Number(value).toFixed(3);
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

function renderEmptyRow(tbodyId, columns, text) {
  const tbody = document.getElementById(tbodyId);
  tbody.innerHTML = `<tr><td colspan="${columns}" class="empty-state">${text}</td></tr>`;
}

function renderCurve(points) {
  const container = document.getElementById("curveChart");
  if (!points.length) {
    container.innerHTML = '<div class="empty-state">暂无收益曲线数据</div>';
    return;
  }

  const width = 900;
  const height = 300;
  const padding = 28;
  const values = points.map((point) => Number(point.equity_value));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = points.length > 1 ? (width - padding * 2) / (points.length - 1) : 0;

  const plotted = points.map((point, index) => {
    const x = points.length === 1 ? width / 2 : padding + step * index;
    const y = height - padding - ((Number(point.equity_value) - min) / range) * (height - padding * 2);
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
    .map(
      (point) => `
        <circle cx="${point.x}" cy="${point.y}" r="4.5" class="curve-point"></circle>
      `,
    )
    .join("");
  const latest = plotted[plotted.length - 1];

  container.innerHTML = `
    <div class="curve-meta">
      <span>起点：${points[0].curve_date}</span>
      <span>终点：${points[points.length - 1].curve_date}</span>
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

function renderSummaryMetrics(metrics) {
  const container = document.getElementById("detailMetrics");
  const items = [
    ["累计收益", formatPercent(metrics.cumulative_return_pct), metricClass(metrics.cumulative_return_pct)],
    ["年化收益", formatPercent(metrics.annualized_return_pct), metricClass(metrics.annualized_return_pct)],
    ["今日收益", formatPercent(metrics.today_return_pct), metricClass(metrics.today_return_pct)],
    ["最大回撤", formatPercent(metrics.max_drawdown_pct), metricClass(metrics.max_drawdown_pct, true)],
    ["累计盈亏", formatNumber(metrics.cumulative_profit), metricClass(metrics.cumulative_profit)],
    ["当前持仓数", String(metrics.current_positions_count), "metric-flat"],
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

function renderEvaluationMetrics(metrics) {
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

function fillCurrentPositions(positions) {
  if (!positions.length) {
    renderEmptyRow("currentPositionsBody", 6, "当前没有持仓");
    return;
  }
  document.getElementById("currentPositionsBody").innerHTML = positions
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
}

function fillRecentTrades(trades) {
  if (!trades.length) {
    renderEmptyRow("recentTradesBody", 6, "暂无成交记录");
    return;
  }
  document.getElementById("recentTradesBody").innerHTML = trades
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
}

function fillPositionHistory(history) {
  if (!history.length) {
    renderEmptyRow("positionHistoryBody", 8, "暂无历史持仓变化");
    return;
  }
  document.getElementById("positionHistoryBody").innerHTML = history
    .map(
      (item) => `
        <tr>
          <td>${formatDate(item.trade_time)}</td>
          <td>${item.symbol}</td>
          <td>${item.direction}</td>
          <td class="${metricClass(item.quantity_change)}">${formatNumber(item.quantity_change, 6)}</td>
          <td>${formatNumber(item.position_quantity, 6)}</td>
          <td>${formatNumber(item.avg_cost, 6)}</td>
          <td>${formatNumber(item.market_price, 6)}</td>
          <td class="${metricClass(item.unrealized_pnl)}">${formatNumber(item.unrealized_pnl)}</td>
        </tr>
      `,
    )
    .join("");
}

async function loadDashboard() {
  const strategyId = document.body.dataset.strategyId;
  const data = await fetchJson(`/api/strategies/${strategyId}/dashboard`);
  document.getElementById("detailTitle").textContent = data.strategy.name;
  document.getElementById("detailDesc").textContent = data.strategy.description || "暂无策略描述";
  document.getElementById("detailStatus").textContent = statusLabel(data.strategy.status);
  document.getElementById("detailType").textContent = data.strategy.type;
  document.getElementById("detailVersion").textContent = `v${data.strategy.version}`;
  renderSummaryMetrics({ ...data.strategy, current_positions_count: data.current_positions.length });
  renderEvaluationMetrics(data.evaluation_metrics || {});
  renderCurve(data.equity_curve);
  fillCurrentPositions(data.current_positions);
  fillRecentTrades(data.recent_trades);
  fillPositionHistory(data.position_history);
}

loadDashboard().catch((error) => {
  console.error(error);
  alert(error.message);
});
