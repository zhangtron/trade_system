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
  if (value === null || value === undefined || value === "") {
    return "--";
  }
  return Number(value).toFixed(digits);
}

function formatPercent(value) {
  if (value === null || value === undefined) {
    return "--";
  }
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

function renderEmptyRow(columns, text) {
  return `<tr><td colspan="${columns}" class="empty-state">${text}</td></tr>`;
}

function renderActions(item) {
  return `
    <div class="row-actions">
      <a class="mini-link" href="/strategies/${item.strategy_id}">详情</a>
      <button class="ghost-btn ${item.status === "draft" ? "is-selected" : ""}" data-id="${item.strategy_id}" data-status="draft">草稿</button>
      <button class="ghost-btn ${item.status === "active" ? "is-selected" : ""}" data-id="${item.strategy_id}" data-status="active">激活</button>
      <button class="ghost-btn ${item.status === "archived" ? "is-selected" : ""}" data-id="${item.strategy_id}" data-status="archived">归档</button>
    </div>
  `;
}

function renderStrategyRows(items, { archived = false } = {}) {
  if (!items.length) {
    return renderEmptyRow(archived ? 10 : 11, archived ? "暂无归档策略" : "当前没有需要关注的策略");
  }

  return items
    .map((item) => {
      if (archived) {
        return `
          <tr>
            <td>
              <a class="name-link" href="/strategies/${item.strategy_id}">${item.name}</a>
              <div class="table-subtext">ID #${item.strategy_id}</div>
            </td>
            <td>${item.type}</td>
            <td><span class="status-chip status-${item.status}">${statusLabel(item.status)}</span></td>
            <td class="${metricClass(item.cumulative_return_pct)}">${formatPercent(item.cumulative_return_pct)}</td>
            <td class="${metricClass(item.annualized_return_pct)}">${formatPercent(item.annualized_return_pct)}</td>
            <td class="${metricClass(item.max_drawdown_pct, true)}">${formatPercent(item.max_drawdown_pct)}</td>
            <td class="${metricClass(item.cumulative_profit)}">${formatNumber(item.cumulative_profit)}</td>
            <td><span class="version-badge">v${item.version}</span></td>
            <td>${formatDate(item.created_at)}</td>
            <td>${renderActions(item)}</td>
          </tr>
        `;
      }

      return `
        <tr>
          <td>
            <a class="name-link" href="/strategies/${item.strategy_id}">${item.name}</a>
            <div class="table-subtext">ID #${item.strategy_id}</div>
          </td>
          <td>${item.type}</td>
          <td><span class="status-chip status-${item.status}">${statusLabel(item.status)}</span></td>
          <td class="${metricClass(item.cumulative_return_pct)}">${formatPercent(item.cumulative_return_pct)}</td>
          <td class="${metricClass(item.annualized_return_pct)}">${formatPercent(item.annualized_return_pct)}</td>
          <td class="${metricClass(item.today_return_pct)}">${formatPercent(item.today_return_pct)}</td>
          <td class="${metricClass(item.max_drawdown_pct, true)}">${formatPercent(item.max_drawdown_pct)}</td>
          <td class="${metricClass(item.cumulative_profit)}">${formatNumber(item.cumulative_profit)}</td>
          <td><span class="version-badge">v${item.version}</span></td>
          <td>${formatDate(item.created_at)}</td>
          <td>${renderActions(item)}</td>
        </tr>
      `;
    })
    .join("");
}

function bindStatusButtons() {
  document.querySelectorAll("button[data-id][data-status]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await fetchJson(`/api/strategies/${button.dataset.id}/status`, {
          method: "PUT",
          body: JSON.stringify({ status: button.dataset.status }),
        });
        await Promise.all([loadStrategies(), refreshOverview()]);
      } catch (error) {
        alert(error.message);
      }
    });
  });
}

async function refreshOverview() {
  const overview = await fetchJson("/api/positions/overview");
  document.getElementById("marketValue").textContent = formatNumber(overview.total_market_value);
  document.getElementById("floatingPnl").textContent = formatNumber(overview.total_unrealized_pnl);
}

async function loadStrategies() {
  const [mainPage, archivedPage] = await Promise.all([
    fetchJson("/api/strategies?page=1&page_size=100&exclude_status=archived"),
    fetchJson("/api/strategies?page=1&page_size=100&status=archived"),
  ]);

  document.getElementById("totalStrategies").textContent = mainPage.total;
  document.getElementById("archivedCount").textContent = archivedPage.total;
  document.getElementById("strategyTableBody").innerHTML = renderStrategyRows(mainPage.items);
  document.getElementById("archivedStrategyTableBody").innerHTML = renderStrategyRows(archivedPage.items, { archived: true });
  bindStatusButtons();
}

function bindArchiveToggle() {
  const archivePanel = document.getElementById("archivePanel");
  const archiveToggle = document.getElementById("archiveToggle");
  if (!archivePanel || !archiveToggle) {
    return;
  }

  const syncLabel = () => {
    archiveToggle.textContent = archivePanel.classList.contains("is-collapsed") ? "展开归档策略" : "收起归档策略";
  };

  archiveToggle.addEventListener("click", () => {
    archivePanel.classList.toggle("is-collapsed");
    syncLabel();
  });

  syncLabel();
}

document.getElementById("strategyForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const formData = new FormData(form);
  let parameters = null;
  const rawParameters = formData.get("parameters");
  if (rawParameters) {
    try {
      parameters = JSON.parse(rawParameters);
    } catch {
      alert("参数 JSON 格式不正确");
      return;
    }
  }
  try {
    await fetchJson("/api/strategies", {
      method: "POST",
      body: JSON.stringify({
        name: formData.get("name"),
        type: formData.get("type"),
        status: formData.get("status"),
        description: formData.get("description") || null,
        parameters,
      }),
    });
    form.reset();
    await Promise.all([loadStrategies(), refreshOverview()]);
  } catch (error) {
    alert(error.message);
  }
});

bindArchiveToggle();
Promise.all([loadStrategies(), refreshOverview()]).catch((error) => {
  console.error(error);
  alert(error.message);
});
