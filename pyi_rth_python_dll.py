"""
PyInstaller 运行时钩子：确保 Python DLL 能被正确加载
"""
import os
import sys
from pathlib import Path

# 如果是打包后的 EXE，确保 _internal 目录在 DLL 搜索路径中
if getattr(sys, 'frozen', False):
    # 获取 EXE 所在目录
    exe_dir = Path(sys.executable).parent
    
    # _internal 目录路径
    internal_dir = exe_dir / '_internal'
    
    # 将 _internal 目录添加到 DLL 搜索路径
    if internal_dir.exists():
        os.add_dll_directory(str(internal_dir))
        
        # 同时添加到 PATH（备用方案）
        current_path = os.environ.get('PATH', '')
        if str(internal_dir) not in current_path:
            os.environ['PATH'] = str(internal_dir) + os.pathsep + current_path

