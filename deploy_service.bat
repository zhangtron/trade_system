@echo off
chcp 65001 >nul
title 部署服务

echo ========================================
echo    NSSM 服务部署
echo ========================================

setlocal enabledelayedexpansion

REM ====== 配置区域 ======
set PROJECT_DIR=%~dp0
set CONDA_ENV=trade_sys

REM 查找 conda 环境中的 python.exe
set PYTHON_EXE=
for /d %%i in ("%CONDA_PREFIX%\envs\%CONDA_ENV%") do (
    if exist "%%i\python.exe" set PYTHON_EXE=%%i\python.exe
)
if "%PYTHON_EXE%"=="" (
    for /d %%i in ("%USERPROFILE%\anaconda3\envs\%CONDA_ENV%") do (
        if exist "%%i\python.exe" set PYTHON_EXE=%%i\python.exe
    )
)
if "%PYTHON_EXE%"=="" (
    for /d %%i in ("%PROGRAMFILES%\Anaconda3\envs\%CONDA_ENV%") do (
        if exist "%%i\python.exe" set PYTHON_EXE=%%i\python.exe
    )
)
if "%PYTHON_EXE%"=="" (
    for /d %%i in ("%PROGRAMFILES(x86)%\Anaconda3\envs\%CONDA_ENV%") do (
        if exist "%%i\python.exe" set PYTHON_EXE=%%i\python.exe
    )
)

if "%PYTHON_EXE%"=="" (
    echo [错误] 找不到 conda 环境 "%CONDA_ENV%" 中的 python.exe
    echo 请确保已创建 conda 环境并安装依赖
    pause
    exit /b 1
)

echo [OK] 找到 Python: %PYTHON_EXE%

REM 检查 NSSM
set NSSM=nssm.exe
where nssm >nul 2>nul
if errorlevel 1 (
    if exist "nssm.exe" (
        set NSSM=%PROJECT_DIR%nssm.exe
    ) else (
        echo [错误] 未找到 nssm.exe
        echo 请从 https://nssm.cc/download 下载并放到项目目录
        pause
        exit /b 1
    )
)

echo [OK] 找到 NSSM: %NSSM%

REM 停止并删除旧服务（如果存在）
echo.
echo [INFO] 检查旧服务...
net stop TradeSystem >nul 2>nul
%nssm% remove TradeSystem confirm >nul 2>nul

REM 创建日志目录
if not exist "%PROJECT_DIR%logs" mkdir "%PROJECT_DIR%logs"

REM 安装服务
echo.
echo [INFO] 安装服务...
%nssm% install TradeSystem "%PYTHON_EXE%" "%PROJECT_DIR%run.py" -d "%PROJECT_DIR%"
if errorlevel 1 (
    echo [错误] 安装服务失败
    pause
    exit /b 1
)

REM 配置服务
%nssm% set TradeSystem Description "模拟交易系统 API 服务"
%nssm% set TradeSystem Start SERVICE_AUTO_START
%nssm% set TradeSystem AppRestartDelay 5000
%nssm% set TradeSystem AppRotateFiles 1
%nssm% set TradeSystem AppStdout "%PROJECT_DIR%logs\stdout.log"
%nssm% set TradeSystem AppStderr "%PROJECT_DIR%logs\stderr.log"

REM 启动服务
echo [INFO] 启动服务...
net start TradeSystem

echo.
echo ========================================
echo    部署完成！
echo ========================================
echo.
echo 服务名称: TradeSystem
echo 访问地址: http://127.0.0.1:8899
echo.
echo 常用命令:
echo   启动: net start TradeSystem
echo   停止: net stop TradeSystem
echo   重启: net stop TradeSystem ^&^& net start TradeSystem
echo.
echo 日志位置: %PROJECT_DIR%logs\
echo.
pause
