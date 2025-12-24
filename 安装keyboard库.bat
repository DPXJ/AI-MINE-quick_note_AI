@echo off
chcp 65001 >nul
echo ========================================
echo 安装 keyboard 库
echo ========================================
echo.
echo 正在安装更稳定的快捷键库...
echo.

pip install keyboard>=0.13.5

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 现在可以运行应用了。
echo 快捷键将使用更稳定的 keyboard 库。
echo.
pause
