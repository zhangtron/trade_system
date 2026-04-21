# 项目文档中心

本目录包含交易系统的完整文档，涵盖部署、配置、测试等方面。

## 📚 文档列表

### 🚀 部署相关

#### DEPLOYMENT_AUTH.md - 认证功能部署指南
**说明：** 详细的认证系统部署步骤和配置说明。

**内容：**
- ✅ 已完成的修改工作
- 📦 依赖包安装
- 🔧 管理员账户初始化
- 🌐 应用启动步骤
- 🔍 功能验证方法
- ⚙️ API 端点说明
- 🔒 安全配置要点
- 📋 故障排查指南

**适用场景：**
- 首次部署认证系统
- 了解认证功能架构
- 生产环境配置

**快速链接：**
```bash
# 查看部署指南
cat docs/DEPLOYMENT_AUTH.md
```

---

#### SECURITY_CONFIG_GUIDE.md - 安全配置指南
**说明：** 生产环境安全配置的完整指南。

**内容：**
- 🔐 密码管理（修改管理员密码）
- 🔑 SECRET_KEY 管理（生成和更新）
- 🚀 生产环境配置清单
- 🛡️ 安全最佳实践
- 📋 首次部署检查清单
- 🔄 密钥轮换流程
- 🚨 故障恢复方案

**适用场景：**
- 生产环境安全加固
- 密码和密钥管理
- 安全审计和合规

**重要工具：**
```bash
# 修改密码
python scripts/change_password.py

# 生成密钥
python scripts/generate_secret_key.py
```

---

### 🧪 测试相关

#### PERMISSION_TEST_GUIDE.md - 权限控制测试指南
**说明：** 基于角色的访问控制测试指南。

**内容：**
- 🔒 权限说明（管理员 vs 普通用户）
- 🧪 测试步骤（创建用户、功能验证）
- 🔍 API 权限测试（curl 命令）
- 🌐 浏览器测试场景
- 🛡️ 安全特性说明
- 📊 权限对比表
- ⚠️ 注意事项
- 🔄 测试数据重置

**适用场景：**
- 验证权限控制功能
- 用户权限测试
- 功能回归测试

**权限矩阵：**
| 功能 | 管理员 | 普通用户 |
|------|--------|----------|
| 查看策略 | ✅ | ✅ |
| 创建策略 | ✅ | ❌ |
| 手动下单 | ✅ | ❌ |
| 用户管理 | ✅ | ❌ |

---

### 📖 开发相关

#### README_TradeApi.md - TradeApi 聚宽平台集成指南
**说明：** 聚宽交易平台 API 客户端使用指南。

**内容：**
- 📁 文件说明
- 🚀 快速开始
- 📊 主要功能
- 🔧 API 变更说明
- 📝 聚宽平台部署
- ⚠️ 注意事项
- 🔄 迁移指南
- 🎯 最佳实践

**适用场景：**
- 聚宽平台策略开发
- API 集成和对接
- 策略回测和实盘

**代码示例：**
```python
from trade_api import TradeApi

api = TradeApi(
    base_url="http://your-server:8899",
    timeout=15
)

# 买入
api.buy(
    strategy_id=1,
    symbol="600519.XSHG",
    quantity=Decimal("100"),
    price=Decimal("1800.50"),
    trade_time="2026-04-16 09:30:00"
)
```

---

#### CSV_Export_Debug_Guide.md - CSV 导出功能调试指南
**说明：** 策略详情页面的 CSV 导出功能使用和调试。

**内容：**
- 📍 导出入口位置
- 🐛 使用 Chrome DevTools 调试
- 📊 测试脚本示例
- 🎯 快速测试步骤
- 💡 常见问题解决

**适用场景：**
- 测试导出功能
- 调试导出问题
- 数据分析和报告

---

## 🎯 按场景查找文档

### 首次部署
1. 📖 阅读 [DEPLOYMENT_AUTH.md](DEPLOYMENT_AUTH.md)
2. 🔐 阅读 [SECURITY_CONFIG_GUIDE.md](SECURITY_CONFIG_GUIDE.md)
3. 🧪 按照 [PERMISSION_TEST_GUIDE.md](PERMISSION_TEST_GUIDE.md) 测试

### 日常维护
1. 🔑 修改密码：参考 [SECURITY_CONFIG_GUIDE.md](SECURITY_CONFIG_GUIDE.md)
2. 🔄 更换密钥：参考 [SECURITY_CONFIG_GUIDE.md](SECURITY_CONFIG_GUIDE.md)
3. 🧪 功能测试：参考 [PERMISSION_TEST_GUIDE.md](PERMISSION_TEST_GUIDE.md)

### 开发集成
1. 📖 阅读 [README_TradeApi.md](README_TradeApi.md)
2. 🐛 参考 [CSV_Export_Debug_Guide.md](CSV_Export_Debug_Guide.md)

---

## 📋 文档更新记录

| 日期 | 文档 | 版本 | 说明 |
|------|------|------|------|
| 2025-04-21 | 所有文档 | 1.0 | 初始版本 |

---

## 🔗 相关资源

- **项目根目录**：[../README.md](../README.md)
- **脚本工具**：[../scripts/README.md](../scripts/README.md)
- **API 文档**：http://localhost:8899/docs
- **在线帮助**：项目 GitHub Issues

---

## 💡 文档使用建议

1. **首次阅读**：按顺序阅读部署和安全相关文档
2. **查阅参考**：使用场景导航快速找到相关文档
3. **问题排查**：查看各文档的故障排查章节
4. **持续学习**：关注最佳实践和安全建议

---

## 📞 获取帮助

如果文档中没有找到答案：
1. 查看 API 文档：`/docs` 端点
2. 检查日志文件：控制台输出
3. 参考测试指南：验证功能是否正常
