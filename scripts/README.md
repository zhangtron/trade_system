# 脚本工具说明

本目录包含项目管理和维护的脚本工具。

## 📋 脚本列表

### 🔐 认证和安全工具

#### init_admin.py - 管理员初始化工具
初始化系统管理员账户。

```bash
python scripts/init_admin.py
```

**功能：**
- 自动创建默认管理员账户
- 默认用户名：`admin`
- 默认密码：`admin123`

**注意：** 生产环境首次登录后请立即修改密码！

---

#### change_password.py - 密码修改工具
修改任意用户的密码。

```bash
# 交互式修改
python scripts/change_password.py

# 命令行修改
python scripts/change_password.py admin new_password123
```

**功能：**
- 修改任意用户密码
- 密码强度验证（至少 8 位）
- 安全的密码输入（不显示明文）
- 自动 BCrypt 加密

**示例：**
```bash
$ python scripts/change_password.py

============================================================
系统用户列表：
============================================================
ID:   1 | 用户名: admin           | 角色: 管理员 | 状态: 启用
ID:   2 | 用户名: trader01        | 角色: 普通用户 | 状态: 启用
============================================================

请输入要修改密码的用户名: admin
请输入新密码: ********
请再次输入新密码: ********

✅ 成功：用户 'admin' 的密码已更新
```

---

#### generate_secret_key.py - 密钥生成工具
生成强随机 SECRET_KEY 并更新到配置文件。

```bash
python scripts/generate_secret_key.py
```

**功能：**
- 生成 64 字节强随机密钥
- 自动备份原配置文件
- 自动更新 config.yaml
- 密钥强度验证

**示例输出：**
```
🔐 正在生成强随机密钥...
📋 生成的密钥（长度: 86 字符）:
======================================================================
xK9d3Ff8Mp2VmLqN7Hj4Rt6WcXsYzB1aE5GhIjKmMnOpQrStUvWxYz1234567890AbCdEf==
======================================================================

✅ 密钥强度：良好

是否要更新配置文件？(yes/no): yes
```

---

### 🧪 测试工具

#### full_flow_test.py - 完整流程测试
测试系统完整功能的脚本。

```bash
python scripts/full_flow_test.py
```

**功能：**
- 测试 API 连接
- 测试数据库操作
- 验证业务流程

---

## 🚀 使用场景

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

### 日常维护
```bash
# 修改用户密码
python scripts/change_password.py

# 更换 SECRET_KEY
python scripts/generate_secret_key.py
```

### 开发测试
```bash
# 运行完整测试
python scripts/full_flow_test.py
```

---

## ⚠️ 注意事项

1. **路径问题**
   - 脚本已自动处理路径问题，可以从项目根目录或 scripts 目录运行
   - 建议从项目根目录运行：`python scripts/xxx.py`

2. **权限要求**
   - 脚本需要读取 `config.yaml` 文件
   - 密码修改工具需要数据库写权限

3. **安全建议**
   - 生产环境必须修改默认密码
   - SECRET_KEY 必须使用强随机密钥
   - 定期更换密码和密钥

4. **备份**
   - `generate_secret_key.py` 会自动备份配置文件
   - 建议手动备份重要数据

---

## 🔗 相关文档

- [部署指南](../docs/DEPLOYMENT_AUTH.md)
- [安全配置指南](../docs/SECURITY_CONFIG_GUIDE.md)
- [权限测试指南](../docs/PERMISSION_TEST_GUIDE.md)

---

## 📞 问题排查

### 问题：脚本运行报错 "No module named 'app'"
**原因：** Python 路径问题
**解决：** 确保从项目根目录运行 `python scripts/xxx.py`

### 问题：配置文件找不到
**原因：** 不在项目根目录运行
**解决：** 切换到项目根目录后再运行

### 问题：数据库连接失败
**原因：** 数据库未启动或配置错误
**解决：** 检查 config.yaml 中的数据库配置
