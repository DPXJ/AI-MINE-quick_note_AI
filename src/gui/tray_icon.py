"""系统托盘图标"""
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QObject
from loguru import logger
import sys


class TrayIcon(QObject):
    """系统托盘图标"""
    
    # 信号
    quick_input_triggered = pyqtSignal()
    settings_triggered = pyqtSignal()
    quit_triggered = pyqtSignal()
    restart_triggered = pyqtSignal()
    clipboard_toggled = pyqtSignal(bool)
    clipboard_history_triggered = pyqtSignal()
    
    def __init__(self, app):
        """
        初始化系统托盘
        
        Args:
            app: QApplication实例
        """
        super().__init__()
        self.app = app
        self.tray_icon = None
        self.clipboard_enabled = True
        self._init_tray()
        logger.info("系统托盘已初始化")
    
    def _init_tray(self):
        """初始化托盘图标"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self.app)
        
        # 设置图标（使用默认图标，实际使用时应该替换）
        icon = self._create_icon()
        self.tray_icon.setIcon(icon)
        
        # 设置提示文本
        self.tray_icon.setToolTip("QuickNote AI - 智能笔记助手")
        
        # 创建菜单
        menu = QMenu()
        
        # 快速输入
        quick_input_action = QAction("📝 快速输入 (Ctrl+Shift+Space)", menu)
        quick_input_action.triggered.connect(self.quick_input_triggered.emit)
        menu.addAction(quick_input_action)
        
        menu.addSeparator()
        
        # 剪切板监控开关
        self.clipboard_action = QAction("✅ 剪切板监控", menu)
        self.clipboard_action.setCheckable(True)
        self.clipboard_action.setChecked(True)
        self.clipboard_action.triggered.connect(self._toggle_clipboard)
        menu.addAction(self.clipboard_action)
        
        menu.addSeparator()
        
        # 剪切板历史
        history_action = QAction("📋 剪切板历史", menu)
        history_action.triggered.connect(self.clipboard_history_triggered.emit)
        menu.addAction(history_action)
        
        # 设置
        settings_action = QAction("⚙️ 设置", menu)
        settings_action.triggered.connect(self.settings_triggered.emit)
        menu.addAction(settings_action)
        
        # 关于
        about_action = QAction("ℹ️ 关于", menu)
        about_action.triggered.connect(self._show_about)
        menu.addAction(about_action)
        
        menu.addSeparator()
        
        # 重启
        restart_action = QAction("🔄 重启", menu)
        restart_action.triggered.connect(self._restart_app)
        menu.addAction(restart_action)
        
        # 退出
        quit_action = QAction("❌ 退出", menu)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)
        
        # 设置菜单
        self.tray_icon.setContextMenu(menu)
        
        # 双击事件
        self.tray_icon.activated.connect(self._on_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
    
    def _create_icon(self):
        """创建托盘图标"""
        from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
        from PyQt5.QtCore import Qt
        
        # 创建一个简单的图标
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制圆形背景
        painter.setBrush(QColor("#007acc"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 60, 60)
        
        # 绘制文字
        painter.setPen(QColor("#ffffff"))
        font = QFont("Arial", 28, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "Q")
        
        painter.end()
        
        return QIcon(pixmap)
    
    def _on_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            # 双击打开快速输入
            self.quick_input_triggered.emit()
    
    def _toggle_clipboard(self, checked):
        """切换剪切板监控"""
        self.clipboard_enabled = checked
        status = "已开启" if checked else "已关闭"
        self.show_message("剪切板监控", f"剪切板监控{status}")
        self.clipboard_toggled.emit(checked)
        logger.info(f"剪切板监控{status}")
    
    def _show_about(self):
        """显示关于信息"""
        from PyQt5.QtWidgets import QMessageBox
        
        about_text = """
        <h2>QuickNote AI</h2>
        <p><b>版本:</b> 1.0.0</p>
        <p><b>功能:</b></p>
        <ul>
            <li>快捷键快速输入灵感</li>
            <li>智能剪切板监控</li>
            <li>自动同步到Notion和Flomo</li>
        </ul>
        <p><b>快捷键:</b></p>
        <ul>
            <li>Ctrl+Shift+Space: 快速输入</li>
            <li>Ctrl+Shift+C: 切换剪切板监控</li>
        </ul>
        <p style="color: #666;">让灵感不再溜走 💡</p>
        """
        
        msg_box = QMessageBox()
        msg_box.setWindowTitle("关于 QuickNote AI")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(about_text)
        msg_box.setIconPixmap(self._create_icon().pixmap(64, 64))
        msg_box.exec_()
    
    def _restart_app(self):
        """重启应用"""
        from PyQt5.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            None,
            "确认重启",
            "确定要重启 QuickNote AI 吗？\n\n程序将关闭并重新启动。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info("用户重启应用")
            self.restart_triggered.emit()
    
    def _quit_app(self):
        """退出应用"""
        from PyQt5.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            None,
            "确认退出",
            "确定要退出 QuickNote AI 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info("用户退出应用")
            self.quit_triggered.emit()
    
    def show_message(self, title: str, message: str, duration: int = 3000):
        """显示托盘消息"""
        self.tray_icon.showMessage(
            title,
            message,
            QSystemTrayIcon.Information,
            duration
        )
    
    def set_clipboard_status(self, enabled: bool):
        """设置剪切板监控状态"""
        self.clipboard_enabled = enabled
        self.clipboard_action.setChecked(enabled)

