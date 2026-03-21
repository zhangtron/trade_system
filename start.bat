@echo off
chcp 65001 >nul
title 模拟交易系统

echo ========================================
echo    模拟交易系统启动中...
echo ========================================

REM 设置conda环境名称
set CONDA_ENV=trade_sys

REM 激活conda环境
call conda activate %CONDA_ENV%
if errorlevel 1 (
    echo [错误] 激活conda环境失败，请确保环境 "%CONDA_ENV%" 已创建
    echo.
    echo 如未创建环境，请运行：
    echo   conda create -n %CONDA_ENV% python=3.13
    echo   conda activate %CONDA_ENV%
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

echo [OK] Conda环境已激活

REM 检查并创建数据库
if not exist "trade_system.db" (
    echo [INFO] 数据库文件不存在，跳过初始化
) else (
    echo [OK] 数据库文件已存在
)

REM 启动应用
echo.
echo [OK] 启动服务...
echo [INFO] 访问地址: http://127.0.0.1:8899
echo [INFO] 按 Ctrl+C 停止服务
echo.

python run.py

pause
