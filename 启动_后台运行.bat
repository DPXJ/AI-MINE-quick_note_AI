@echo off
chcp 65001 >nul
title QuickNote AI - 后台运行

REM 切换到脚本所在目录（项目根目录）
cd /d "%~dp0"

REM 首次配置仍建议用“启动.bat”，这里做最小检查
if not exist ".env" (
    echo [错误] 未找到 .env 文件。
    echo [提示] 请先运行 “启动.bat” 完成首次配置（会提示你创建/编辑 .env）。
    pause
    exit /b 1
)

REM 尽量使用 pythonw（无控制台窗口），并用 start 脱离当前控制台
where pythonw >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 pythonw.exe（你的Python可能不完整或未加入PATH）。
    echo [提示] 请确认安装了 Windows 版 CPython，并能在命令行执行 pythonw。
    echo [提示] 临时方案：使用 “启动_调试日志.bat” 启动（会显示控制台）。
    pause
    exit /b 1
)

REM 后台启动（关闭本窗口不影响程序）
set PYTHONPATH=%CD%
start "" /D "%CD%" pythonw src/main.py

echo [OK] 已后台启动 QuickNote AI（无控制台窗口）。
echo [提示] 日志在 logs\quicknote_*.log
exit /b 0


