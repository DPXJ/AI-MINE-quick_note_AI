@echo off
chcp 65001 >nul
echo ========================================
echo QuickNote AI - keyboard 库测试
echo ========================================
echo.
echo 此工具将测试 keyboard 库是否正常工作
echo.
echo 按任意键开始测试...
pause >nul

python 测试keyboard库.py

pause
