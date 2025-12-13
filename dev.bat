@echo off
REM 开发调试脚本 - 快速启动并显示详细信息

echo ========================================
echo QuickNote AI - 开发调试模式
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查Python
python --version
if errorlevel 1 (
    echo [错误] Python未安装或不在PATH中
    pause
    exit /b 1
)

REM 显示当前配置信息
echo [信息] 当前工作目录: %CD%
echo [信息] Python路径: 
where python
echo.

REM 直接运行主程序（会显示完整错误信息）
echo [启动] 正在启动程序...
echo [提示] 按 Ctrl+C 停止程序
echo ========================================
echo.

REM 设置PYTHONPATH并运行
set PYTHONPATH=%CD%
python -c "import sys; sys.path.insert(0, '.'); from src.main import main; main()"

echo.
echo ========================================
echo 程序已退出
echo ========================================
pause

