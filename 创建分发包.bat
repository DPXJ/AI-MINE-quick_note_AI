@echo off
chcp 65001 >nul
title QuickNote AI - 创建分发压缩包

echo ╔══════════════════════════════════════════╗
echo ║   QuickNote AI - 创建分发压缩包          ║
echo ╚══════════════════════════════════════════╝
echo.

REM 检查是否已打包
if not exist "dist\QuickNote_AI_v" (
    echo [提示] 未找到已打包的程序，正在开始打包...
    echo.
    call "一键打包.bat"
    if errorlevel 1 (
        echo [错误] 打包失败，无法创建分发包
        pause
        exit /b 1
    )
    echo.
    echo [继续] 打包完成，继续创建分发包...
    echo.
)

REM 查找最新的打包版本
set LATEST_VERSION=
for /f "tokens=*" %%i in ('dir /b /ad "dist\QuickNote_AI_v*" 2^>nul ^| sort /r') do (
    set LATEST_VERSION=%%i
    goto :found_version
)

:found_version
if "%LATEST_VERSION%"=="" (
    echo [错误] 未找到已打包的程序
    echo [提示] 请先运行 一键打包.bat 进行打包
    pause
    exit /b 1
)

echo [检测] 找到最新版本: %LATEST_VERSION%
echo.

REM 创建分发目录
set DIST_DIR=dist\分发包_%LATEST_VERSION%
echo [1/5] 创建分发目录...
if exist "%DIST_DIR%" (
    echo [清理] 删除旧的分发目录...
    rmdir /s /q "%DIST_DIR%"
)
mkdir "%DIST_DIR%"
echo [成功] 分发目录已创建
echo.

REM 复制程序文件
echo [2/5] 复制程序文件...
xcopy /E /I /Y "dist\%LATEST_VERSION%\*" "%DIST_DIR%\%LATEST_VERSION%\"
if errorlevel 1 (
    echo [错误] 复制程序文件失败
    pause
    exit /b 1
)
echo [成功] 程序文件已复制
echo.

REM 复制配置文件模板
echo [3/5] 复制配置文件模板...
copy /Y "config.yaml" "%DIST_DIR%\config.yaml.example" >nul
copy /Y "env.example" "%DIST_DIR%\.env.example" >nul
echo [成功] 配置文件模板已复制
echo.

