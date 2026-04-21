# 应用启动指南

## 🚀 快速启动

### Windows 用户

#### 方法1：双击启动脚本（推荐）
双击 `start.bat` 文件，选择启动模式：
- 选项 1：生产模式（使用 `run.py`）
- 选项 2：开发模式（热重载）
- 选项 3：自定义参数

#### 方法2：命令行启动
```cmd
# 生产模式
python run.py

# 开发模式（热重载）
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8899
```

### Linux/Mac 用户

#### 方法1：使用启动脚本（推荐）
```bash
./start.sh
```

#### 方法2：命令行启动
```bash
# 生产模式
python3 run.py

# 开发模式（热重载）
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8899
```

---

## 📋 启动模式对比

### 生产模式（python run.py）

**特点：**
- ✅ 从 `config.yaml` 读取配置
- ✅ 自动使用配置的 host 和 port
- ✅ 稳定性好，适合生产环境
- ❌ 无热重载功能

**适用场景：**
- 生产环境部署
- 服务器长期运行
- 不需要频繁修改代码

**配置文件读取：**
```yaml
# config.yaml
app:
  host: 0.0.0.0
  port: 8899
```

### 开发模式（uvicorn --reload）

**特点：**
- ✅ 代码修改后自动重启
- ✅ 开发调试更高效
- ✅ 实时查看修改效果
- ❌ 需要手动指定参数

**适用场景：**
- 开发调试阶段
- 频繁修改代码
- 需要快速验证功能

**启动命令：**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8899
```

---

## ⚠️ 常见问题

### 问题1：`uvicorn: command not found`

**原因：** uvicorn 没有安装或不在 PATH 中

**解决方案：**
```bash
# 使用 Python 模块方式运行
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8899

# 或安装 uvicorn
pip install uvicorn
```

### 问题2：`ModuleNotFoundError: No module named 'app'`

**原因：** 当前工作目录不正确

**解决方案：**
```bash
# 确保在项目根目录运行
cd /path/to/trade_system
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8899
```

### 问题3：配置文件不生效

**原因：** uvicorn 命令不会读取 `config.yaml`

**解决方案：**
- 使用 `python run.py` 启动（会读取配置）
- 或在 uvicorn 命令中手动指定参数

### 问题4：端口被占用

**错误信息：** `Address already in use`

**解决方案：**
```bash
# 查找占用端口的进程
# Windows
netstat -ano | findstr :8899

# Linux/Mac
lsof -i :8899

# 杀死进程或更换端口
python -m uvicorn app.main:app --reload --port 8890
```

---

## 🔧 高级启动选项

### 指定工作目录
```bash
# 确保在项目根目录
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8899
```

### 多进程部署
```bash
# 使用 4 个 worker 进程
python -m uvicorn app.main:app --host 0.0.0.0 --port 8899 --workers 4
```

### 指定日志级别
```bash
# 显示详细日志
python -m uvicorn app.main:app --reload --log-level debug

# 只显示错误
python -m uvicorn app.main:app --reload --log-level error
```

---

## 🎯 推荐使用方式

### 开发环境
```bash
# 使用 start.bat 或 start.sh
./start.sh
# 选择选项 2（开发模式）
```

### 生产环境
```bash
# 使用 start.bat 或 start.sh
./start.sh
# 选择选项 1（生产模式）

# 或直接运行
python run.py
```

### 自定义需求
```bash
# 使用 start.bat 或 start.sh
./start.sh
# 选择选项 3（自定义）

# 或手动运行
python -m uvicorn app.main:app --host 0.0.0.0 --port 8899 --workers 4
```

---

## 📊 启动后验证

### 1. 检查服务状态
访问：`http://localhost:8899/health`

**预期输出：**
```json
{"status": "ok"}
```

### 2. 访问 Web 界面
- 首页：`http://localhost:8899/`
- 登录页：`http://localhost:8899/login`
- API 文档：`http://localhost:8899/docs`

### 3. 测试 API
```bash
curl http://localhost:8899/health
```

---

## 🛑 停止服务

### 开发模式
在运行终端按 `Ctrl + C`

### 生产模式
在运行终端按 `Ctrl + C`

### 强制停止（如有必要）
```bash
# 查找进程
ps aux | grep uvicorn

# 杀死进程
kill -9 [PID]
```

---

## 🔄 重启服务

### 开发模式（自动）
- 修改代码后会自动重启
- 无需手动操作

### 生产模式（手动）
```bash
# 按 Ctrl+C 停止
# 重新运行启动命令
python run.py
```

---

## 📞 故障排查

### 检查依赖
```bash
python -m pytest tests/test_app.py
```

### 检查配置
```bash
python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"
```

### 查看日志
- 控制台输出会显示所有请求和错误
- 使用 `--log-level debug` 查看详细日志

---

## 🔗 相关文档

- [部署指南](DEPLOYMENT_AUTH.md)
- [安全配置指南](SECURITY_CONFIG_GUIDE.md)
- [项目主文档](../README.md)
