@echo off
chcp 65001 >nul
title QuickNote AI - 一键打包工具

echo ╔══════════════════════════════════════════╗
echo ║      QuickNote AI - 一键打包工具         ║
echo ╚══════════════════════════════════════════╝
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/5] 检查 Python 环境...
python --version
echo.

REM 检查依赖
echo [2/5] 检查依赖包...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [提示] 未安装 PyInstaller，正在安装...
    pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败
        pause
        exit /b 1
    )
    echo [成功] PyInstaller 安装完成
) else (
    echo [成功] PyInstaller 已安装
)
echo.

REM 检查 build.spec 是否存在
echo [3/5] 检查配置文件...
if not exist "build.spec" (
    echo [错误] 未找到 build.spec 文件
    echo [提示] 请确保在项目根目录运行此脚本
    pause
    exit /b 1
)
echo [成功] 配置文件存在
echo.

REM 清理旧文件
echo [4/5] 清理旧文件...
if exist "build" (
    echo [清理] 删除 build 目录...
    rmdir /s /q "build"
)
if exist "dist" (
    echo [清理] 删除 dist 目录...
    rmdir /s /q "dist"
)
echo [成功] 清理完成
echo.

REM 开始打包
echo [5/5] 开始打包...
echo ============================================
echo 打包过程需要 2-5 分钟，请耐心等待...
echo ============================================
echo.

pyinstaller build.spec

REM 检查打包结果
echo.
echo ============================================
echo 检查打包结果...
echo ============================================
echo.

if exist "dist\QuickNote_AI\QuickNote_AI.exe" (
    echo [成功] 打包完成！
    echo.
    echo 文件位置: dist\QuickNote_AI\QuickNote_AI.exe
    echo.
    
    REM 计算文件大小
    for %%A in ("dist\QuickNote_AI\QuickNote_AI.exe") do set size=%%~zA
    set /a sizeMB=%size% / 1048576
    echo 文件大小: 约 %sizeMB% MB
    echo.
    
    echo ╔══════════════════════════════════════════╗
    echo ║              使用说明                     ║
    echo ╚══════════════════════════════════════════╝
    echo.
    echo 1. 在 dist\QuickNote_AI\ 目录下找到 QuickNote_AI.exe
    echo 2. 将 .env 和 config.yaml 文件复制到 exe 同目录下
    echo 3. 双击运行 QuickNote_AI.exe
    echo 4. 程序会最小化到系统托盘
    echo.
    echo [提示] 按任意键打开输出目录...
    pause >nul
    explorer "dist\QuickNote_AI\"
) else (
    echo [失败] 打包失败，未找到可执行文件
    echo.
    echo 可能的原因:
    echo 1. 依赖包未正确安装
    echo 2. build.spec 配置有误
    echo 3. 源代码存在语法错误
    echo.
    echo 请查看上面的错误信息，或运行 build.bat 查看详细日志
    echo.
    pause
    exit /b 1
)

pause

