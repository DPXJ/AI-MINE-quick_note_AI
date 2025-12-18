@echo off
chcp 65001 >nul
title QuickNote AI - 调试日志模式

REM 调试模式：保留控制台输出，便于看报错/日志
REM 关闭该窗口会退出程序（用于调试时主动结束）

cd /d "%~dp0"
set PYTHONPATH=%CD%

echo ========================================
echo QuickNote AI - 调试日志模式
echo ========================================
echo [提示] 关闭窗口/按 Ctrl+C 会退出程序
echo [提示] 文件日志仍会写入 logs\quicknote_*.log
echo ========================================
echo.

python src/main.py

echo.
echo ========================================
echo 程序已退出（如需后台运行请用：启动_后台运行.bat）
echo ========================================
pause


