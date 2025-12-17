"""快速输入窗口"""
from PyQt5.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QGraphicsDropShadowEffect, QButtonGroup, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QFont, QColor, QPalette, QKeyEvent, QMouseEvent, QCursor, QPainter, QBrush
from loguru import logger


class CustomTextEdit(QTextEdit):
    """自定义文本编辑器，修复按键处理"""
    
    # 信号
    submit_requested = pyqtSignal()
    cancel_requested = pyqtSignal()
    
    def keyPressEvent(self, event: QKeyEvent):
        """按键事件处理"""
        # Ctrl+Enter: 换行（正常处理）
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ControlModifier:
                # Ctrl+Enter: 正常换行
                super().keyPressEvent(event)
                return
            else:
                # Enter: 提交内容
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


class PinButton(QPushButton):
    """自定义置顶按钮，支持不同颜色的圆点"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_pinned = True
        self._fg_color = "#e8e8e8"
        self.setFlat(True)  # 扁平按钮，无默认背景
        
    def setPinned(self, pinned: bool):
        """设置置顶状态"""
        self._is_pinned = pinned
        self.update()  # 触发重绘
        
    def paintEvent(self, event):
        """绘制按钮（包含不同颜色的圆点）"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景（如果有hover效果）
        if self.underMouse():
            painter.fillRect(self.rect(), QColor(0, 212, 255, 51))  # rgba(0, 212, 255, 0.2)
        
        # 设置字体（调小2个字号：从13px改为11px）
        font = QFont('Microsoft YaHei', 11)
        painter.setFont(font)
        
        # 根据状态设置圆点颜色
        if self._is_pinned:
            # 已置顶：绿色圆点
            dot_color = QColor(76, 175, 80)  # #4caf50
            text = "已置顶"
        else:
            # 未置顶：红色圆点
            dot_color = QColor(244, 67, 54)  # #f44336
            text = "未置顶"
        
        # 绘制圆点
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(dot_color))
        dot_radius = 4
        dot_x = 8
        dot_y = self.height() // 2
        painter.drawEllipse(dot_x - dot_radius, dot_y - dot_radius, dot_radius * 2, dot_radius * 2)
        
        # 绘制文字
        painter.setPen(QColor(self._fg_color))
        text_x = dot_x + dot_radius * 2 + 6
        text_y = self.height() // 2 + 5  # 垂直居中（字体基线）
        painter.drawText(text_x, text_y, text)


