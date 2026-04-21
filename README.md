# 模拟交易系统（报表版）

当前仓库已收敛为”报表功能优先”的最新版本，只保留策略报表、持仓、历史持仓与交易记录相关能力。

## 🚀 快速启动

### 开发环境
```bash
# 使用 uvicorn（推荐，支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8899

# 或使用 run.py
python run.py
```

### 生产环境
```bash
# 使用多进程
uvicorn app.main:app --host 0.0.0.0 --port 8899 --workers 4
```

### 首次部署
```bash
# 1. 初始化管理员账户
python scripts/init_admin.py

# 2. 修改默认密码
python scripts/change_password.py

# 3. 生成 SECRET_KEY（生产环境）
python scripts/generate_secret_key.py

# 4. 启动应用
python run.py
```

**默认地址：**
- 首页：`http://localhost:8899/`
- Swagger API 文档：`http://localhost:8899/docs`
- 登录页：`http://localhost:8899/login`

**默认管理员账户：**
- 用户名：`admin`
- 密码：`admin123`（首次登录后请修改）

---

## 📁 项目结构

```
trade_system/
├── app/                    # 应用核心代码
│   ├── __init__.py
│   ├── main.py            # FastAPI 应用和路由
│   ├── auth.py            # 认证和授权模块
│   ├── database.py        # 数据库连接
│   ├── models.py          # SQLAlchemy 模型
│   ├── schemas.py         # Pydantic 模型
│   └── services.py        # 业务逻辑
│
├── templates/             # HTML 模板
│   ├── index.html         # 首页（策略列表）
│   ├── login.html         # 登录页面
│   ├── manual_order.html  # 手动下单页面
│   ├── strategy_detail.html # 策略详情页面
│   ├── user_management.html # 用户管理页面
│   └── 403.html           # 权限不足页面
│
├── static/                # 静态资源
│   ├── styles.css         # 样式文件
│   ├── app.js             # 首页脚本
│   ├── login.js           # 登录页脚本
│   ├── manual_order.js    # 手动下单脚本
│   └── strategy_detail.js # 策略详情脚本
│
├── scripts/               # 管理和维护脚本 ⭐
│   ├── init_admin.py      # 初始化管理员
│   ├── change_password.py # 修改密码工具
│   ├── generate_secret_key.py # 生成密钥工具
│   └── README.md          # 脚本使用说明
│
├── docs/                  # 项目文档 ⭐
│   ├── DEPLOYMENT_AUTH.md       # 认证部署指南
│   ├── SECURITY_CONFIG_GUIDE.md # 安全配置指南
│   ├── PERMISSION_TEST_GUIDE.md # 权限测试指南
│   ├── README_TradeApi.md       # TradeApi 集成指南
│   ├── CSV_Export_Debug_Guide.md # 导出功能调试
│   └── README.md          # 文档索引
│
├── tests/                 # 测试文件
│   ├── test_app.py        # 应用测试
│   ├── trade_api.py       # TradeApi 客户端
│   └── joinquant_strategy_template.py
│
├── config.yaml            # 配置文件
├── run.py                 # 启动脚本
├── requirements.txt       # Python 依赖
└── README.md              # 本文件
```

---

## 🔐 核心功能

### 认证和权限管理
- ✅ JWT Token 认证
- ✅ 基于角色的访问控制（RBAC）
- ✅ 管理员/普通用户权限分离
- ✅ 用户管理（仅管理员）
- ✅ 密码安全（BCrypt 加密）

### 策略管理
- ✅ 策略列表与详情报表
- ✅ 创建策略（仅管理员）
- ✅ 策略状态管理
- ✅ 策略版本控制

### 交易功能
- ✅ 手动下单（仅管理员）
- ✅ 交易记录查询
- ✅ 当前持仓管理
- ✅ 历史持仓查询
- ✅ 持盈亏计算

### 数据导出
- ✅ CSV 导出功能
- ✅ 收益曲线展示
- ✅ 策略报表指标

---

## 📊 权限说明

### 管理员权限
- 查看所有策略和持仓
- 创建新策略
- 手动下单交易
- 用户管理
- 导出数据

### 普通用户权限
- 查看策略列表和详情
- 查看持仓和交易记录
- 导出数据
- ❌ 创建策略
- ❌ 手动下单
- ❌ 用户管理

---

## 🔗 主要接口

### 认证相关
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/logout` - 用户登出
- `GET /api/users` - 用户列表（仅管理员）
- `POST /api/users` - 创建用户（仅管理员）
- `DELETE /api/users/{user_id}` - 删除用户（仅管理员）

### 策略相关
- `GET /api/strategies` - 策略列表
- `GET /api/strategies/{id}` - 策略详情
- `GET /api/strategies/{id}/dashboard` - 策略仪表板
- `POST /api/strategies` - 创建策略（仅管理员）
- `PUT /api/strategies/{id}` - 更新策略
- `PUT /api/strategies/{id}/status` - 更新策略状态

### 交易相关
- `POST /api/trades` - 创建交易（仅管理员）
- `GET /api/trades` - 交易记录
- `GET /api/trades/stats` - 交易统计
- `GET /api/trades/{trade_id}` - 交易详情

### 持仓相关
- `GET /api/positions` - 当前持仓
- `GET /api/positions/overview` - 持仓概览
- `GET /api/positions/history` - 历史持仓
- `PUT /api/positions/update-prices` - 更新价格
- `PUT /api/positions/manual-adjustments` - 手动调整

---

## 🧪 测试

### 单元测试
```bash
python -m pytest tests/test_app.py
```

### 全流程测试
```bash
# 基础测试
python scripts/full_flow_test.py

