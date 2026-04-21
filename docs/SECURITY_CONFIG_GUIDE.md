# 生产环境安全配置指南

## 🔐 密码管理

### 修改管理员密码

#### 方法1：使用密码修改工具（推荐）

```bash
# 交互式修改
python change_password.py

# 命令行修改
python change_password.py admin new_password123
```

**步骤：**
1. 运行脚本
2. 选择要修改的用户（输入用户名）
3. 输入新密码（两次确认）
4. 密码修改完成

**特点：**
- ✅ 自动验证密码强度
- ✅ 支持所有用户（不只是管理员）
- ✅ 安全的密码输入（不显示明文）
- ✅ 自动 BCrypt 哈希

#### 方法2：通过用户管理页面

1. 使用管理员账户登录
2. 访问 `http://your-server:8899/user-management`
3. 删除旧用户，创建新用户

**注意：** 此方法不支持修改现有用户密码，只能删除重建。

#### 方法3：直接修改数据库（不推荐）

```sql
-- 生成 BCrypt 哈希（需要 Python）
-- 在 Python 中执行：
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("new_password")
print(hashed)

-- 然后在数据库中执行：
UPDATE users SET hashed_password = '$2b$12$...' WHERE username = 'admin';
```

---

## 🔑 SECRET_KEY 管理

### 生成和更新 SECRET_KEY

#### 自动生成（推荐）

```bash
python generate_secret_key.py
```

**功能：**
- 🔐 自动生成 64 字节强随机密钥
- 📦 自动备份原配置文件
- 📝 自动更新 config.yaml
- ✅ 验证密钥强度

**步骤：**
1. 运行脚本
2. 查看生成的密钥
3. 确认更新（输入 yes）
4. 密钥已写入配置文件
5. 重启服务器

#### 手动生成

```bash
# 使用 OpenSSL
openssl rand -hex 32

# 使用 Python
python -c "import secrets; print(secrets.token_urlsafe(64))"

# 在线工具（不推荐生产环境）
# https://generate-random.org/encryption-key-generator
```

然后将生成的密钥手动更新到 `config.yaml`：

```yaml
auth:
  secret_key: "your-generated-secret-key-here"
```

---

## 🚀 生产环境配置清单

### 1. 修改默认管理员密码

**必做项！** 生产环境必须修改默认密码。

```bash
python change_password.py
```

输入用户名：`admin`
输入新密码：[使用强密码]

### 2. 生成强随机 SECRET_KEY

**必做项！** 生产环境必须使用强随机密钥。

```bash
python generate_secret_key.py
```

### 3. 配置文件权限

**必做项！** 限制配置文件访问权限。

```bash
# Linux/Mac
chmod 600 config.yaml

# Windows (使用文件属性)
# 右键点击 config.yaml → 属性 → 安全 → 编辑权限
```

### 4. 配置文件版本控制

**必做项！** 避免敏感信息泄露。

在 `.gitignore` 中添加：

```gitignore
# 配置文件（包含敏感信息）
config.yaml
config.yaml.backup.*

# 但保留示例配置文件
!config.yaml.example
```

创建示例配置文件 `config.yaml.example`：

```yaml
# 数据库配置
database:
  type: mysql
  mysql:
    user: your_username
    password: your_password
    host: localhost
    port: 3306
    database: trade_system_db

# 应用配置
app:
  host: 0.0.0.0
  port: 8899

# 认证配置
auth:
  secret_key: "your-secret-key-here"
  access_token_expire_minutes: 1440
  remember_me_expire_days: 7
```

---

## 🛡️ 安全最佳实践

### 密码策略

1. **最小长度**：8 个字符
2. **复杂度要求**：
   - 包含大小写字母
   - 包含数字
   - 可选：包含特殊字符

3. **定期更换**：建议每 3-6 个月更换一次

4. **避免使用**：
   - 常见密码（password、12345678）
   - 生日、电话号码
   - 字典单词

### SECRET_KEY 策略

1. **密钥长度**：至少 32 字符（推荐 64+）
2. **随机性**：使用密码学安全的随机数生成器
3. **定期更换**：建议每 6-12 个月更换一次
4. **更换影响**：更换后所有 Token 失效，用户需重新登录

### 网络安全

1. **启用 HTTPS**：生产环境必须使用
2. **防火墙配置**：限制数据库端口访问
3. **反向代理**：使用 Nginx/Apache
4. **API 限流**：防止暴力破解

---

## 📋 首次部署检查清单

### 启动前检查

- [ ] 运行 `python init_admin.py` 创建管理员账户
- [ ] 运行 `python change_password.py` 修改默认密码
- [ ] 运行 `python generate_secret_key.py` 生成强随机密钥
- [ ] 设置 `config.yaml` 文件权限为 600
- [ ] 检查数据库密码强度
- [ ] 配置 HTTPS 证书
- [ ] 配置防火墙规则

### 启动后检查

- [ ] 使用管理员账户登录
- [ ] 创建一个测试用户
- [ ] 测试普通用户权限
- [ ] 检查日志文件无异常
- [ ] 测试 Token 过期机制
- [ ] 验证 HTTPS 正常工作

---

## 🔄 密钥轮换流程

### 定期更换 SECRET_KEY

1. **准备阶段**
   ```bash
   # 通知用户系统将在指定时间维护
   # 建议用户提前保存工作内容
   ```

2. **生成新密钥**
   ```bash
   python generate_secret_key.py
   ```

3. **更新配置**
   - 配置文件已自动更新
   - 旧密钥已备份

4. **重启服务**
   ```bash
   # 重启应用服务器
   # 所有 Token 失效
   ```

5. **验证功能**
   - 测试登录功能
   - 测试 API 访问
   - 检查日志无异常

---

## 🚨 故障恢复

### 密钥丢失/损坏

如果 `config.yaml` 中的密钥丢失或损坏：

```bash
# 重新生成密钥
python generate_secret_key.py

# 重启服务
# 用户需要重新登录
```

### 无法登录

如果忘记管理员密码：

```bash
# 重新初始化（会重置密码）
python init_admin.py

# 或使用密码修改工具
python change_password.py admin new_password
```

---

## 📞 技术支持

如有问题，请检查：

1. **配置文件格式**：确保 YAML 语法正确
2. **文件权限**：确保应用有读取权限
3. **日志文件**：查看应用日志排查问题
4. **数据库连接**：确保数据库配置正确

---

## 🔗 相关文件

- `change_password.py` - 密码修改工具
- `generate_secret_key.py` - 密钥生成工具
- `init_admin.py` - 管理员初始化工具
- `config.yaml` - 配置文件
- `app/auth.py` - 认证模块
