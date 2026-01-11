@echo off
chcp 65001 >nul
title QuickNote AI - 后台运行（带日志窗口）

REM 切换到脚本所在目录（项目根目录）
cd /d "%~dp0"

if not exist ".env" (
    echo [错误] 未找到 .env 文件。
    echo [提示] 请先运行 “启动.bat” 完成首次配置。
    pause
    exit /b 1
)

where pythonw >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 pythonw.exe。
    echo [提示] 临时方案：使用 “启动_调试日志.bat” 启动（会显示控制台）。
    pause
    exit /b 1
)

REM 1) 先后台启动主程序（关掉本窗口不影响程序）
set PYTHONPATH=%CD%
start "" /D "%CD%" pythonw src/main.py

REM 2) 等待日志文件生成
if not exist "logs" mkdir logs
timeout /t 1 >nul

REM 3) 找到最新日志文件（quicknote_*.log）
set "LATEST_LOG="
for /f "delims=" %%F in ('dir /b /a-d /o-d "logs\quicknote_*.log" 2^>nul') do (
    set "LATEST_LOG=%%F"
    goto :found
)
:found

if not defined LATEST_LOG (
    echo [提示] 未找到日志文件，可能刚启动还没写入，稍后在 logs\ 目录查看。
    exit /b 0
)

REM 4) 打开一个独立日志窗口（你可以随时关闭该窗口，不影响主程序运行）
start "QuickNote AI - 实时日志（可关闭）" cmd /k powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Write-Host 'Tailing logs\\%LATEST_LOG% (close window anytime)...' -ForegroundColor Cyan; " ^
    "Get-Content -Path (Join-Path $PWD 'logs\\%LATEST_LOG%') -Tail 200 -Wait"

exit /b 0