class OverlayMaskWidget(QWidget):
    """全屏遮罩窗口（自定义绘制半透明背景）"""
    
    def __init__(self, geometry, mask_color=(0, 0, 0), mask_alpha=153, on_click_callback=None, parent=None):
        super().__init__(parent)
        self.setGeometry(geometry)
        self.mask_color = mask_color  # RGB颜色元组
        self.mask_alpha = mask_alpha  # 透明度（0-255）
        self.on_click_callback = on_click_callback  # 点击回调函数
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.X11BypassWindowManagerHint |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # 设置鼠标事件穿透，让输入窗口可以接收鼠标事件
        # 注意：遮罩只用于视觉效果，不拦截鼠标事件
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
    def mousePressEvent(self, event):
        """点击遮罩时关闭输入窗口（但鼠标事件已穿透，这个不会被调用）"""
        # 由于设置了 WA_TransparentForMouseEvents，这个事件不会被触发
        # 点击遮罩关闭窗口的功能改为在输入窗口失去焦点时实现
        if self.on_click_callback:
            self.on_click_callback()
        super().mousePressEvent(event)
        
    def paintEvent(self, event):
        """绘制半透明背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 使用配置的颜色和透明度
        painter.fillRect(self.rect(), QColor(*self.mask_color, self.mask_alpha))


class QuickInputWindow(QWidget):
    """快速输入窗口"""
    
    # 信号：内容提交（平台，内容，额外参数字典）
    content_submitted = pyqtSignal(str, str, dict)  # platform, content, extra_params
    
    def __init__(self, config: dict):
        """
        初始化快速输入窗口
        
        Args:
            config: UI配置
        """
        super().__init__()
        self.config = config
        self.drag_position = None  # 用于拖动窗口
        self._mask_widgets = []  # 全屏遮罩列表
        self._is_always_on_top = True  # 默认置顶
        # 确保窗口可以接收输入法事件（支持中文输入）
        self.setAttribute(Qt.WA_InputMethodEnabled, True)
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
        
        # 窗口标志：无边框、普通窗口（可最小化）
        # 置顶状态通过 _update_window_flags 方法动态设置
        self._update_window_flags()
        
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
        
        # 添加阴影效果（AI 发光感 + 立体感）
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)  # 模糊半径缩小50%（从80到40）
        shadow.setColor(QColor(94, 184, 217, 100))  # 柔和青色光晕
        shadow.setOffset(0, 8)  # 阴影偏移
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
        
        # 置顶开关按钮（使用自定义文字按钮）
        self.pin_btn = PinButton()
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(True)  # 默认置顶
        self.pin_btn.setPinned(True)  # 默认置顶
        self.pin_btn.setFixedHeight(40)
        self.pin_btn.setMinimumWidth(90)
        self.pin_btn.setToolTip("点击切换置顶状态")
        self.pin_btn._fg_color = fg_color
        # 设置按钮样式
        self.pin_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                font-size: 13px;
                color: {fg_color};
                font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;
            }}
            QPushButton:hover {{
                background: rgba(0, 212, 255, 0.2);
                border-radius: 8px;
            }}
        """)
        self.pin_btn.clicked.connect(self._toggle_always_on_top)
        title_layout.addWidget(self.pin_btn)
        
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
        content_layout.setContentsMargins(20, 15, 20, 18)  # 底部边距稍微减少
        content_layout.setSpacing(15)
        
        # Tab切换按钮（只包含平台切换按钮）
        tab_layout = QHBoxLayout()
        tab_layout.setSpacing(10)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
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
        
        tab_layout.addStretch()
        content_layout.addLayout(tab_layout)
        
        # ========== 平台特定的选填项区域 ==========
        self.options_container = QWidget()
        self.options_container.setStyleSheet("background: transparent; border: none;")
        self.options_layout = QHBoxLayout()
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        self.options_layout.setSpacing(12)
        
        # Notion选填项: 状态、优先级、标签
        self.notion_options = QWidget()
        notion_options_layout = QHBoxLayout()
        notion_options_layout.setContentsMargins(0, 0, 0, 0)
        notion_options_layout.setSpacing(10)  # 缩小间距：15 * 0.7 = 10.5，取整为10
        
        # 状态选择（改为按钮组）
        status_label = QLabel("状态:")
        # 增大字体，使用微软雅黑
        status_label.setStyleSheet(f"font-size: 13px; color: {fg_secondary}; min-width: 35px; font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;")
        notion_options_layout.addWidget(status_label)
        
        # 状态按钮组
        status_btn_group = QHBoxLayout()
        status_btn_group.setSpacing(4)  # 缩小间距：6 * 0.7 = 4.2，取整为4
        status_btn_group.setContentsMargins(0, 0, 0, 0)
        self.notion_status_group = QButtonGroup()
        self.notion_status_buttons = {}
        status_options = ["待处理", "进行中", "已完成", "已搁置"]
        
        for i, option in enumerate(status_options):
            btn = QPushButton(option)
            btn.setCheckable(True)
            # 缩小30%：36 * 0.7 = 25.2，取整为25
            btn.setFixedHeight(25)
            # 缩小30%：75 * 0.7 = 52.5，取整为53
            btn.setMinimumWidth(53)
            if i == 0:  # 默认选中"待处理"
                btn.setChecked(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: white;
                    border: 1px solid {border_color};
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 13px;
                    font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;
                }}
                QPushButton:hover {{
                    border: 1px solid {accent_color};
                    background: rgba(94, 184, 217, 0.1);
                }}
                QPushButton:checked {{
                    background: {accent_color};
                    color: white;
                    border: 1px solid {accent_color};
                }}
            """)
            self.notion_status_group.addButton(btn, i)
            self.notion_status_buttons[option] = btn
            status_btn_group.addWidget(btn)
        
        status_btn_group.addStretch()
        notion_options_layout.addLayout(status_btn_group)
        
        # 优先级选择（改为按钮组）
        priority_label = QLabel("优先级:")
        # 增大字体，使用微软雅黑
        priority_label.setStyleSheet(f"font-size: 13px; color: {fg_secondary}; min-width: 42px; font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;")
        notion_options_layout.addWidget(priority_label)
        
        # 优先级按钮组
        priority_btn_group = QHBoxLayout()
        priority_btn_group.setSpacing(4)  # 缩小间距：6 * 0.7 = 4.2，取整为4
        priority_btn_group.setContentsMargins(0, 0, 0, 0)
        self.notion_priority_group = QButtonGroup()
        self.notion_priority_buttons = {}
        priority_options = ["高", "中", "低"]
        
        for i, option in enumerate(priority_options):
            btn = QPushButton(option)
            btn.setCheckable(True)
            # 缩小30%：36 * 0.7 = 25.2，取整为25
            btn.setFixedHeight(25)
            # 缩小30%：60 * 0.7 = 42，取整为42
            btn.setMinimumWidth(42)
            if i == 1:  # 默认选中"中"
                btn.setChecked(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: white;
                    border: 1px solid {border_color};
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 13px;
                    font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;
                }}
                QPushButton:hover {{
                    border: 1px solid {accent_color};
                    background: rgba(94, 184, 217, 0.1);
                }}
                QPushButton:checked {{
                    background: {accent_color};
                    color: white;
                    border: 1px solid {accent_color};
                }}
            """)
            self.notion_priority_group.addButton(btn, i)
            self.notion_priority_buttons[option] = btn
            priority_btn_group.addWidget(btn)
        
        priority_btn_group.addStretch()
        notion_options_layout.addLayout(priority_btn_group)
        
        # 标签输入
        tags_label_notion = QLabel("标签:")
        # 增大字体，使用微软雅黑
        tags_label_notion.setStyleSheet(f"font-size: 13px; color: {fg_secondary}; min-width: 35px; font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;")
        notion_options_layout.addWidget(tags_label_notion)
        
        self.notion_tags = QLineEdit()
        self.notion_tags.setText("灵感")  # 默认标签
        self.notion_tags.setPlaceholderText("多个标签用空格分隔")
        # 缩小30%：200 * 0.7 = 140
        self.notion_tags.setMinimumWidth(140)
        self.notion_tags.setFixedHeight(25)  # 缩小30%：36 * 0.7 = 25.2，取整为25
        self.notion_tags.setStyleSheet(f"""
            QLineEdit {{
                background: {bg_input};
                color: {fg_color};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
                font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;
                min-width: 140px;
            }}
            QLineEdit:focus {{
                border: 2px solid {accent_color};
                background: {bg_secondary};
            }}
            QLineEdit::placeholder {{
                color: {fg_secondary};
                font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;
            }}
        """)
        notion_options_layout.addWidget(self.notion_tags, stretch=2)  # 增加stretch值，让标签输入框更宽
        
        notion_options_layout.addStretch()
        self.notion_options.setLayout(notion_options_layout)
        
        # Flomo选填项: 标签
        self.flomo_options = QWidget()
        flomo_options_layout = QHBoxLayout()
        flomo_options_layout.setContentsMargins(0, 0, 0, 0)
        flomo_options_layout.setSpacing(12)
        
        tags_label_flomo = QLabel("标签:")
        tags_label_flomo.setStyleSheet(f"font-size: 13px; color: {fg_secondary}; min-width: 45px;")
        self.flomo_tags = QLineEdit()
        self.flomo_tags.setPlaceholderText("多个标签用空格分隔")
        self.flomo_tags.setText("闪念 QuickNote AI")  # 默认标签
        self.flomo_tags.setStyleSheet(f"""
            QLineEdit {{
                background: {bg_input};
                color: {fg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 2px solid {accent_color};
                background: {bg_secondary};
            }}
            QLineEdit::placeholder {{
                color: {fg_secondary};
            }}
        """)
        flomo_options_layout.addWidget(tags_label_flomo)
        flomo_options_layout.addWidget(self.flomo_tags, stretch=1)
        flomo_options_layout.addStretch()
        self.flomo_options.setLayout(flomo_options_layout)
        self.flomo_options.setVisible(False)
        
        # TickTick选填项: 无（已删除提醒时间输入框）
        # 创建一个空的占位widget，保持布局一致
        self.ticktick_options = QWidget()
        self.ticktick_options.setVisible(False)
        
        # 添加到选项容器
        self.options_layout.addWidget(self.notion_options)
        self.options_layout.addWidget(self.flomo_options)
        self.options_layout.addWidget(self.ticktick_options)
        self.options_container.setLayout(self.options_layout)
        content_layout.addWidget(self.options_container)
        
        # 输入框
        self.text_edit = CustomTextEdit()  # 使用自定义的TextEdit
        self.text_edit.setPlaceholderText("输入你的灵感...")
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {bg_input};
                color: {fg_color};
                border: 1px solid {border_color};
                border-radius: 14px;
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
        button_layout.setContentsMargins(0, 8, 0, 0)  # 增加顶部边距
        
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
    
    def _update_window_flags(self):
        """更新窗口标志（根据置顶状态）"""
        # 保存当前窗口位置和大小
        current_pos = self.pos()
        current_size = self.size()
        is_visible = self.isVisible()
        
        flags = (
            Qt.FramelessWindowHint |
            Qt.Window |  # 普通窗口，可以最小化
            Qt.X11BypassWindowManagerHint  # 绕过窗口管理器（Windows上无影响，但确保圆角正常）
        )
        if self._is_always_on_top:
            flags |= Qt.WindowStaysOnTopHint  # 保持在顶层
        
        self.setWindowFlags(flags)
        # 恢复窗口位置和大小
        self.move(current_pos)
        self.resize(current_size)
        
        # 重新显示窗口以应用新的标志
        if is_visible:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def _toggle_always_on_top(self):
        """切换置顶状态"""
        # 获取按钮的当前状态（点击后会自动切换）
        checked = self.pin_btn.isChecked()
        self._is_always_on_top = checked
        
        # 更新自定义按钮的置顶状态（触发重绘）
        self.pin_btn.setPinned(checked)
        
        # 根据置顶状态创建或移除遮罩
        if checked:
            # 置顶时：创建遮罩
            self._create_overlay_mask()
        else:
            # 未置顶时：移除遮罩
            self._remove_overlay_mask()
        
        # 延迟更新窗口标志，避免窗口关闭
        QTimer.singleShot(50, self._update_window_flags)
        
        logger.info(f"窗口置顶状态已切换: {self._is_always_on_top}, 按钮文字: {'已置顶' if checked else '未置顶'}, 遮罩: {'已创建' if checked else '已移除'}")
    
    def _create_overlay_mask(self):
        """创建全屏遮罩（使用自定义绘制窗口，可配置颜色和透明度）"""
        # 如果已经创建过，先移除
        if self._mask_widgets:
            self._remove_overlay_mask()
        
        # 从配置读取遮罩颜色和透明度
        # 默认：黑色，透明度60%（alpha=153）
        mask_color_rgb = self.config.get('mask_color', self.config.get('ui.mask_color', [0, 0, 0]))  # 默认黑色
        mask_alpha = self.config.get('mask_alpha', self.config.get('ui.mask_alpha', 153))  # 默认60%透明度（255*0.6≈153）
        
        # 确保颜色是元组格式
        if isinstance(mask_color_rgb, list):
            mask_color = tuple(mask_color_rgb)
        else:
            mask_color = (0, 0, 0)  # 默认黑色
        
        # 点击遮罩时关闭输入窗口的回调
        def on_mask_clicked():
            logger.info("遮罩被点击，关闭输入窗口")
            self.hide()
        
        # 在所有屏幕上显示遮罩
        screens = QApplication.screens()
        for screen in screens:
            geometry = screen.geometry()
            # 使用自定义遮罩窗口类，传递颜色、透明度和点击回调
            mask = OverlayMaskWidget(
                geometry, 
                mask_color=mask_color, 
                mask_alpha=mask_alpha,
                on_click_callback=on_mask_clicked
            )
            
            # 显示遮罩
            mask.show()
            mask.raise_()  # 确保遮罩显示在最上层
            
            # 保存引用以便后续关闭
            self._mask_widgets.append(mask)
            
            logger.debug(f"遮罩已创建: {geometry}, 颜色: {mask_color}, 透明度: {mask_alpha}, 可见: {mask.isVisible()}")
        
        # 延迟确保输入窗口在遮罩上方
        # 使用多次延迟和 Windows API 确保窗口层级正确
        def ensure_on_top():
            try:
                import ctypes
                # 先确保所有遮罩窗口显示并设置为 TOPMOST
                for mask in self._mask_widgets:
                    if mask.isVisible():
                        mask_hwnd = int(mask.winId())
                        # 遮罩窗口设置为 HWND_TOPMOST
                        ctypes.windll.user32.SetWindowPos(
                            mask_hwnd,
                            -2,  # HWND_TOPMOST
                            0, 0, 0, 0,
                            0x0001 | 0x0002  # SWP_NOMOVE | SWP_NOSIZE
                        )
                        # 强制刷新遮罩窗口
                        ctypes.windll.user32.ShowWindow(mask_hwnd, 1)  # SW_SHOWNORMAL
                
                # 然后确保输入窗口在最上层（在所有遮罩之上）
                hwnd = int(self.winId())
                # 使用 HWND_TOPMOST 确保输入窗口在遮罩之上，并且可以接收鼠标事件
                ctypes.windll.user32.SetWindowPos(
                    hwnd,
                    -2,  # HWND_TOPMOST - 置顶（在所有遮罩之上）
                    0, 0, 0, 0,
                    0x0001 | 0x0002  # SWP_NOMOVE | SWP_NOSIZE
                )
            except Exception as e:
                logger.warning(f"设置窗口层级失败: {e}")
            
            self.raise_()
            self.activateWindow()
        
        # 多次延迟确保窗口层级正确
        QTimer.singleShot(10, ensure_on_top)
        QTimer.singleShot(50, ensure_on_top)
        QTimer.singleShot(100, ensure_on_top)
        QTimer.singleShot(200, ensure_on_top)
        QTimer.singleShot(500, ensure_on_top)  # 增加一次延迟
        
        logger.info(f"遮罩已创建，数量: {len(self._mask_widgets)}, 屏幕数: {len(screens)}")
    
    def _remove_overlay_mask(self):
        """移除全屏遮罩"""
        if self._mask_widgets:
            for mask in self._mask_widgets:
                try:
                    mask.close()
                    mask.deleteLater()
                except:
                    pass
            self._mask_widgets.clear()
    
    def _get_screen_at_cursor(self):
        """获取鼠标所在屏幕"""
        cursor_pos = QCursor.pos()
        screens = QApplication.screens()
        
        for screen in screens:
            geometry = screen.geometry()
            if geometry.contains(cursor_pos):
                return screen
        
        # 如果找不到，返回主屏幕
        return QApplication.primaryScreen()
    
    def show_at_center(self):
        """显示在鼠标所在屏幕的中央"""
        # 只有置顶时才创建遮罩
        if self._is_always_on_top:
            self._create_overlay_mask()
        
        # 获取鼠标所在屏幕
        screen = self._get_screen_at_cursor()
        screen_geometry = screen.geometry()
        
        # 计算中心位置（相对于该屏幕）
        x = screen_geometry.x() + (screen_geometry.width() - self.width()) // 2
        y = screen_geometry.y() + (screen_geometry.height() - self.height()) // 2
        
        self.move(x, y)
        
        # 确保窗口显示并获取焦点
        self.show()
        
        # 强制确保输入窗口在遮罩上方（多次尝试）
        def ensure_on_top():
            self.raise_()
            self.activateWindow()
            # 在 Windows 上强制激活窗口
            try:
                import ctypes
                hwnd = int(self.winId())
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                # 确保窗口在顶层
                ctypes.windll.user32.SetWindowPos(
                    hwnd, 
                    -1,  # HWND_TOP
                    0, 0, 0, 0,
                    0x0001 | 0x0002  # SWP_NOMOVE | SWP_NOSIZE
                )
            except:
                pass
        
        # 延迟确保窗口在顶层（多次尝试确保成功）
        QTimer.singleShot(10, ensure_on_top)
        QTimer.singleShot(50, ensure_on_top)
        QTimer.singleShot(100, ensure_on_top)
        QTimer.singleShot(200, ensure_on_top)
        
        # 延迟聚焦到输入框，确保窗口已完全激活
        QTimer.singleShot(250, lambda: self.text_edit.setFocus())
        
        logger.info(f"快速输入窗口已显示在屏幕: {screen.name()}, 遮罩数量: {len(self._mask_widgets)}")
    
    def hide(self):
        """隐藏窗口并移除遮罩"""
        self._remove_overlay_mask()
        super().hide()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self._remove_overlay_mask()
        super().closeEvent(event)
    
    
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
            self.notion_options.setVisible(True)
            self.flomo_options.setVisible(False)
            self.ticktick_options.setVisible(False)
            self.options_container.setVisible(True)  # 显示选项容器
            self.text_edit.setPlaceholderText("输入你的灵感...")
            logger.info("切换到Notion模式")
        elif platform == "flomo":
            self.notion_tab_btn.setChecked(False)
            self.flomo_tab_btn.setChecked(True)
            self.ticktick_tab_btn.setChecked(False)
            self.notion_options.setVisible(False)
            self.flomo_options.setVisible(True)
            self.ticktick_options.setVisible(False)
            self.options_container.setVisible(True)  # 显示选项容器
            # 如果标签为空，设置为默认值
            if not self.flomo_tags.text().strip():
                self.flomo_tags.setText("闪念 QuickNote AI")
            self.text_edit.setPlaceholderText("输入金句、知识或方法论...")
            logger.info("切换到Flomo模式")
        else:  # ticktick
            self.notion_tab_btn.setChecked(False)
            self.flomo_tab_btn.setChecked(False)
            self.ticktick_tab_btn.setChecked(True)
            self.notion_options.setVisible(False)
            self.flomo_options.setVisible(False)
            self.ticktick_options.setVisible(False)  # TickTick无选填项，隐藏
            self.options_container.setVisible(False)  # 隐藏整个选项容器，减少间隔
            self.text_edit.setPlaceholderText("输入待办任务...")
            logger.info("切换到滴答清单模式")
    
    def _submit_content(self):
        """提交内容"""
        content = self.text_edit.toPlainText().strip()
        
        if content:
            # 根据平台收集额外参数
            extra_params = {}
            
            if self.target_platform == "notion":
                # Notion: 状态、优先级、标签
                # 获取选中的状态按钮
                checked_status_btn = self.notion_status_group.checkedButton()
                if checked_status_btn:
                    extra_params["status"] = checked_status_btn.text()
                else:
                    extra_params["status"] = "待处理"  # 默认值
                
                # 获取选中的优先级按钮
                checked_priority_btn = self.notion_priority_group.checkedButton()
                if checked_priority_btn:
                    extra_params["priority"] = checked_priority_btn.text()
                else:
                    extra_params["priority"] = "中"  # 默认值
                
                tags_text = self.notion_tags.text().strip()
                if tags_text:
                    extra_params["tags"] = [tag.strip() for tag in tags_text.split() if tag.strip()]
                
            elif self.target_platform == "flomo":
                # Flomo: 标签
                tags_text = self.flomo_tags.text().strip()
                if not tags_text:
                    tags_text = "闪念 QuickNote AI"  # 默认标签
                extra_params["tags"] = tags_text
                
            elif self.target_platform == "ticktick":
                # TickTick: 无额外参数（时间从内容中自动提取）
                pass
            
            logger.info(f"提交内容到{self.target_platform}: {content[:50]}..., 参数: {extra_params}")
            
            # 立即清空输入并隐藏窗口（不等待保存结果）
            self.text_edit.clear()
            if self.target_platform == "flomo":
                self.flomo_tags.setText("闪念 QuickNote AI")  # 重置为默认值
            elif self.target_platform == "notion":
                self.notion_tags.setText("灵感")  # 重置为默认标签
                # 重置状态和优先级按钮为默认值
                if "待处理" in self.notion_status_buttons:
                    self.notion_status_buttons["待处理"].setChecked(True)
                if "中" in self.notion_priority_buttons:
                    self.notion_priority_buttons["中"].setChecked(True)
            # TickTick 无需清空（已删除提醒时间输入框）
            self.hide()
            
            # 发送信号到后台处理（异步）
            self.content_submitted.emit(self.target_platform, content, extra_params)
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
