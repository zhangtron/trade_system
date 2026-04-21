# 权限控制测试指南

## 🔒 权限说明

### 管理员权限
- ✅ 查看所有策略和持仓
- ✅ 创建新策略
- ✅ 手动下单交易
- ✅ 用户管理（创建、删除用户）
- ✅ 查看所有交易记录
- ✅ 导出数据

### 普通用户权限
- ✅ 查看策略列表和详情
- ✅ 查看持仓和交易记录
- ✅ 导出数据
- ❌ 创建策略
- ❌ 手动下单
- ❌ 用户管理

---

## 🧪 测试步骤

### 1. 创建测试用户

使用管理员账户登录后，访问 `http://localhost:8899/user-management`，创建两个测试用户：

**普通用户：**
- 用户名：`trader01`
- 密码：`password123`
- 角色：`user`

**管理员：**
- 用户名：`admin02`
- 密码：`password123`
- 角色：`admin`

### 2. 测试普通用户权限

**步骤：**
1. 退出当前账户
2. 使用 `trader01` 账户登录
3. 检查导航栏（应该看不到"手动下单"和"创建策略"）
4. 尝试访问受限功能

**预期结果：**
- ✅ 可以访问首页，查看策略列表
- ✅ 可以进入策略详情页
- ❌ 导航栏不显示"手动下单"链接
- ❌ 不显示"创建策略"标签页
- ❌ 访问 `http://localhost:8899/manual-order` 会显示权限不足页面
- ❌ 创建策略 API 返回 403 错误
- ❌ 手动下单 API 返回 403 错误

### 3. 测试管理员权限

**步骤：**
1. 退出当前账户
2. 使用 `admin02` 账户登录
3. 检查导航栏和功能

**预期结果：**
- ✅ 导航栏显示所有功能链接
- ✅ 可以访问手动下单页面
- ✅ 可以创建新策略
- ✅ 可以访问用户管理页面
- ✅ 所有 API 正常工作

---

## 🔍 API 权限测试

### 使用 curl 测试

```bash
# 1. 使用普通用户登录
TOKEN=$(curl -s -X POST http://localhost:8899/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"trader01","password":"password123","remember_me":false}' | \
  jq -r '.access_token')

# 2. 测试创建策略（应该返回 403）
curl -X POST http://localhost:8899/api/strategies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试策略",
    "type": "趋势跟踪",
    "status": "draft"
  }'

# 预期输出：
# {"detail":"需要管理员权限"}

# 3. 测试手动下单（应该返回 403）
curl -X POST http://localhost:8899/api/trades \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": 1,
    "symbol": "600000.XSHG",
    "direction": "BUY",
    "quantity": 100,
    "price": 10.0
  }'

# 预期输出：
# {"detail":"需要管理员权限"}

# 4. 测试查看策略（应该正常工作）
curl http://localhost:8899/api/strategies \
  -H "Authorization: Bearer $TOKEN"

# 预期输出：
# 正常返回策略列表
```

---

## 🌐 浏览器测试

### 测试场景 1：普通用户访问手动下单

1. 使用 `trader01` 登录
2. 直接访问：`http://localhost:8899/manual-order`
3. **预期结果**：显示权限不足页面

### 测试场景 2：普通用户尝试创建策略

1. 使用 `trader01` 登录
2. 打开浏览器控制台（F12）
3. 执行以下代码：

```javascript
fetch('/api/strategies', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`
  },
  body: JSON.stringify({
    name: '测试策略',
    type: '趋势跟踪',
    status: 'draft'
  })
}).then(r => r.json()).then(data => {
  console.log(data);
});
```

4. **预期结果**：返回 `{"detail": "需要管理员权限"}`

### 测试场景 3：管理员访问所有功能

1. 使用 `admin` 登录
2. 验证可以访问所有页面和功能
3. 创建策略成功
4. 手动下单成功

---

## 🛡️ 安全特性

### 前端控制
- 导航栏根据用户角色动态显示链接
- 页面功能根据用户角色显示/隐藏
- Tab 页根据权限动态隐藏

### 后端控制
- API 路由级别的权限验证
- HTTPException 统一异常处理
- 自定义 403/401 错误页面

### 双重保护
- 前端：提升用户体验，避免无意义的点击
- 后端：确保数据安全，防止绕过前端限制

---

## 📋 权限矩阵

| 功能 | 管理员 | 普通用户 |
|------|--------|----------|
| 查看策略列表 | ✅ | ✅ |
| 查看策略详情 | ✅ | ✅ |
| 查看持仓信息 | ✅ | ✅ |
| 查看交易记录 | ✅ | ✅ |
| 导出数据 | ✅ | ✅ |
| **创建策略** | ✅ | ❌ |
| **手动下单** | ✅ | ❌ |
| **用户管理** | ✅ | ❌ |
| 修改策略 | ✅ | ✅* |
| 删除策略 | ✅ | ✅* |

*注：普通用户可以修改/删除自己创建的策略（此功能待实现）

---

## ⚠️ 注意事项

1. **权限缓存**：修改用户角色后，需要用户重新登录才能生效
2. **API 安全**：不要仅依赖前端控制，后端 API 验证才是关键
3. **Token 过期**：Token 默认 24 小时过期，过期后需要重新登录
4. **浏览器缓存**：测试时建议清除浏览器缓存或使用隐私模式

---

## 🔄 重置测试数据

如果需要重置测试数据：

```sql
-- 删除测试用户
DELETE FROM users WHERE username IN ('trader01', 'admin02');

-- 重置管理员密码（可选）
UPDATE users SET hashed_password = '$2b$12$...' WHERE username = 'admin';
```

或者直接在用户管理页面删除测试用户。

---

## 📞 问题排查

### 问题 1：权限控制不起作用
**原因**：服务器未重启
**解决**：重启服务器，确保新代码生效

### 问题 2：普通用户仍能看到受限功能
**原因**：浏览器缓存了旧的前端代码
**解决**：清除浏览器缓存并硬刷新（Ctrl+Shift+R）

### 问题 3：API 返回 401 而不是 403
**原因**：用户未登录或 Token 过期
**解决**：重新登录获取新的 Token

### 问题 4：权限修改后不生效
**原因**：Token 中存储的角色信息不会自动更新
**解决**：用户需要退出并重新登录
