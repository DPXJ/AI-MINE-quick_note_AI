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

REM 检测版本号并创建新版本（小版本号：V3.1, V3.2, V3.3...）
echo [4/6] 检测版本号...
set VERSION=3.1
set MAX_VERSION=

REM 使用 Python 检测 dist 目录下已有的版本号（支持 v3.1, v3.2 格式）
if exist "dist" (
    for /f "tokens=*" %%i in ('python -c "import os, re; dirs = [d for d in os.listdir('dist') if os.path.isdir(os.path.join('dist', d)) and d.startswith('QuickNote_AI_v')]; versions = [re.sub(r'QuickNote_AI_v', '', d) for d in dirs]; versions = [v for v in versions if re.match(r'^\d+\.\d+$', v)]; if versions: versions.sort(key=lambda x: [int(i) for i in x.split('.')]); print(versions[-1])"') do (
        set MAX_VERSION=%%i
    )
)

REM 如果找到已有版本，小版本号+0.1，否则从V3.1开始
if not "%MAX_VERSION%"=="" (
    REM 使用 Python 计算下一个版本号（支持 3.1 -> 3.2 这样的递增）
    for /f "tokens=*" %%j in ('python -c "v='%MAX_VERSION%'; parts=v.split('.'); parts[-1]=str(int(parts[-1])+1); print('.'.join(parts))"') do (
        set VERSION=%%j
    )
    echo [检测] 发现已有版本 V%MAX_VERSION%，将创建新版本 V%VERSION%
) else (
    echo [检测] 未发现已有版本，将创建 V%VERSION%
)
echo [版本] 本次打包版本: V%VERSION%
echo.

REM 清理 build 目录（保留 dist 以便检测版本）
echo [5/6] 清理 build 目录...
if exist "build" (
    echo [清理] 删除 build 目录...
    rmdir /s /q "build"
)
echo [成功] 清理完成
echo.

REM 使用 Python 脚本动态修改 build.spec 中的版本号（EXE名称和目录名称）
echo [6/6] 更新打包配置...
python -c "import re; content = open('build.spec', 'r', encoding='utf-8').read(); version='%VERSION%'; new_content = re.sub(r\"name='QuickNote_AI(_v[\d.]+)?'\", f\"name='QuickNote_AI_v{version}'\", content); new_content = re.sub(r\"name='QuickNote_AI_v[\d.]+\'\", f\"name='QuickNote_AI_v{version}'\", new_content); open('build.spec', 'w', encoding='utf-8').write(new_content); print(f'[成功] 已更新版本号为 V{version}')"
if errorlevel 1 (
    echo [警告] 无法自动更新版本号，将使用 build.spec 中的默认版本
    echo [提示] 请手动检查 build.spec 中的版本号设置
) else (
    echo [确认] EXE名称和目录名称已更新为 V%VERSION%
)
echo.

REM 开始打包
echo [打包] 开始打包 V%VERSION%...
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

set EXE_PATH=dist\QuickNote_AI_v%VERSION%\QuickNote_AI_v%VERSION%.exe
if exist "%EXE_PATH%" (
    echo [成功] 打包完成！
    echo.
    echo 版本: V%VERSION%
    echo 文件位置: %EXE_PATH%
    echo.
    
    REM 计算文件大小
    for %%A in ("%EXE_PATH%") do set size=%%~zA
    set /a sizeMB=%size% / 1048576
    echo 文件大小: 约 %sizeMB% MB
    echo.
    
    echo ╔══════════════════════════════════════════╗
    echo ║              使用说明                     ║
    echo ╚══════════════════════════════════════════╝
    echo.
    echo 1. 在 dist\QuickNote_AI_v%VERSION%\ 目录下找到 QuickNote_AI_v%VERSION%.exe
    echo 2. 将 .env 和 config.yaml 文件复制到 exe 同目录下
    echo 3. 双击运行 QuickNote_AI_v%VERSION%.exe
    echo 4. 程序会最小化到系统托盘
    echo.
    echo [提示] 按任意键打开输出目录...
    pause >nul
    explorer "dist\QuickNote_AI_v%VERSION%\"
) else (
    echo [失败] 打包失败，未找到可执行文件
    echo.
    echo 预期路径: %EXE_PATH%
    echo.
    echo 可能的原因:
    echo 1. 依赖包未正确安装
    echo 2. build.spec 配置有误
    echo 3. 源代码存在语法错误
    echo.
    echo 请查看上面的错误信息
    echo.
    pause
    exit /b 1
)

pause

