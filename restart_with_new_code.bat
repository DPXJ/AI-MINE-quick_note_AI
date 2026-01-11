@echo off
chcp 65001 >nul
echo ================================
echo QuickNote AI - 重启程序（加载新代码）
echo ================================
echo.

REM 停止旧程序
echo [1/2] 停止旧程序...
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM 启动新程序
echo [2/2] 启动新程序...
set PYTHONPATH=%~dp0
start "" /D "%~dp0" pythonw src\main.py

echo.
echo ================================
echo 重启完成！新代码已生效
echo ================================
echo [提示] Flomo 预检查已更新为 500 字上限
echo [提示] 超过 500 字的长文本不会同步到 flomo
echo ================================
pause