# 长周期高波动测试
python scripts/full_flow_test.py --days 240 --volatility 0.08 --min-trades 60

# HTTP 模式（需先启动服务）
python scripts/full_flow_test.py --mode http --base-url http://localhost:8899
```

### 权限测试
详细的权限测试指南请查看：[docs/PERMISSION_TEST_GUIDE.md](docs/PERMISSION_TEST_GUIDE.md)

---

## 📖 文档

### 快速链接
- **部署指南**：[docs/DEPLOYMENT_AUTH.md](docs/DEPLOYMENT_AUTH.md)
- **安全配置**：[docs/SECURITY_CONFIG_GUIDE.md](docs/SECURITY_CONFIG_GUIDE.md)
- **权限测试**：[docs/PERMISSION_TEST_GUIDE.md](docs/PERMISSION_TEST_GUIDE.md)
- **脚本说明**：[scripts/README.md](scripts/README.md)
- **文档索引**：[docs/README.md](docs/README.md)

### 脚本工具
```bash
# 初始化管理员
python scripts/init_admin.py

# 修改密码
python scripts/change_password.py

# 生成密钥
python scripts/generate_secret_key.py
```

---

## ⚙️ 配置

### 数据库配置（config.yaml）
```yaml
database:
  type: mysql  # mysql 或 sqlite
  mysql:
    user: root
    password: your_password
    host: localhost
    port: 3306
    database: trade_system_db
```

### 认证配置（config.yaml）
```yaml
auth:
  secret_key: “your-secret-key-here”  # 生产环境使用强随机密钥
  access_token_expire_minutes: 1440   # Token 有效期
  remember_me_expire_days: 7          # 记住登录有效期
```

### 应用配置（config.yaml）
```yaml
app:
  host: 0.0.0.0
  port: 8899
```

---

## 🛡️ 安全建议

### 🔴 生产环境必做
1. ✅ 修改默认管理员密码
2. ✅ 使用强随机 SECRET_KEY（运行 `python scripts/generate_secret_key.py`）
3. ✅ 启用 HTTPS
4. ✅ 配置防火墙规则
5. ✅ 设置配置文件权限（600）
6. ✅ 定期备份数据库
7. ✅ **不要将 config.yaml 提交到版本控制**

### 🟡 安全配置检查清单
- [ ] 已运行 `python scripts/generate_secret_key.py` 生成强密钥
- [ ] 已修改默认管理员密码
- [ ] 已配置 .gitignore 排除 config.yaml
- [ ] 已启用 HTTPS（生产环境）
- [ ] 已设置合理的 Token 过期时间（建议15-30分钟）
- [ ] 已配置 CORS 允许的源
- [ ] 已设置速率限制
- [ ] 已配置防火墙规则

### 密码和密钥管理

- 密码长度至少 8 位，包含大小写字母和数字
- SECRET_KEY 使用 `python scripts/generate_secret_key.py` 生成
- 定期更换密码和密钥（建议 3-6 个月）
- 不要在代码中硬编码密钥

### 🔐 安全特性

- ✅ JWT Token 认证
- ✅ BCrypt 密码哈希
- ✅ 基于角色的访问控制（RBAC）
- ✅ SQL 注入防护（使用 SQLAlchemy ORM）
- ✅ XSS 防护（内容安全策略头）
- ✅ 点击劫持防护（X-Frame-Options）
- ✅ CORS 配置
- ✅ 安全响应头

### 📋 安全审查
详细的安全审查报告请查看：[SECURITY_AUDIT.md](SECURITY_AUDIT.md)

#### 最近一次安全审查：2026-04-21

- ✅ 修复了敏感信息暴露问题
- ✅ 添加了安全响应头
- ✅ 改进了配置文件管理
- ✅ 创建了密钥生成工具

---

## 🚨 故障排查

### 常见问题

**问题：无法登录**
- 检查是否已运行 `python scripts/init_admin.py`
- 确认用户名和密码正确
- 查看浏览器控制台错误信息

**问题：API 返回 401**
- Token 可能过期，重新登录
- 检查浏览器 Local Storage/Session Storage

**问题：权限不足**
- 确认用户角色（管理员/普通用户）
- 检查功能权限要求

**问题：脚本运行报错**
- 确保从项目根目录运行
- 检查 Python 路径配置

---

## 📞 技术支持

如有问题，请查看：
1. API 文档：`http://localhost:8899/docs`
2. 项目文档：[docs/](docs/)
3. 脚本说明：[scripts/README.md](scripts/README.md)
4. 应用日志：控制台输出
