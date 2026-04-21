# 交易系统认证功能部署说明

## 已完成的修改

### 第一阶段：基础认证设施 ✅
- ✅ 添加认证依赖包 (python-jose, passlib, bcrypt)
- ✅ 创建 User 模型和 UserRole 枚举
- ✅ 创建认证模块 (app/auth.py)
- ✅ 添加认证 API 端点
- ✅ 创建登录页面
- ✅ 添加登录页面样式
- ✅ 创建管理员初始化脚本

### 第二阶段：API 保护 ✅
- ✅ 为所有策略相关 API 添加认证保护
- ✅ 为所有交易相关 API 添加认证保护
- ✅ 为所有持仓相关 API 添加认证保护

### 第三阶段：前端认证集成 ✅
- ✅ 更新所有 fetchJson 函数添加认证头
- ✅ 添加认证状态检查和用户信息显示
- ✅ 修改所有页面导航栏显示用户信息
- ✅ 添加页面级路由守卫

## 部署步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

新增的依赖包：
- python-jose[cryptography]==3.3.0
- passlib[bcrypt]==1.7.4
- bcrypt==4.1.2

### 2. 初始化管理员账户

```bash
python init_admin.py
```

默认管理员账户：
- 用户名：`admin`
- 密码：`admin123`

⚠️ **重要**：首次登录后请立即修改默认密码！

### 3. 启动应用

```bash
# 开发环境
uvicorn app.main:app --reload --port 8899

# 生产环境
uvicorn app.main:app --host 0.0.0.0 --port 8899 --workers 4
```

### 4. 访问系统

1. 打开浏览器访问 `http://localhost:8899`
2. 系统会自动跳转到登录页面
3. 使用默认管理员账户登录
4. 登录成功后可以正常使用所有功能

## 功能验证

### 1. 登录功能测试
1. 访问首页，应自动跳转到 `/login`
2. 使用管理员账户登录（admin/admin123）
3. 登录成功后应跳转到首页
4. 导航栏应显示用户信息

### 2. API 认证测试
```bash
# 无 token 访问应返回 401
curl http://localhost:8899/api/strategies

# 使用 token 访问应正常返回
TOKEN="your-jwt-token"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8899/api/strategies
```

### 3. 用户管理测试（需要管理员权限）
```bash
# 创建新用户
curl -X POST http://localhost:8899/api/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "email": "test@example.com",
    "full_name": "Test User",
    "role": "user"
  }'
```

### 4. 登出功能测试
1. 点击导航栏中的"登出"按钮
2. 应清除本地认证信息
3. 应跳转到登录页

## API 端点说明

### 认证相关 API
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/logout` - 用户登出
- `GET /api/users` - 用户列表（仅管理员）
- `POST /api/users` - 创建用户（仅管理员）
- `PUT /api/users/{user_id}` - 更新用户（仅管理员）

### 业务 API（需要认证）
所有 `/api/strategies/*`, `/api/trades/*`, `/api/positions/*` 下的端点都需要认证

## 安全配置

### 生产环境必须修改

1. **SECRET_KEY** - 在 `app/auth.py` 中修改：
   ```python
   SECRET_KEY = "your-production-secret-key-min-32-chars"
   ```
   建议使用 `openssl rand -hex 32` 生成

2. **默认管理员密码** - 首次登录后立即修改

3. **数据库密码** - 使用强密码

4. **启用 HTTPS** - 生产环境必须使用 HTTPS

### 推荐安全实践

1. **密码策略**
   - 最小长度 8 位
   - 包含大小写字母、数字
   - 定期强制修改密码

2. **Token 管理**
   - Token 有效期：24 小时（默认）
   - 记住登录功能：7 天有效
   - 建议实现 Token 自动刷新机制

3. **访问控制**
   - 限制 API 请求频率
   - 记录登录失败次数
   - 审计敏感操作日志

## 故障排查

### 问题：无法登录
- 检查用户名和密码是否正确
- 确认数据库连接正常
- 查看 `init_admin.py` 是否成功执行

### 问题：API 返回 401
- 确认已正确登录
- 检查浏览器控制台的 localStorage/sessionStorage
- 确认 token 未过期

### 问题：用户信息显示异常
- 检查 `userNav` 元素是否存在
- 确认 user_info 数据格式正确
- 查看浏览器控制台错误信息

## 后续优化方向

1. **Token 自动刷新** - 避免用户频繁登录
2. **多级权限管理** - 细粒度的功能权限控制
3. **操作审计日志** - 记录所有敏感操作
4. **双因素认证** - 提高账户安全性
5. **密码找回功能** - 通过邮件重置密码
6. **账户锁定机制** - 多次登录失败后锁定账户

## 技术架构

### 后端认证
- **密码哈希**：BCrypt
- **Token 生成**：JWT (JSON Web Tokens)
- **认证方式**：HTTP Bearer Token
- **权限控制**：基于角色的访问控制 (RBAC)

### 前端认证
- **Token 存储**：localStorage（记住登录）或 sessionStorage（临时登录）
- **认证检查**：页面加载时验证 token 有效性
- **自动跳转**：未登录时自动跳转到登录页
- **用户信息**：动态显示在导航栏

## 联系支持

如有问题，请查看：
- 应用日志：控制台输出
- 浏览器控制台：前端错误信息
- API 响应：详细的错误信息
