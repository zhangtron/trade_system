# Windows 服务部署指南 (NSSM)

本文档介绍如何使用 NSSM 将模拟交易系统部署为 Windows 后台服务。

## 前置要求

- Windows Server 2016+ 或 Windows 10/11
- Conda 已安装
- NSSM 工具

## 步骤一：下载 NSSM

1. 访问 NSSM 官网下载最新版本：https://nssm.cc/download
2. 解压后将 `nssm.exe` 放到项目根目录或系统 PATH 中
3. 或者使用 winget 安装：
   ```powershell
   winget install nssm
   ```

## 步骤二：准备应用

确保项目结构如下：
```
trade_system/
├── run.py              # 启动入口
├── app/                # 应用代码
├── templates/          # 模板文件
├── static/             # 静态文件
└── nssm.exe           # NSSM 工具（可选放这里）
```

测试应用能否正常启动：
```powershell
python run.py
```

## 步骤三：创建服务

以管理员身份打开 PowerShell，执行：

```powershell
# 进入项目目录
cd E:\Desktop\trade_system

# 找到 conda 环境中的 python.exe 路径
# 假设 conda 环境名称为 trade_sys
# 默认路径类似：C:\Users\用户名\anaconda3\envs\trade_sys\python.exe
# 或：C:\ProgramData\anaconda3\envs\trade_sys\python.exe

# 创建服务（conda 环境）
nssm.exe install TradeSystem "C:\Users\你的用户名\anaconda3\envs\trade_sys\python.exe" "E:\Desktop\trade_system\run.py" -d "E:\Desktop\trade_system"
```

参数说明：
| 参数 | 说明 |
|------|------|
| `TradeSystem` | 服务名称（可自定义） |
| 第一个路径 | conda 环境中的 python.exe 完整路径 |
| 第二个路径 | run.py 完整路径 |
| `-d` | 工作目录 |

## 步骤四：配置服务

```powershell
# 设置服务描述
nssm.exe set TradeSystem Description "模拟交易系统 API 服务"

# 设置启动方式为自动
nssm.exe set TradeSystem Start SERVICE_AUTO_START

# 设置重启策略（应用崩溃后自动重启）
nssm.exe set TradeSystem AppRestartDelay 5000
```

## 步骤五：启动服务

```powershell
# 启动服务
Start-Service TradeSystem

# 检查服务状态
Get-Service TradeSystem
```

## 常用操作

```powershell
# 停止服务
Stop-Service TradeSystem

# 重启服务
Restart-Service TradeSystem

# 删除服务
nssm.exe remove TradeSystem confirm
```

## 日志查看

NSSM 会自动重定向应用输出到日志文件：

```powershell
# 查看日志输出位置
nssm.exe get TradeSystem AppStdout

# 设置日志文件路径
nssm.exe set TradeSystem AppStdout "E:\Desktop\trade_system\logs\stdout.log"
nssm.exe set TradeSystem AppStderr "E:\Desktop\trade_system\logs\stderr.log"

# 启用日志轮转
nssm.exe set TradeSystem AppRotateFiles 1
```

## 访问应用

服务启动后，访问：http://127.0.0.1:8000

如需局域网访问，修改 `run.py`：
```python
uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
```

## 故障排查

1. **服务无法启动**
   - 检查 conda 环境路径是否正确
   - 确认 conda 环境已安装必要依赖
   - 查看 NSSM 日志

2. **端口被占用**
   ```powershell
   netstat -ano | findstr :8000
   ```

3. **权限问题**
   - 确保以管理员身份运行 PowerShell
   - 检查文件夹读写权限
