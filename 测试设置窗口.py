"""测试设置窗口"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from src.gui.settings import SettingsDialog
from src.utils.config import config

def test_settings():
    """测试设置窗口"""
    app = QApplication(sys.argv)
    
    try:
        dialog = SettingsDialog(config)
        dialog.exec_()
    except Exception as e:
        import traceback
        print(f"错误: {e}")
        print(traceback.format_exc())
        input("按Enter键退出...")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_settings()


