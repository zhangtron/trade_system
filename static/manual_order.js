async function fetchJson(url, options = {}) {
  const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  const headers = { "Content-Type": "application/json" };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, { headers, ...options });

  if (response.status === 401) {
    clearAuthAndRedirect();
    throw new Error('请先登录');
  }

  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: "请求失败" }));
    throw new Error(data.detail || "请求失败");
  }
  return response.json();
}

// Authentication functions
function showLoginModal() {
  const loginModal = document.getElementById('loginModal');
  if (loginModal) {
    loginModal.classList.add('active');
  }
}

function hideLoginModal() {
  const loginModal = document.getElementById('loginModal');
  if (loginModal) {
    loginModal.classList.remove('active');
  }
}

function clearAuthAndRedirect() {
  localStorage.removeItem('auth_token');
  sessionStorage.removeItem('auth_token');
  localStorage.removeItem('user_info');
  sessionStorage.removeItem('user_info');
  // 显示登录模态框而不是重定向
  showLoginModal();
}

async function checkAuthStatus() {
  const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
  if (!token) {
    clearAuthAndRedirect();
    return false;
  }

  try {
    const response = await fetch('/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      clearAuthAndRedirect();
      return false;
    }

    return true;
  } catch (error) {
    clearAuthAndRedirect();
    return false;
  }
}

function updateUserInfo() {
  const userInfo = localStorage.getItem('user_info') || sessionStorage.getItem('user_info');
  const userNav = document.getElementById('userNav');

  if (!userInfo) {
    clearAuthAndRedirect();
    return;
  }

  try {
    const user = JSON.parse(userInfo);
    if (userNav) {
      const roleLabel = user.role === 'admin' ? '管理员' : '用户';
      const userManagementLink = user.role === 'admin' ?
        '<a href="/user-management">用户管理</a>' : '';
      const manualOrderLink = user.role === 'admin' ?
        '<a href="/manual-order">手动下单</a>' : '';
      userNav.innerHTML = `
        ${manualOrderLink}
        ${userManagementLink}
        <div class="user-info">
          <span class="user-name">${user.full_name || user.username}</span>
          <span class="user-role ${user.role}">${roleLabel}</span>
        </div>
        <button class="btn-logout" onclick="logout()">登出</button>
      `;
    }
  } catch (error) {
    console.error('Failed to parse user info:', error);
    clearAuthAndRedirect();
  }
}

function logout() {
  if (confirm('确定要登出吗？')) {
    clearAuthAndRedirect();
  }
}

// Login form handler
function handleLogin(event) {
  event.preventDefault();

  const usernameInput = document.getElementById('username');
  const passwordInput = document.getElementById('password');
  const rememberMeInput = document.getElementById('rememberMe');
  const errorMessage = document.getElementById('errorMessage');

  const username = usernameInput.value.trim();
  const password = passwordInput.value;
  const rememberMe = rememberMeInput.checked;

  if (!username || !password) {
    showError('请输入用户名和密码');
    return;
  }

  // 禁用表单
  const submitButton = document.querySelector('#loginForm button[type="submit"]');
  submitButton.disabled = true;
  submitButton.textContent = '登录中...';

  fetch('/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username,
      password,
      remember_me: rememberMe
    })
  })
  .then(response => {
    if (!response.ok) {
      return response.json().then(data => {
        throw new Error(data.detail || '登录失败');
      });
    }
    return response.json();
  })
  .then(data => {
    // 存储 token
    const storage = rememberMe ? localStorage : sessionStorage;
    storage.setItem('auth_token', data.access_token);
    storage.setItem('user_info', JSON.stringify(data.user));

    // 清除另一个存储
    if (rememberMe) {
      sessionStorage.removeItem('auth_token');
      sessionStorage.removeItem('user_info');
    } else {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_info');
    }

    // 隐藏登录模态框
    hideLoginModal();

    // 更新用户信息
    updateUserInfo();

    // 刷新页面内容
    bootstrap();

    console.log('登录成功');
  })
  .catch(error => {
    showError(error.message);
    submitButton.disabled = false;
    submitButton.textContent = '登录';
  });
}

function showError(message) {
  const errorMessage = document.getElementById('errorMessage');
  if (errorMessage) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    setTimeout(() => {
      errorMessage.style.display = 'none';
    }, 5000);
  }
}

// Setup login form handler when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
});

function formatDate(value) {
  if (!value) return "--";
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined || value === "") return "--";
  return Number(value).toFixed(digits);
}

function metricClass(value) {
  const num = Number(value || 0);
  if (num === 0 || Number.isNaN(num)) return "metric-flat";
  return num > 0 ? "metric-positive" : "metric-negative";
}