REM 创建使用说明
echo [4/5] 创建使用说明...
(
echo # QuickNote AI - 快速开始指南
echo.
echo ## 📦 文件说明
echo.
echo - `%LATEST_VERSION%\` - 主程序文件夹（包含所有运行文件）
echo - `config.yaml.example` - 配置文件模板（复制为 config.yaml 并修改）
echo - `.env.example` - 环境变量配置模板（复制为 .env 并填入你的API密钥）
echo.
echo ## 🚀 快速开始
echo.
echo ### 第一步：运行程序
echo.
echo 1. 进入 `%LATEST_VERSION%\` 文件夹
echo 2. 双击 `QuickNote_AI_v*.exe` 运行程序
echo 3. 程序会最小化到系统托盘（任务栏右下角）
echo 4. 右键托盘图标 → 选择"设置"打开配置界面
echo.
echo ### 第二步：配置API密钥（通过设置界面）
echo.
echo **无需提前配置！** 程序可以在没有配置文件的情况下启动。
echo.
echo 1. 右键系统托盘图标 → 选择"设置"
echo 2. 在设置界面中填入你的API密钥：
echo    - **AI配置**：`OPENAI_API_KEY` - DeepSeek或其他OpenAI兼容API的密钥
echo    - **Notion配置**：`NOTION_API_KEY` 和 `NOTION_DATABASE_ID`（可选）
echo    - **Flomo配置**：`FLOMO_API_URL`（可选）
echo    - **TickTick配置**：`TICKTICK_WEBHOOK_URL`（可选）
echo 3. 点击"保存"按钮，配置会自动保存到 `.env` 和 `config.yaml` 文件
echo 4. 配置完成后，相关功能即可使用
echo.
echo **注意**：如果配置文件不存在，程序会自动创建。你也可以参考 `config.yaml.example` 和 `.env.example` 手动创建配置文件。
echo.
echo ## ⌨️ 快捷键
echo.
echo - `Ctrl+Shift+Space` - 打开快速输入窗口
echo - `Ctrl+Shift+C` - 开启/关闭剪切板自动同步
echo.
echo ## ⚙️ 功能说明
echo.
echo ### 快速输入
echo.
echo 按 `Ctrl+Shift+Space` 打开快速输入窗口，支持：
echo - **Notion**：状态、优先级、标签
echo - **Flomo**：标签
echo - **TickTick**：自动识别时间并设置提醒
echo.
echo ### 剪切板自动同步
echo.
echo 开启后，复制的内容会自动识别并同步到对应平台：
echo - 包含时间信息的任务 → TickTick
echo - 知识、金句、方法论 → Flomo
echo - 待办、灵感 → Notion
echo.
echo ## 🔧 常见问题
echo.
echo ### Q1: 程序无法启动
echo.
echo **解决方法**：
echo 1. 安装 [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
echo 2. 确保程序路径中没有中文字符
echo 3. 以管理员身份运行（全局快捷键需要管理员权限）
echo.
echo ### Q2: 快捷键不工作
echo.
echo **解决方法**：
echo 1. 以管理员身份运行程序
echo 2. 检查快捷键是否与其他程序冲突
echo 3. 在设置中重新设置快捷键
echo.
echo ### Q3: API连接失败
echo.
echo **解决方法**：
echo 1. 检查 `.env` 文件中的API密钥是否正确
echo 2. 检查网络连接
echo 3. 检查防火墙设置
echo.
echo ## 📝 注意事项
echo.
echo 1. **不要删除 `_internal` 文件夹**：这是程序运行必需的依赖文件
echo 2. **路径建议**：避免使用包含中文字符的路径
echo 3. **管理员权限**：全局快捷键功能需要管理员权限
echo 4. **配置文件**：可以通过设置界面配置，程序会自动创建 `.env` 和 `config.yaml` 文件
echo.
echo ## 🆘 技术支持
echo.
echo 如果遇到问题：
echo 1. 查看 `logs` 文件夹中的日志文件
echo 2. 确保已安装 Visual C++ Redistributable
echo 3. 尝试以管理员身份运行
echo 4. 检查配置文件是否正确
echo.
echo 祝使用愉快！🎉
) > "%DIST_DIR%\README.md"
echo [成功] 使用说明已创建
echo.

REM 创建压缩包
echo [5/5] 创建压缩包...
set ZIP_NAME=QuickNote_AI_分发包_%LATEST_VERSION%.zip
set ZIP_PATH=dist\%ZIP_NAME%

REM 删除旧压缩包
if exist "%ZIP_PATH%" del /F /Q "%ZIP_PATH%"

REM 使用 PowerShell 创建 ZIP 压缩包
powershell -Command "$zip='dist\%ZIP_NAME%'; $src='%DIST_DIR%\*'; Compress-Archive -Path $src -DestinationPath $zip -Force"

if exist "%ZIP_PATH%" (
    echo [成功] 压缩包已创建！
    echo.
    echo ╔══════════════════════════════════════════╗
    echo ║           打包完成！                     ║
    echo ╚══════════════════════════════════════════╝
    echo.
    echo 压缩包位置: %ZIP_PATH%
    echo.
    REM 计算压缩包大小
    for %%A in ("%ZIP_PATH%") do set zipsize=%%~zA
    set /a zipMB=%zipsize% / 1048576
    echo 压缩包大小: 约 %zipMB% MB
    echo.
    echo ╔══════════════════════════════════════════╗
    echo ║           分发说明                       ║
    echo ╚══════════════════════════════════════════╝
    echo.
    echo ✅ 压缩包已创建: %ZIP_NAME%
    echo ✅ 可以直接发送给其他用户
    echo ✅ 用户解压后即可使用（无需安装 Python）
    echo ✅ 包含完整的使用说明和配置模板
    echo.
    echo [提示] 按任意键打开输出目录...
    pause >nul
    explorer "dist\"
) else (
    echo [错误] 压缩包创建失败
    echo [提示] 可以手动压缩 %DIST_DIR% 文件夹
    pause
)

