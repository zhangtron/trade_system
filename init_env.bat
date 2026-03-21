@echo off
chcp 65001 >nul
title 环境初始化

echo ========================================
echo    初始化 conda 环境
echo ========================================

REM 创建conda环境（如果不存在）
echo [1/3] 创建conda环境...
conda create -n trade_sys python=3.13 -y
if errorlevel 1 (
    echo [错误] 创建环境失败
    pause
    exit /b 1
)

REM 激活环境
echo [2/3] 激活环境...
call conda activate trade_sys
if errorlevel 1 (
    echo [错误] 激活环境失败
    pause
    exit /b 1
)

REM 安装依赖
echo [3/3] 安装依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 安装依赖失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo    环境初始化完成！
echo ========================================
echo.
echo 运行以下命令启动程序：
echo   call conda activate trade_sys
echo   python run.py
echo.
echo 或者直接运行 start.bat
echo.
pause
