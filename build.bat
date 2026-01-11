@echo off
REM QuickNote AI 打包脚本（Windows批处理）

echo ========================================
echo QuickNote AI - 打包工具
echo ========================================
echo.

REM 检查是否安装了依赖
echo [1/4] 检查依赖...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 错误: 未安装 PyInstaller
    echo 正在安装...
    pip install pyinstaller
)

REM 清理旧的构建文件
echo.
echo [2/4] 清理旧文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 执行打包
echo.
echo [3/4] 开始打包...
pyinstaller build.spec

REM 检查打包结果
echo.
echo [4/4] 检查打包结果...
if exist "dist\QuickNote_AI.exe" (
    echo.
    echo ========================================
    echo 打包成功！
    echo ========================================
    echo.
    echo 可执行文件位置: dist\QuickNote_AI.exe
    echo.
    echo 使用说明:
    echo 1. 在首次运行前，请确保 .env 文件配置正确
    echo 2. 将 .env 和 config.yaml 文件放在 exe 同目录下
    echo 3. 双击 QuickNote_AI.exe 运行
    echo.
) else (
    echo.
    echo ========================================
    echo 打包失败！
    echo ========================================
    echo.
    echo 请查看上面的错误信息
    echo.
)

pause

