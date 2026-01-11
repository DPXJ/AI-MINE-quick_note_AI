@echo off
chcp 65001 >nul
title QuickNote AI - 快速测试

echo ========================================
echo   QuickNote AI - 快速测试
echo ========================================
echo.
echo 正在启动应用...
echo.

set PYTHONPATH=%~dp0

python src/main.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo   启动失败！
    echo ========================================
    echo.
    echo 可能的原因：
    echo 1. Python环境未安装
    echo 2. 依赖包未安装（运行 pip install -r requirements.txt）
    echo 3. 配置文件错误（检查 .env 和 config.yaml）
    echo.
    pause
) else (
    echo.
    echo 应用已正常退出
)

