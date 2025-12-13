@echo off
REM QuickNote AI 运行脚本（开发模式）

echo ========================================
echo QuickNote AI - 启动中...
echo ========================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未安装 Python 或 Python 不在 PATH 中
    pause
    exit /b 1
)

REM 检查依赖
echo 检查依赖...
pip show PyQt5 >nul 2>&1
if errorlevel 1 (
    echo 未安装依赖，正在安装...
    pip install -r requirements.txt
)

REM 检查配置文件
if not exist ".env" (
    echo.
    echo 警告: .env 文件不存在！
    echo 请先复制 .env.example 为 .env 并填入配置信息
    echo.
    pause
    exit /b 1
)

REM 运行程序
echo.
echo 正在启动 QuickNote AI...
echo.

REM 设置PYTHONPATH并运行（确保能找到src模块）
set PYTHONPATH=%CD%
python -c "import sys; sys.path.insert(0, '.'); from src.main import main; main()"

REM 如果程序异常退出
if errorlevel 1 (
    echo.
    echo 程序异常退出，请查看错误信息
    pause
)

