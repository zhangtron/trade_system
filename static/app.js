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
function clearAuthAndRedirect() {
  localStorage.removeItem('auth_token');
  sessionStorage.removeItem('auth_token');
  localStorage.removeItem('user_info');
  sessionStorage.removeItem('user_info');
  // 显示登录模态框而不是重定向
  showLoginModal();
}

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

    // 隐藏创建策略标签（仅管理员可见）
    const createTab = document.querySelector('[data-tab="create"]');
    if (createTab && user.role !== 'admin') {
      createTab.style.display = 'none';
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

    // 更新用户信息和页面内容
    updateUserInfo();

    // 如果有 pending 的操作，可以在这里处理
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

// 页面加载时立即检查认证状态
checkAuthStatus().then(isAuthenticated => {
  if (isAuthenticated) {
    // 已登录，正常加载页面内容
    updateUserInfo();
    Promise.all([loadStrategies(), refreshOverview()]).catch((error) => {
      console.error(error);
      alert(error.message);
    });
  }
  // else: 未登录状态，clearAuthAndRedirect() 已经显示了登录模态框
});

// Setup login form handler when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
});
