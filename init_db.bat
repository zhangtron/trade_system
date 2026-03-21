@echo off
chcp 65001 >nul
title 初始化数据库

echo ========================================
echo    数据库初始化
echo ========================================

echo.
echo 请选择数据库类型：
echo   1) SQLite
echo   2) MySQL
echo.
set /p CHOICE=请输入选项 (1/2):

if "%CHOICE%"=="1" goto sqlite
if "%CHOICE%"=="2" goto mysql
echo 无效选项
pause
exit /b

:sqlite
echo.
echo [INFO] 使用 SQLite
echo.
call conda activate trade_sys
pip install pyyaml -q
python -c "from app.database import engine, Base; from app import models; Base.metadata.create_all(bind=engine)"
echo.
echo 数据库表创建完成！
echo 数据库文件: trade_system.db
echo.
echo 请确保 config.yaml 中 database.type 设为 sqlite
pause
exit /b

:mysql
echo.
echo [INFO] 使用 MySQL
echo.
call conda activate trade_sys
pip install pyyaml -q

REM 检查 MySQL 是否可用
mysql -u root -p7842zc -e "SELECT 1" >nul 2>&1
if errorlevel 1 (
    echo [错误] 无法连接 MySQL，请检查 MySQL 服务是否启动
    pause
    exit /b 1
)

REM 创建数据库
mysql -u root -p7842zc -e "CREATE DATABASE IF NOT EXISTS trade_system_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

REM 创建数据表
python -c "from app.database import engine, Base; from app import models; Base.metadata.create_all(bind=engine)"

echo.
echo 数据库初始化完成！
echo 数据库: trade_system_db@localhost:3306
echo.
echo 请确保 config.yaml 中 database.type 设为 mysql
pause
