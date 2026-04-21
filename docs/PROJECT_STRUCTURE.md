# 项目文件结构说明

## 📁 完整目录树

```
trade_system/
│
├── 📄 README.md                    # 项目主文档
├── 📄 config.yaml                  # 配置文件
├── 📄 requirements.txt             # Python 依赖
├── 🚀 run.py                       # 应用启动脚本
├── 📄 sitecustomize.py             # Python 环境配置
│
├── 📂 app/                         # 应用核心代码
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用和路由
│   ├── auth.py                    # 认证和授权模块 ⭐
│   ├── database.py                # 数据库连接
│   ├── models.py                  # SQLAlchemy 数据模型
│   ├── schemas.py                 # Pydantic 验证模型
│   └── services.py                # 业务逻辑服务
│
├── 📂 templates/                   # HTML 模板文件
│   ├── index.html                 # 首页 - 策略列表
│   ├── login.html                 # 登录页面 ⭐
│   ├── manual_order.html          # 手动下单页面
│   ├── strategy_detail.html       # 策略详情页面
│   ├── user_management.html       # 用户管理页面 ⭐
│   └── 403.html                   # 权限不足提示页 ⭐
│
├── 📂 static/                      # 静态资源
│   ├── styles.css                 # 全局样式
│   ├── app.js                     # 首页脚本
│   ├── login.js                   # 登录页脚本 ⭐
│   ├── manual_order.js            # 手动下单脚本
│   └── strategy_detail.js         # 策略详情脚本
│
├── 📂 scripts/                     # 管理和维护工具 ⭐
│   ├── init_admin.py              # 初始化管理员账户
│   ├── change_password.py         # 修改用户密码
│   ├── generate_secret_key.py     # 生成 SECRET_KEY
│   ├── full_flow_test.py          # 完整流程测试
│   └── README.md                  # 脚本使用说明
│
├── 📂 docs/                        # 项目文档 ⭐
│   ├── README.md                  # 文档索引
│   ├── DEPLOYMENT_AUTH.md         # 认证功能部署指南
│   ├── SECURITY_CONFIG_GUIDE.md   # 安全配置指南
│   ├── PERMISSION_TEST_GUIDE.md   # 权限测试指南
│   ├── README_TradeApi.md         # TradeApi 集成指南
│   └── CSV_Export_Debug_Guide.md  # CSV 导出调试指南
│
├── 📂 tests/                       # 测试文件
│   ├── test_app.py                # 应用单元测试
│   ├── trade_api.py               # TradeApi 客户端
│   └── joinquant_strategy_template.py
│
└── 📂 .vendor/                     # 第三方依赖（内部使用）
    └── ...
```

---

## 🔑 符号说明

- 📄 = 配置文件或文档
- 🚀 = 启动脚本
- 📂 = 文件夹/目录
- ⭐ = 新增/重要文件

---

## 📂 核心目录详解

### app/ - 应用核心
**用途：** FastAPI 应用的核心代码
**关键文件：**
- `main.py` - 路由和 API 定义
- `auth.py` - 认证逻辑（JWT Token、权限验证）

### templates/ - HTML 模板
**用途：** 前端页面模板
**关键文件：**
- `login.html` - 登录页面
- `user_management.html` - 用户管理页面

### static/ - 静态资源
**用途：** CSS 样式和 JavaScript 脚本
**关键文件：**
- `login.js` - 登录页面脚本
- `app.js` - 首页脚本（已更新认证逻辑）

### scripts/ - 管理工具 ⭐
**用途：** 项目管理和维护脚本
**关键文件：**
- `init_admin.py` - 创建管理员账户
- `change_password.py` - 修改用户密码
- `generate_secret_key.py` - 生成安全密钥

### docs/ - 项目文档 ⭐
**用途：** 部署、配置、测试文档
**关键文件：**
- `DEPLOYMENT_AUTH.md` - 认证部署步骤
- `SECURITY_CONFIG_GUIDE.md` - 安全配置指南
- `PERMISSION_TEST_GUIDE.md` - 权限测试指南

---

## 🎯 快速导航

### 部署相关
- [部署指南](../docs/DEPLOYMENT_AUTH.md)
- [安全配置](../docs/SECURITY_CONFIG_GUIDE.md)
- [主文档](../README.md)

### 脚本工具
- [脚本说明](../scripts/README.md)
- 初始化管理员：`python scripts/init_admin.py`
- 修改密码：`python scripts/change_password.py`
- 生成密钥：`python scripts/generate_secret_key.py`

### 开发相关
- [权限测试](../docs/PERMISSION_TEST_GUIDE.md)
- [TradeApi 集成](../docs/README_TradeApi.md)
- [导出功能](../docs/CSV_Export_Debug_Guide.md)

---

## 📋 文件移动记录

### 移动到 docs/ 的文件
- ✅ `DEPLOYMENT_AUTH.md`
- ✅ `PERMISSION_TEST_GUIDE.md`
- ✅ `SECURITY_CONFIG_GUIDE.md`
- ✅ `tests/README_TradeApi.md`
- ✅ `tests/CSV_Export_Debug_Guide.md`

### 移动到 scripts/ 的文件
- ✅ `init_admin.py`
- ✅ `change_password.py`
- ✅ `generate_secret_key.py`
- ✅ `full_flow_test.py`

### 保留在根目录的文件
- ✅ `README.md` - 项目主文档
- ✅ `run.py` - 启动脚本
- ✅ `config.yaml` - 配置文件

---

## 🔄 迁移影响

### 脚本路径变化
**旧路径：**
```bash
python init_admin.py
```

**新路径：**
```bash
python scripts/init_admin.py
```

### 文档路径变化
**旧路径：**
```bash
cat DEPLOYMENT_AUTH.md
```

**新路径：**
```bash
cat docs/DEPLOYMENT_AUTH.md
```

---

## 💡 使用建议

### 新用户
1. 先阅读 [README.md](../README.md)
2. 查看 [docs/](../docs/) 中的部署指南
3. 使用 [scripts/](../scripts/) 中的工具初始化

### 日常维护
1. 需要修改密码？→ `python scripts/change_password.py`
2. 需要更换密钥？→ `python scripts/generate_secret_key.py`
3. 遇到问题？→ 查看 [docs/](../docs/) 中的故障排查

### 开发集成
1. API 集成？→ 查看 [docs/README_TradeApi.md](README_TradeApi.md)
2. 功能测试？→ 查看 [docs/PERMISSION_TEST_GUIDE.md](PERMISSION_TEST_GUIDE.md)

---

## 📊 文件统计

| 目录 | 文件数量 | 说明 |
|------|---------|------|
| app/ | 7 | 应用核心代码 |
| templates/ | 6 | HTML 模板 |
| static/ | 5 | 静态资源 |
| scripts/ | 5 | 管理工具 |
| docs/ | 6 | 项目文档 |
| tests/ | 3 | 测试文件 |
| **总计** | **32+** | 完整项目 |

---

*最后更新：2025-04-21*
