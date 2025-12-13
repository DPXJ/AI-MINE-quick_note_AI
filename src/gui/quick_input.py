"""快速输入窗口"""
from PyQt5.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QFont, QColor, QPalette, QKeyEvent, QMouseEvent
from loguru import logger


class CustomTextEdit(QTextEdit):
    """自定义文本编辑器，修复按键处理"""
    
    # 信号
    submit_requested = pyqtSignal()
    cancel_requested = pyqtSignal()
    
    def keyPressEvent(self, event: QKeyEvent):
        """按键事件处理"""
        # Enter: 提交（不是Ctrl+Enter）
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if not (event.modifiers() & Qt.ControlModifier):
                # 提交内容
                self.submit_requested.emit()
                event.accept()
                return
        # Esc: 取消
        elif event.key() == Qt.Key_Escape:
            self.cancel_requested.emit()
            event.accept()
            return
        
        # 其他按键正常处理（包括Backspace、Delete等）
        super().keyPressEvent(event)


class QuickInputWindow(QWidget):
    """快速输入窗口"""
    
    # 信号：内容提交
    content_submitted = pyqtSignal(str)
    
    def __init__(self, config: dict):
        """
        初始化快速输入窗口
        
        Args:
            config: UI配置
        """
        super().__init__()
        self.config = config
        self.drag_position = None  # 用于拖动窗口
        self._init_ui()
        logger.info("快速输入窗口已初始化")
    
    def _init_ui(self):
        """初始化UI"""
        # 禁用DPI缩放影响
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        # 窗口属性
        self.setWindowTitle("QuickNote - 快速输入")
        
        # 窗口标志：无边框、非置顶、普通窗口（可最小化）
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Window  # 普通窗口，可以最小化
        )
        
        # 窗口大小（固定物理像素）
        width = 900  # 固定宽度
        height = 450  # 固定高度
        
        self.setFixedSize(width, height)
        # 不设置透明度，保持完全不透明
        self.setWindowOpacity(1.0)
        
        # 主题颜色
        bg_color = "#ffffff"
        fg_color = "#333333"
        accent_color = "#007acc"
        border_color = "#d0d0d0"
        
        # 主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题栏（可拖动）
        title_bar = QWidget()
        title_bar.setStyleSheet(f"""
            QWidget {{
                background: {accent_color};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
        """)
        title_bar.setFixedHeight(50)
        title_bar.mousePressEvent = self._title_bar_mouse_press
        title_bar.mouseMoveEvent = self._title_bar_mouse_move
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(20, 0, 20, 0)
        
        # 标题
        self.title_label = QLabel("💡 快速输入灵感")
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            }
        """)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        # 最小化按钮
        minimize_btn = QPushButton("─")
        minimize_btn.setFixedSize(40, 40)
        minimize_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(minimize_btn)
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(40, 40)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self._cancel)
        title_layout.addWidget(close_btn)
        
        title_bar.setLayout(title_layout)
        layout.addWidget(title_bar)
        
        # 内容区域
        content_widget = QWidget()
        content_widget.setStyleSheet(f"""
            QWidget {{
                background: {bg_color};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
        """)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 15, 20, 15)
        content_layout.setSpacing(15)
        
        # 输入框
        self.text_edit = CustomTextEdit()  # 使用自定义的TextEdit
        self.text_edit.setPlaceholderText("输入你的灵感...")
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg_color};
                color: {fg_color};
                border: 2px solid {border_color};
                border-radius: 6px;
                padding: 15px;
                font-size: 16px;
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
                line-height: 1.8;
            }}
            QTextEdit:focus {{
                border: 2px solid {accent_color};
            }}
        """)
        # 连接自定义信号
        self.text_edit.submit_requested.connect(self._submit_content)
        self.text_edit.cancel_requested.connect(self._cancel)
        content_layout.addWidget(self.text_edit, stretch=1)
        
        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 提示标签
        hint_label = QLabel("💡 Enter发送 | Ctrl+Enter换行 | Esc取消")
        hint_label.setStyleSheet(f"""
            QLabel {{
                color: #999;
                font-size: 13px;
                padding: 5px;
            }}
        """)
        button_layout.addWidget(hint_label)
        button_layout.addStretch()
        
        # 取消按钮
        cancel_btn = QPushButton("✕ 取消")
        cancel_btn.setFixedSize(100, 40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0;
                color: #666;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e0e0e0;
                border: 1px solid #b0b0b0;
            }
        """)
        cancel_btn.clicked.connect(self._cancel)
        button_layout.addWidget(cancel_btn)
        
        # 发送按钮
        send_btn = QPushButton("📤 发送")
        send_btn.setFixedSize(100, 40)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent_color};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #005a9e;
            }}
            QPushButton:pressed {{
                background: #004578;
            }}
        """)
        send_btn.clicked.connect(self._submit_content)
        button_layout.addWidget(send_btn)
        
        content_layout.addLayout(button_layout)
        content_widget.setLayout(content_layout)
        layout.addWidget(content_widget)
        
        self.setLayout(layout)
        
        # 设置窗口圆角和阴影效果
        self.setStyleSheet("""
            QuickInputWindow {
                border-radius: 8px;
            }
        """)
    
    def _title_bar_mouse_press(self, event: QMouseEvent):
        """标题栏鼠标按下事件（开始拖动）"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def _title_bar_mouse_move(self, event: QMouseEvent):
        """标题栏鼠标移动事件（拖动窗口）"""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def show_at_center(self):
        """显示在屏幕中央"""
        # 获取屏幕几何信息（主屏幕）
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        
        # 计算中心位置
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        
        # 聚焦到输入框
        QTimer.singleShot(100, lambda: self.text_edit.setFocus())
        
        logger.info("快速输入窗口已显示")
    
    
    def keyPressEvent(self, event: QKeyEvent):
        """窗口按键事件（用于Esc键等）"""
        if event.key() == Qt.Key_Escape:
            self._cancel()
        else:
            super().keyPressEvent(event)
    
    def _submit_content(self):
        """提交内容"""
        content = self.text_edit.toPlainText().strip()
        
        if content:
            logger.info(f"提交内容: {content[:50]}...")
            self.content_submitted.emit(content)
            self.text_edit.clear()
            self.hide()
        else:
            logger.warning("内容为空，不提交")
    
    def _cancel(self):
        """取消输入"""
        self.text_edit.clear()
        self.hide()
        logger.info("用户取消输入")
    
    def focusOutEvent(self, event):
        """失去焦点时不自动隐藏（用户可能需要切换窗口）"""
        # 不再自动隐藏，让用户主动关闭
        super().focusOutEvent(event)
