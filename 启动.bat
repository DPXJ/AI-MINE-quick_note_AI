@echo off
chcp 65001 >nul
echo ========================================
echo QuickNote AI - 启动程序
echo ========================================
echo.

REM 检查.env文件
if not exist .env (
    echo [提示] .env文件不存在，正在创建...
    python setup_and_run.py
    echo.
    echo ========================================
    echo 请先编辑 .env 文件，填入你的API密钥！
    echo ========================================
    pause
    exit /b
)

REM 运行程序
echo [启动] 正在启动 QuickNote AI...
echo.
python -c "import sys; sys.path.insert(0, '.'); from src.main import main; main()"

if errorlevel 1 (
    echo.
    echo ========================================
    echo 启动失败！
    echo ========================================
    echo.
    echo 请检查：
    echo 1. 是否安装了依赖: pip install -r requirements.txt
    echo 2. .env文件配置是否正确
    echo 3. 查看日志文件: logs\ 目录
    echo.
    pause
)

