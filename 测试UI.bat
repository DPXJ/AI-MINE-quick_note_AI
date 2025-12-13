@echo off
chcp 65001 >nul
echo ================================
echo QuickNote AI - UI测试
echo ================================
echo.

set PYTHONPATH=%~dp0

echo 请选择测试项：
echo 1. 快速输入窗口
echo 2. 设置窗口
echo.

set /p choice=请输入选择 (1/2): 

if "%choice%"=="1" (
    echo.
    echo 正在启动快速输入窗口测试...
    python test_ui.py
    echo 1
) else if "%choice%"=="2" (
    echo.
    echo 正在启动设置窗口测试...
    python test_ui.py
    echo 2
) else (
    echo 无效选择
)

echo.
pause