function fillRows(tbodyId, columns, rowsHtml, emptyText) {
  document.getElementById(tbodyId).innerHTML =
    rowsHtml || `<tr><td colspan="${columns}" class="empty-state">${emptyText}</td></tr>`;
}

function toDatetimeLocalString(date) {
  const offsetMs = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
}

function getCurrentStrategyId() {
  const value = document.getElementById("strategySelect").value;
  return value ? Number(value) : null;
}

async function loadActiveStrategies() {
  const select = document.getElementById("strategySelect");
  const data = await fetchJson("/api/strategies?page=1&page_size=100&status=active");
  select.innerHTML = "";

  if (!data.items.length) {
    select.innerHTML = '<option value="">暂无激活策略</option>';
    select.disabled = true;
    return;
  }

  data.items.forEach((item) => {
    const option = document.createElement("option");
    option.value = String(item.strategy_id);
    option.textContent = `${item.name} (#${item.strategy_id})`;
    select.appendChild(option);
  });
  select.disabled = false;
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
  fillRows("manualPositionsBody", 6, rows, "当前策略暂无持仓");
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
          <td>${item.exec_status || "--"}</td>
        </tr>
      `,
    )
    .join("");
  fillRows("manualTradesBody", 7, rows, "当前策略暂无成交记录");
}

function renderOrderResult(order) {
  const box = document.getElementById("orderResult");
  box.innerHTML = `
    <strong>提交成功</strong><br>
    trade_id=${order.trade_id} · ${order.direction} ${order.symbol}<br>
    quantity=${order.quantity} · price=${order.price} · realized_pnl=${order.realized_pnl ?? 0}<br>
    trade_time=${formatDate(order.trade_time)}
  `;
}

async function refreshManualPanel() {
  const strategyId = getCurrentStrategyId();
  if (!strategyId) {
    renderPositions([]);
    renderTrades([]);
    document.getElementById("manualTotalTrades").textContent = "0";
    document.getElementById("manualRealizedPnl").textContent = "0.00";
    document.getElementById("manualUnrealizedPnl").textContent = "0.00";
    return;
  }

  const [stats, overview, positions, trades] = await Promise.all([
    fetchJson(`/api/trades/stats?strategy_id=${strategyId}`),
    fetchJson(`/api/positions/overview?strategy_id=${strategyId}`),
    fetchJson(`/api/positions?strategy_id=${strategyId}`),
    fetchJson(`/api/trades?strategy_id=${strategyId}&page=1&page_size=10`),
  ]);

  document.getElementById("manualTotalTrades").textContent = String(stats.total_trades ?? 0);
  document.getElementById("manualRealizedPnl").textContent = formatNumber(stats.total_realized_pnl);
  document.getElementById("manualUnrealizedPnl").textContent = formatNumber(overview.total_unrealized_pnl);
  renderPositions(positions || []);
  renderTrades((trades && trades.items) || []);
}

async function submitOrder(event) {
  event.preventDefault();

  const strategyId = getCurrentStrategyId();
  if (!strategyId) {
    alert("请先选择激活策略");
    return;
  }

  const quantity = Number(document.getElementById("quantityInput").value);
  const price = Number(document.getElementById("priceInput").value);
  const commission = Number(document.getElementById("commissionInput").value || 0);
  if (!Number.isFinite(quantity) || quantity <= 0) {
    alert("数量必须大于 0");
    return;
  }
  if (!Number.isFinite(price) || price <= 0) {
    alert("价格必须大于 0");
    return;
  }
  if (!Number.isFinite(commission) || commission < 0) {
    alert("手续费必须大于等于 0");
    return;
  }

  const tradeTime = document.getElementById("tradeTimeInput").value;
  const payload = {
    strategy_id: strategyId,
    symbol: document.getElementById("symbolInput").value.trim(),
    direction: document.getElementById("directionSelect").value,
    quantity,
    price,
    commission,
    trade_time: tradeTime || null,
    remark: document.getElementById("remarkInput").value.trim() || null,
  };

  if (!payload.symbol) {
    alert("标的不能为空");
    return;
  }

  try {
    const order = await fetchJson("/api/trades", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderOrderResult(order);
    await refreshManualPanel();
  } catch (error) {
    alert(error.message);
  }
}

async function bootstrap() {
  document.getElementById("tradeTimeInput").value = toDatetimeLocalString(new Date());
  await loadActiveStrategies();
  await refreshManualPanel();
}

document.getElementById("manualOrderForm").addEventListener("submit", submitOrder);
document.getElementById("strategySelect").addEventListener("change", () => {
  refreshManualPanel().catch((error) => alert(error.message));
});

checkAuthStatus().then(isAuthenticated => {
  if (isAuthenticated) {
    updateUserInfo();
    bootstrap().catch((error) => {
      console.error(error);
      alert(error.message);
    });
  }
});
