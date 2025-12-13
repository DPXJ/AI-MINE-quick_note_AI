"""QuickNote AI - 主程序入口"""
import sys
import os
from pathlib import Path

# 确保项目根目录在Python路径中
_current_dir = Path(__file__).parent.parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, QThread, Qt
from loguru import logger

# 配置日志
logger.add(
    "logs/quicknote_{time}.log",
    rotation="10 MB",
    retention="7 days",
    encoding="utf-8",
    enqueue=True
)

from src.utils.config import config
from src.gui.quick_input import QuickInputWindow
from src.gui.tray_icon import TrayIcon
from src.gui.settings import SettingsDialog
from src.core.hotkey import HotkeyListener
from src.core.clipboard import ClipboardMonitor
from src.core.ai_processor import AIProcessor
from src.integrations.notion_api import NotionAPI
from src.integrations.flomo_api import FlomoAPI


class QuickNoteApp(QObject):
    """主应用程序类"""
    
    def __init__(self, app: QApplication):
        """初始化应用"""
        super().__init__()
        self.app = app
        
        logger.info("=" * 50)
        logger.info("QuickNote AI 启动中...")
        logger.info("=" * 50)
        
        # 验证配置（允许通过设置界面配置，不强制退出）
        if not config.validate():
            logger.warning("配置验证失败，将在设置界面中配置")
            # 不强制退出，允许用户通过设置界面配置
            # 后续在使用时会再次验证
        
        # 初始化组件
        self._init_components()
        self._connect_signals()
        
        logger.info("QuickNote AI 启动完成")
    
    def _init_components(self):
        """初始化所有组件"""
        try:
            # GUI组件
            ui_config = config.get("ui.quick_input", {})
            self.quick_input_window = QuickInputWindow(ui_config)
            self.tray_icon = TrayIcon(self.app)
            self.settings_dialog = None
            
            # 快捷键监听器
            self.hotkey_listener = HotkeyListener()
            self.hotkey_listener.register(
                config.hotkey_quick_input,
                self._show_quick_input
            )
            self.hotkey_listener.register(
                config.hotkey_toggle_clipboard,
                self._toggle_clipboard
            )
            self.hotkey_listener.start()
            
            # API集成
            self.notion_api = NotionAPI(
                config.notion_api_key,
                config.notion_database_id
            )
            
            self.flomo_api = None
            if config.flomo_api_url:
                self.flomo_api = FlomoAPI(config.flomo_api_url)
            
            # AI处理器
            self.ai_processor = AIProcessor(config.ai_provider)
            
            # 剪切板监控
            self.clipboard_monitor = ClipboardMonitor(
                callback=self._on_clipboard_content,
                check_interval=config.clipboard_check_interval,
                min_length=config.clipboard_min_length,
                max_length=config.clipboard_max_length
            )
            
            # 如果配置启用，则启动剪切板监控
            if config.clipboard_enabled:
                self.clipboard_monitor.start()
            
            logger.info("所有组件初始化完成")
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 快速输入窗口
        self.quick_input_window.content_submitted.connect(self._on_quick_input_submitted)
        
        # 系统托盘
        self.tray_icon.quick_input_triggered.connect(self._show_quick_input)
        self.tray_icon.settings_triggered.connect(self._show_settings)
        self.tray_icon.quit_triggered.connect(self._quit_app)
        self.tray_icon.restart_triggered.connect(self._restart_app)
        self.tray_icon.clipboard_toggled.connect(self._on_clipboard_toggled)
        
        # 设置保存后重新初始化
        if self.settings_dialog:
            self.settings_dialog.settings_saved.connect(self._reload_config)
    
    def _show_quick_input(self):
        """显示快速输入窗口"""
        logger.info("显示快速输入窗口")
        self.quick_input_window.show_at_center()
    
    def _show_settings(self):
        """显示设置界面"""
        logger.info("显示设置界面")
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(config)
            self.settings_dialog.settings_saved.connect(self._reload_config)
        self.settings_dialog.exec_()
    
    def _reload_config(self):
        """重新加载配置（设置保存后）"""
        logger.info("重新加载配置")
        from src.utils.config import config as new_config
        
        # 重新加载环境变量和YAML配置
        if new_config.env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(new_config.env_file, override=True)
        
        # 重新加载YAML配置
        new_config.config = new_config._load_config()
        
        # 重新初始化API
        try:
            if new_config.validate():
                self.ai_processor = AIProcessor(new_config.ai_provider)
                logger.info("AI处理器已重新初始化")
            
            if new_config.notion_api_key and new_config.notion_database_id:
                self.notion_api = NotionAPI(
                    new_config.notion_api_key,
                    new_config.notion_database_id
                )
                logger.info("Notion API已重新初始化")
            
            if new_config.flomo_api_url:
                self.flomo_api = FlomoAPI(new_config.flomo_api_url)
                logger.info("Flomo API已重新初始化")
            
            # 快捷键配置已保存到config.yaml，但需要重启才能生效
            logger.info("快捷键配置已更新，需要重启应用才能生效")
            
            self.tray_icon.show_message("配置已更新", "设置已保存并重新加载 ✅\n⚠️ 快捷键需重启生效")
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            self.tray_icon.show_message("配置更新失败", f"请检查配置: {str(e)}")
    
    def _toggle_clipboard(self):
        """切换剪切板监控"""
        enabled = self.clipboard_monitor.toggle()
        self.tray_icon.set_clipboard_status(enabled)
        
        status = "已开启" if enabled else "已关闭"
        self.tray_icon.show_message("剪切板监控", f"剪切板监控{status}")
    
    def _on_clipboard_toggled(self, enabled: bool):
        """剪切板监控切换事件"""
        if enabled:
            self.clipboard_monitor.start()
        else:
            self.clipboard_monitor.stop()
    
    def _on_quick_input_submitted(self, content: str):
        """处理快速输入的内容"""
        logger.info(f"收到快速输入: {content[:50]}...")
        
        if not self.notion_api:
            self.tray_icon.show_message("配置错误", "请先在设置界面配置Notion API")
            logger.error("Notion API未初始化")
            return
        
        # 显示处理中的提示
        self.tray_icon.show_message("处理中", "正在保存到Notion...")
        
        # 保存到Notion
        success = self.notion_api.add_inspiration(content)
        
        if success:
            self.tray_icon.show_message("保存成功", "灵感已保存到Notion ✅")
            logger.info("快速输入已保存到Notion")
        else:
            self.tray_icon.show_message("保存失败", "保存到Notion失败 ❌")
            logger.error("保存到Notion失败")
    
    def _on_clipboard_content(self, content: str):
        """处理剪切板内容"""
        logger.info(f"检测到剪切板内容: {content[:50]}...")
        
        if not self.ai_processor:
            logger.warning("AI处理器未初始化，跳过剪切板内容处理")
            return
        
        try:
            # AI识别
            result = self.ai_processor.classify_content(content)
            
            if not result.get("valuable"):
                logger.info("内容不符合保存规则，已忽略")
                return
            
            target_type = result.get("type")
            
            # 根据类型分流
            if target_type == "notion":
                # 保存到Notion
                title = result.get("title")
                priority = result.get("priority", "中")
                
                success = self.notion_api.add_inspiration(
                    content,
                    title=title,
                    priority=priority
                )
                
                if success:
                    self.tray_icon.show_message(
                        "已保存到Notion",
                        f"{title or content[:30]}"
                    )
                    logger.info("剪切板内容已保存到Notion")
                
            elif target_type == "flomo" and self.flomo_api:
                # 保存到Flomo
                category = result.get("category")
                tags = result.get("tags", [])
                if category and category not in tags:
                    tags.insert(0, category)
                
                success = self.flomo_api.add_memo(content, tags=tags)
                
                if success:
                    self.tray_icon.show_message(
                        "已保存到Flomo",
                        f"{content[:30]}..."
                    )
                    logger.info("剪切板内容已保存到Flomo")
            
        except Exception as e:
            logger.error(f"处理剪切板内容失败: {e}")
    
    def _restart_app(self):
        """重启应用"""
        import subprocess
        import os
        import sys
        from pathlib import Path
        
        logger.info("正在重启应用...")
        
        # 获取当前脚本路径
        current_dir = Path(__file__).parent.parent
        script_path = current_dir / "src" / "main.py"
        
        # 获取Python解释器路径
        python_exe = sys.executable
        
        # 停止所有服务
        self.clipboard_monitor.stop()
        self.hotkey_listener.stop()
        
        # 显示重启提示
        self.tray_icon.show_message("正在重启", "QuickNote AI 正在重启...")
        
        # 延迟一点再启动新进程，确保当前进程完全退出
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(500, lambda: self._do_restart(python_exe, script_path, current_dir))
        
        # 退出当前应用
        self.app.quit()
    
    def _do_restart(self, python_exe, script_path, current_dir):
        """执行重启操作"""
        import subprocess
        import os
        
        try:
            # 切换到项目目录
            os.chdir(str(current_dir))
            
            # 启动新进程
            subprocess.Popen(
                [python_exe, "-c", "import sys; sys.path.insert(0, '.'); from src.main import main; main()"],
                cwd=str(current_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            logger.info("新进程已启动")
        except Exception as e:
            logger.error(f"重启失败: {e}")
    
    def _quit_app(self):
        """退出应用"""
        logger.info("正在退出应用...")
        
        # 停止所有服务
        self.clipboard_monitor.stop()
        self.hotkey_listener.stop()
        
        # 退出应用
        self.app.quit()
        
        logger.info("应用已退出")


def main():
    """主函数"""
    # 设置高DPI支持（在创建QApplication之前）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("QuickNote AI")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出
    
    try:
        # 创建主应用实例
        quick_note = QuickNoteApp(app)
        
        # 显示启动成功提示
        quick_note.tray_icon.show_message(
            "QuickNote AI",
            "已启动！使用 Ctrl+Shift+Space 快速输入"
        )
        
        # 运行应用
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"应用运行异常: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "运行错误",
            f"应用运行时发生错误：\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

