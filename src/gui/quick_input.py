"""快速输入窗口"""
from PyQt5.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QGraphicsDropShadowEffect
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
    
    # 信号：内容提交（平台，内容，标签）
    content_submitted = pyqtSignal(str, str, str)  # platform, content, tags
    
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
        # 启用透明背景以支持圆角和阴影
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # 启用透明绘制
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        
        # 窗口属性
        self.setWindowTitle("QuickNote - 快速输入")
        
        # 窗口标志：无边框、普通窗口（可最小化）、保持在上层但不是置顶
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Window |  # 普通窗口，可以最小化
            Qt.WindowStaysOnTopHint |  # 保持在顶层，确保快捷键调用时可见
            Qt.X11BypassWindowManagerHint  # 绕过窗口管理器（Windows上无影响，但确保圆角正常）
        )
        
        # 窗口大小（固定物理像素，补偿外边距）
        width = 930  # 固定宽度（增加30以补偿边距）
        height = 530  # 增加高度以容纳Tab和边距
        
        self.setFixedSize(width, height)
        
        # 暗色 AI 主题颜色（柔和版本）
        bg_color = "#1a1a1a"  # 深黑色背景
        bg_secondary = "#242424"  # 次要背景
        bg_input = "#2d2d2d"  # 输入框背景
        fg_color = "#e8e8e8"  # 前景文字（浅色）
        fg_secondary = "#8a8a8a"  # 次要文字（降低亮度）
        accent_color = "#5eb8d9"  # 柔和的青蓝色（不刺眼）
        accent_secondary = "#4a9ec4"  # 次要强调色（更深）
        accent_glow = "#3d8fb3"  # 发光用的更深青色
        border_color = "#3a3a3a"  # 边框颜色
        glow_color = "rgba(94, 184, 217, 0.4)"  # 柔和的发光效果
        
        # 当前目标平台（默认Notion）
        self.target_platform = "notion"
        
        # 创建主容器（用于圆角和阴影）
        main_container = QWidget()
        main_container.setAttribute(Qt.WA_StyledBackground, True)
        main_container.setStyleSheet(f"""
            QWidget#main_container {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a1a, 
                    stop:1 #141414);
                border-radius: 20px;
                border: 1px solid rgba(94, 184, 217, 0.25);
            }}
        """)
        main_container.setObjectName("main_container")
        
        # 添加更强的阴影效果（AI 发光感 + 立体感）
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(80)  # 超大模糊半径，增强立体感
        shadow.setColor(QColor(94, 184, 217, 100))  # 柔和青色光晕
        shadow.setOffset(0, 15)  # 增大阴影偏移
        main_container.setGraphicsEffect(shadow)
        
        # 主布局
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题栏（可拖动）
        title_bar = QWidget()
        title_bar.setAttribute(Qt.WA_StyledBackground, True)
        title_bar.setStyleSheet(f"""
            QWidget#title_bar {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1f2a2e, 
                    stop:0.5 #1a252a,
                    stop:1 #1f2a2e);
                border: none;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom: 1px solid rgba(94, 184, 217, 0.2);
            }}
        """)
        title_bar.setObjectName("title_bar")
        title_bar.setFixedHeight(60)
        title_bar.mousePressEvent = self._title_bar_mouse_press
        title_bar.mouseMoveEvent = self._title_bar_mouse_move
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(20, 0, 20, 0)
        
        # 标题
        self.title_label = QLabel("💡 快速输入灵感")
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: #8db8d0;
                font-size: 17px;
                font-weight: 600;
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
                border: none;
                background: transparent;
            }}
        """)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        
        # 最小化按钮
        minimize_btn = QPushButton("─")
        minimize_btn.setFixedSize(40, 40)
        minimize_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {fg_secondary};
                border: none;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(0, 212, 255, 0.2);
                color: {accent_color};
                border-radius: 8px;
            }}
        """)
        minimize_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(minimize_btn)
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(40, 40)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {fg_secondary};
                border: none;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(255, 50, 50, 0.3);
                color: #ff5252;
                border-radius: 8px;
            }}
        """)
        close_btn.clicked.connect(self._cancel)
        title_layout.addWidget(close_btn)
        
        title_bar.setLayout(title_layout)
        layout.addWidget(title_bar)
        
        # 内容区域
        content_widget = QWidget()
        content_widget.setAttribute(Qt.WA_StyledBackground, True)  # 启用样式背景
        content_widget.setStyleSheet(f"""
            QWidget#content_widget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {bg_color}, 
                    stop:1 {bg_secondary});
                border: none;
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
            }}
        """)
        content_widget.setObjectName("content_widget")
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(20, 15, 20, 20)  # 增加底部边距到20px
        content_layout.setSpacing(15)
        
        # Tab切换按钮
        tab_layout = QHBoxLayout()
        tab_layout.setSpacing(10)
        
        self.notion_tab_btn = QPushButton("📝 Notion")
        self.notion_tab_btn.setCheckable(True)
        self.notion_tab_btn.setChecked(True)
        self.notion_tab_btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent_color};
                color: {bg_color};
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {accent_secondary};
            }}
            QPushButton:checked {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent_color}, stop:1 {accent_secondary});
                color: white;
                border: 2px solid {accent_color};
            }}
            QPushButton:!checked {{
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
            }}
        """)
        self.notion_tab_btn.clicked.connect(lambda: self._switch_platform("notion"))
        tab_layout.addWidget(self.notion_tab_btn)
        
        self.flomo_tab_btn = QPushButton("🏷️ Flomo")
        self.flomo_tab_btn.setCheckable(True)
        self.flomo_tab_btn.setChecked(False)
        self.flomo_tab_btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent_color};
                color: {bg_color};
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {accent_secondary};
            }}
            QPushButton:checked {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent_color}, stop:1 {accent_secondary});
                color: white;
                border: 2px solid {accent_color};
            }}
            QPushButton:!checked {{
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
            }}
        """)
        self.flomo_tab_btn.clicked.connect(lambda: self._switch_platform("flomo"))
        tab_layout.addWidget(self.flomo_tab_btn)
        
        self.ticktick_tab_btn = QPushButton("✅ 滴答清单")
        self.ticktick_tab_btn.setCheckable(True)
        self.ticktick_tab_btn.setChecked(False)
        self.ticktick_tab_btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent_color};
                color: {bg_color};
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {accent_secondary};
            }}
            QPushButton:checked {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent_color}, stop:1 {accent_secondary});
                color: white;
                border: 2px solid {accent_color};
            }}
            QPushButton:!checked {{
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
            }}
        """)
        self.ticktick_tab_btn.clicked.connect(lambda: self._switch_platform("ticktick"))
        tab_layout.addWidget(self.ticktick_tab_btn)
        
        # 标签输入（仅Flomo显示）
        self.tags_label = QLabel("标签（用空格分隔）：")
        self.tags_label.setStyleSheet(f"font-size: 13px; color: {fg_secondary};")
        self.tags_label.setVisible(False)
        
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("例如：产品 AI 方法论")
        self.tags_input.setText("闪念")  # 设置默认标签
        self.tags_input.setStyleSheet(f"""
            QLineEdit {{
                background: {bg_input};
                color: {fg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {accent_color};
                background: {bg_secondary};
            }}
            QLineEdit::placeholder {{
                color: {fg_secondary};
            }}
        """)
        self.tags_input.setVisible(False)
        
        # 清单名称输入（仅TickTick显示）
        self.list_name_label = QLabel("清单名称（可选）：")
        self.list_name_label.setStyleSheet(f"font-size: 13px; color: {fg_secondary};")
        self.list_name_label.setVisible(False)
        
        self.list_name_input = QLineEdit()
        self.list_name_input.setPlaceholderText("例如：工作、生活（不填则使用默认清单）")
        self.list_name_input.setStyleSheet(f"""
            QLineEdit {{
                background: {bg_input};
                color: {fg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {accent_color};
                background: {bg_secondary};
            }}
            QLineEdit::placeholder {{
                color: {fg_secondary};
            }}
        """)
        self.list_name_input.setVisible(False)
        
        tab_layout.addWidget(self.tags_label)
        tab_layout.addWidget(self.tags_input, stretch=1)
        tab_layout.addWidget(self.list_name_label)
        tab_layout.addWidget(self.list_name_input, stretch=1)
        tab_layout.addStretch()
        
        content_layout.addLayout(tab_layout)
        
        # 输入框
        self.text_edit = CustomTextEdit()  # 使用自定义的TextEdit
        self.text_edit.setPlaceholderText("输入你的灵感...")
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {bg_input};
                color: {fg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 20px;
                font-size: 16px;
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
                line-height: 1.8;
                selection-background-color: {accent_color};
                selection-color: white;
            }}
            QTextEdit:focus {{
                border: 2px solid {accent_color};
                background: {bg_secondary};
            }}
        """)
        # 连接自定义信号
        self.text_edit.submit_requested.connect(self._submit_content)
        self.text_edit.cancel_requested.connect(self._cancel)
        
        # 为输入框添加内阴影效果，增强立体感
        text_shadow = QGraphicsDropShadowEffect()
        text_shadow.setBlurRadius(15)
        text_shadow.setColor(QColor(0, 0, 0, 60))
        text_shadow.setOffset(0, 2)
        self.text_edit.setGraphicsEffect(text_shadow)
        
        content_layout.addWidget(self.text_edit, stretch=1)
        
        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 提示标签
        hint_label = QLabel("💡 Enter发送 | Ctrl+Enter换行 | Esc取消")
        hint_label.setStyleSheet(f"""
            QLabel {{
                color: {fg_secondary};
                font-size: 12px;
                padding: 5px;
                background: transparent;
            }}
        """)
        button_layout.addWidget(hint_label)
        button_layout.addStretch()
        
        # 取消按钮
        cancel_btn = QPushButton("✕ 取消")
        cancel_btn.setFixedSize(100, 44)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {bg_input};
                color: {fg_color};
                border: 1px solid {accent_color};
            }}
        """)
        cancel_btn.clicked.connect(self._cancel)
        button_layout.addWidget(cancel_btn)
        
        # 发送按钮
        send_btn = QPushButton("🚀 发送")
        send_btn.setFixedSize(120, 44)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {accent_color}, stop:1 {accent_secondary});
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 212, 255, 1), stop:1 rgba(0, 153, 255, 1));
                border: 1px solid {accent_color};
            }}
            QPushButton:pressed {{
                background: {accent_secondary};
            }}
        """)
        send_btn.clicked.connect(self._submit_content)
        
        # 为发送按钮添加发光效果（柔和版）
        send_glow = QGraphicsDropShadowEffect()
        send_glow.setBlurRadius(30)
        send_glow.setColor(QColor(94, 184, 217, 140))
        send_glow.setOffset(0, 2)
        send_btn.setGraphicsEffect(send_glow)
        
        button_layout.addWidget(send_btn)
        
        content_layout.addLayout(button_layout)
        content_widget.setLayout(content_layout)
        layout.addWidget(content_widget)
        
        main_container.setLayout(layout)
        
        # 外层布局（增加边距以确保圆角和阴影完整显示）
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(15, 15, 15, 15)  # 四周留出空间
        outer_layout.addWidget(main_container)
        self.setLayout(outer_layout)
    
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
        
        # 确保窗口显示并获取焦点
        self.show()
        self.raise_()
        self.activateWindow()
        
        # 在 Windows 上强制激活窗口
        try:
            import ctypes
            hwnd = int(self.winId())
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except:
            pass
        
        # 延迟聚焦到输入框，确保窗口已完全激活
        QTimer.singleShot(50, lambda: self.text_edit.setFocus())
        QTimer.singleShot(100, lambda: self.text_edit.setFocus())  # 双重保险
        
        logger.info("快速输入窗口已显示")
    
    
    def keyPressEvent(self, event: QKeyEvent):
        """窗口按键事件（用于Esc键等）"""
        if event.key() == Qt.Key_Escape:
            self._cancel()
        else:
            super().keyPressEvent(event)
    
    def _switch_platform(self, platform: str):
        """切换目标平台"""
        self.target_platform = platform
        
        if platform == "notion":
            self.notion_tab_btn.setChecked(True)
            self.flomo_tab_btn.setChecked(False)
            self.ticktick_tab_btn.setChecked(False)
            self.tags_label.setVisible(False)
            self.tags_input.setVisible(False)
            self.list_name_label.setVisible(False)
            self.list_name_input.setVisible(False)
            self.text_edit.setPlaceholderText("输入你的灵感...")
            logger.info("切换到Notion模式")
        elif platform == "flomo":
            self.notion_tab_btn.setChecked(False)
            self.flomo_tab_btn.setChecked(True)
            self.ticktick_tab_btn.setChecked(False)
            self.tags_label.setVisible(True)
            self.tags_input.setVisible(True)
            self.list_name_label.setVisible(False)
            self.list_name_input.setVisible(False)
            # 如果标签为空，设置为默认值
            if not self.tags_input.text().strip():
                self.tags_input.setText("闪念")
            self.text_edit.setPlaceholderText("输入金句、知识或方法论...")
            logger.info("切换到Flomo模式")
        else:  # ticktick
            self.notion_tab_btn.setChecked(False)
            self.flomo_tab_btn.setChecked(False)
            self.ticktick_tab_btn.setChecked(True)
            self.tags_label.setVisible(False)
            self.tags_input.setVisible(False)
            self.list_name_label.setVisible(True)
            self.list_name_input.setVisible(True)
            self.text_edit.setPlaceholderText("输入待办任务...")
            logger.info("切换到滴答清单模式")
    
    def _submit_content(self):
        """提交内容"""
        content = self.text_edit.toPlainText().strip()
        
        if content:
            # 获取标签或额外参数
            tags = ""
            if self.target_platform == "flomo":
                tags = self.tags_input.text().strip()
                if not tags:
                    tags = "闪念"  # 如果没有标签，使用默认值
            elif self.target_platform == "ticktick":
                # TickTick 使用 tags 字段传递清单名称
                tags = self.list_name_input.text().strip()
            
            logger.info(f"提交内容到{self.target_platform}: {content[:50]}..., 标签/参数: {tags}")
            
            # 发送信号：平台，内容，标签/参数
            self.content_submitted.emit(self.target_platform, content, tags)
            
            # 清空输入
            self.text_edit.clear()
            if self.target_platform == "flomo":
                self.tags_input.setText("闪念")  # 重置为默认值
            elif self.target_platform == "ticktick":
                self.list_name_input.clear()  # 清空清单名称
            else:
                self.tags_input.clear()
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
