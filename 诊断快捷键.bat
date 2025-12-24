@echo off
chcp 65001 >nul
echo ========================================
echo QuickNote AI 快捷键诊断工具
echo ========================================
echo.
echo 此工具将启动应用并显示详细的调试日志
echo 请按下快捷键（Ctrl+Shift+Space）并观察日志输出
echo.
echo 日志位置: logs 文件夹
echo.
echo 按任意键开始...
pause >nul

echo.
echo 正在启动应用（调试模式）...
echo.

python src\main.py

pause
