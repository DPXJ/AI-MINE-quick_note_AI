"""快速输入窗口"""
from PyQt5.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QGraphicsDropShadowEffect, QButtonGroup, QApplication, QDialog, QInputDialog
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint, QTime, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QPalette, QKeyEvent, QMouseEvent, QCursor, QPainter, QBrush, QPen, QLinearGradient
from loguru import logger
import datetime
from src.services.quote_service import QuoteService


class CustomTextEdit(QTextEdit):
    """自定义文本编辑器，修复按键处理"""
    
    # 信号
    submit_requested = pyqtSignal()
    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # 确保文本框可以接收输入法事件（支持中文输入/IME）
        self.setAttribute(Qt.WA_InputMethodEnabled, True)
    
    def keyPressEvent(self, event: QKeyEvent):
        """按键事件处理"""
        key = event.key()
        modifiers = event.modifiers()
        
        # Enter 或 Return 键
        if key in (Qt.Key_Return, Qt.Key_Enter):
            # 检查是否按下了 Ctrl 键
            ctrl_pressed = bool(modifiers & Qt.ControlModifier)
            
            if ctrl_pressed:
                # Ctrl+Enter: 显式插入换行符
                cursor = self.textCursor()
                cursor.insertText('\n')
                self.setTextCursor(cursor)
                event.accept()
                return
            else:
                # Enter: 提交内容
                self.submit_requested.emit()
                event.accept()
                return
        
        # Esc: 取消
        if key == Qt.Key_Escape:
            self.cancel_requested.emit()
            event.accept()
            return
        
        # 其他按键正常处理（包括Backspace、Delete等）
        super().keyPressEvent(event)


class GradientBorderButton(QPushButton):
    """自定义按钮，支持渐变边框（AI风格）"""
    
    def __init__(self, text, bg_color, border_gradient_colors, text_color, parent=None):
        super().__init__(text, parent)
        self.bg_color = bg_color
        self.border_gradient_colors = border_gradient_colors  # [(r, g, b, a), ...]
        self.text_color = text_color
        self._hover = False
        
    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect()
        border_width = 2
        
        # 绘制渐变边框
        if self._hover:
            # hover时边框更亮
            colors = [(min(255, c[0] + 20), min(255, c[1] + 20), min(255, c[2] + 20), c[3]) 
                     for c in self.border_gradient_colors]
        else:
            colors = self.border_gradient_colors
        
        # 绘制渐变边框（使用多个小段模拟渐变）
        num_segments = len(colors)
        for i in range(num_segments):
            color1 = colors[i]
            color2 = colors[(i + 1) % num_segments]
            start_pos = i / num_segments
            end_pos = (i + 1) / num_segments
            
            # 绘制边框段（简化版：使用线性渐变）
            painter.setPen(QColor(*color1))
            # 这里简化处理，使用单色边框
            if i == 0:
                painter.setPen(QColor(*colors[0]))
        
        # 绘制边框（使用渐变色的平均值）
        avg_color = tuple(sum(c[i] for c in colors) // len(colors) for i in range(3))
        painter.setPen(QColor(*avg_color, colors[0][3] if colors else 200))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect.adjusted(border_width//2, border_width//2, 
                                             -border_width//2, -border_width//2), 
                               10, 10)
        
        # 绘制背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(self.bg_color)))
        painter.drawRoundedRect(rect.adjusted(border_width, border_width, 
                                            -border_width, -border_width), 
                               10, 10)
        
        # 绘制文字
        painter.setPen(QColor(self.text_color))
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignCenter, self.text())


class FlowGradientButton(QPushButton):
    """发送按钮：渐变边框可流动（QTimer 驱动的相位偏移）。"""

    def __init__(self, text: str, bg_color: str, text_color: str, gradient_colors, parent=None):
        super().__init__(text, parent)
        self._bg_color = bg_color
        self._text_color = text_color
        self._gradient_colors = gradient_colors  # [(r,g,b,a), ...]
        self._hover = False
        self._phase = 0.0

        self.setCursor(Qt.PointingHandCursor)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(30)  # ~33fps，足够顺滑且开销低

    def _tick(self):
        self._phase = (self._phase + 0.02) % 1.0
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def hideEvent(self, event):
        # 不显示时停掉动画，省 CPU
        if self._timer.isActive():
            self._timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        if not self._timer.isActive():
            self._timer.start(30)
        super().showEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        border_width = 3
        radius = 10

        # hover 时提升亮度
        if self._hover:
            colors = [(min(255, c[0] + 25), min(255, c[1] + 25), min(255, c[2] + 25), c[3]) for c in self._gradient_colors]
        else:
            colors = self._gradient_colors

        # 渐变“流动”：移动渐变起止点
        w = max(1, rect.width())
        shift = (self._phase * 2.0 - 1.0) * w  # [-w, +w]
        gradient = QLinearGradient(rect.left() + shift, rect.top(), rect.right() + shift, rect.bottom())
        if len(colors) >= 3:
            gradient.setColorAt(0.0, QColor(*colors[0]))
            gradient.setColorAt(0.33, QColor(*colors[1]))
            gradient.setColorAt(0.66, QColor(*colors[2]))
            gradient.setColorAt(1.0, QColor(*colors[0]))
        else:
            gradient.setColorAt(0.0, QColor(168, 85, 247, 230))
            gradient.setColorAt(0.5, QColor(34, 197, 94, 230))
            gradient.setColorAt(1.0, QColor(59, 130, 246, 230))

        # 边框
        painter.setPen(QPen(gradient, border_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(
            rect.adjusted(border_width // 2, border_width // 2, -border_width // 2, -border_width // 2),
            radius,
            radius,
        )

        # 背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(self._bg_color)))
        painter.drawRoundedRect(
            rect.adjusted(border_width, border_width, -border_width, -border_width),
            radius,
            radius,
        )

        # 文字
        painter.setPen(QColor(self._text_color))
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignCenter, self.text())


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


class SelectedDotButton(QPushButton):
    """通用选项按钮：选中时矩形填充 + 右上角绿色圆点。"""

    def __init__(
        self,
        text: str,
        bg: str,
        bg_checked: str,
        fg: str,
        fg_checked: str,
        border: str,
        border_checked: str,
        radius: int = 6,
        parent=None,
    ):
        super().__init__(text, parent)
        self._bg = bg
        self._bg_checked = bg_checked
        self._fg = fg
        self._fg_checked = fg_checked
        self._border = border
        self._border_checked = border_checked
        self._radius = radius
        self._hover = False

        self.setCheckable(True)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        # 关键：这里用像素大小与 QLabel 的 `font-size: 13px` 保持一致
        font = QFont('Microsoft YaHei')
        font.setPixelSize(13)
        self.setFont(font)

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        checked = self.isChecked()

        # 背景
        bg = self._bg_checked if checked else self._bg
        if self._hover and not checked:
            # hover 轻微提亮
            bg = QColor(bg)
            bg = QColor(min(bg.red() + 8, 255), min(bg.green() + 8, 255), min(bg.blue() + 8, 255))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(bg)))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), self._radius, self._radius)

        # 边框
        border_color = self._border_checked if checked else self._border
        border_w = 2 if checked else 1
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(border_color), border_w))
        painter.drawRoundedRect(
            rect.adjusted(border_w // 2, border_w // 2, -border_w // 2, -border_w // 2),
            self._radius,
            self._radius,
        )

        # 文字
        painter.setPen(QColor(self._fg_checked if checked else self._fg))
        painter.setFont(self.font())
        painter.drawText(rect, Qt.AlignCenter, self.text())

        # 选中圆点（右上角绿色）
        if checked:
            dot_color = QColor(76, 175, 80)  # #4caf50
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(dot_color))
            # 调小 50%
            r = 2
            x = rect.right() - 8
            y = rect.top() + 8
            painter.drawEllipse(x - r, y - r, r * 2, r * 2)


class PlainLineEditContainer(QWidget):
    """圆角输入框容器：统一绘制背景/边框，避免 QLineEdit 右侧圆角在某些 DPI/主题下丢失。"""

    def __init__(
        self,
        line_edit: QLineEdit,
        bg_color: str,
        border_color: str,
        focus_border_color: str,
        text_color: str,
        placeholder_color: str,
        radius: int = 6,
        parent=None,
    ):
        super().__init__(parent)
        self._bg_color = bg_color
        self._border_color = border_color
        self._focus_border_color = focus_border_color
        self._text_color = text_color
        self._placeholder_color = placeholder_color
        self._radius = radius
        self._focused = False

        self.line_edit = line_edit
        self.line_edit.setFrame(False)
        self.line_edit.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                color: {self._text_color};
                border: none;
                padding: 0px;
                font-size: 13px;
                font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;
            }}
            QLineEdit::placeholder {{
                color: {self._placeholder_color};
                font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;
            }}
        """)
        self.line_edit.installEventFilter(self)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 3, 10, 3)
        layout.setSpacing(0)
        layout.addWidget(self.line_edit)
        self.setLayout(layout)

    def eventFilter(self, obj, event):
        if obj is self.line_edit:
            if event.type() == event.FocusIn:
                self._focused = True
                self.update()
            elif event.type() == event.FocusOut:
                self._focused = False
                self.update()
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # 背景
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(self._bg_color)))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), self._radius, self._radius)

        # 边框（focus 高亮）
        border = self._focus_border_color if self._focused else self._border_color
        border_w = 2 if self._focused else 1
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(border), border_w))
        painter.drawRoundedRect(
            rect.adjusted(border_w // 2, border_w // 2, -border_w // 2, -border_w // 2),
            self._radius,
            self._radius,
        )


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
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # 遮罩需要拦截鼠标：点击遮罩可关闭输入窗口，同时阻止与其他应用交互
        # 关键点：通过 SetWindowPos 保证输入窗口始终在遮罩之上，因此按钮仍可点击
        self.setFocusPolicy(Qt.NoFocus)
        
    def mousePressEvent(self, event):
        """点击遮罩时关闭输入窗口"""
        if self.on_click_callback:
            self.on_click_callback()
        event.accept()
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
        
        # 初始化金句服务
        self.quote_service = QuoteService()
        
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
        # 略微加大一点点，避免选项区文字拥挤/重叠
        # 冥想模式需要更高的窗口来显示计时器
        width = 1000
        height = 620  # 增加高度以容纳冥想计时器
        
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
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {bg_input};
                border: 1px solid rgba(94, 184, 217, 0.4);
                color: {fg_color};
            }}
            QPushButton:checked {{
                background: {bg_input};
                color: {accent_color};
                border: 1px solid {accent_color};
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
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {bg_input};
                border: 1px solid rgba(94, 184, 217, 0.4);
                color: {fg_color};
            }}
            QPushButton:checked {{
                background: {bg_input};
                color: {accent_color};
                border: 1px solid {accent_color};
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
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {bg_input};
                border: 1px solid rgba(94, 184, 217, 0.4);
                color: {fg_color};
            }}
            QPushButton:checked {{
                background: {bg_input};
                color: {accent_color};
                border: 1px solid {accent_color};
            }}
            QPushButton:!checked {{
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
            }}
        """)
        self.ticktick_tab_btn.clicked.connect(lambda: self._switch_platform("ticktick"))
        tab_layout.addWidget(self.ticktick_tab_btn)
        
        self.meditation_tab_btn = QPushButton("🧘 冥想")
        self.meditation_tab_btn.setCheckable(True)
        self.meditation_tab_btn.setChecked(False)
        self.meditation_tab_btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {bg_input};
                border: 1px solid rgba(94, 184, 217, 0.4);
                color: {fg_color};
            }}
            QPushButton:checked {{
                background: {bg_input};
                color: {accent_color};
                border: 1px solid {accent_color};
            }}
            QPushButton:!checked {{
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
            }}
        """)
        self.meditation_tab_btn.clicked.connect(lambda: self._switch_platform("meditation"))
        tab_layout.addWidget(self.meditation_tab_btn)
        
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
        # 这一行内容较多（状态/优先级/标签），整体间距调小避免挤压
        notion_options_layout.setSpacing(6)
        
        # 状态选择（改为按钮组）
        status_label = QLabel("状态:")
        # 增大字体，使用微软雅黑
        status_label.setStyleSheet(f"font-size: 13px; color: {fg_secondary}; min-width: 35px; font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;")
        notion_options_layout.addWidget(status_label)
        
        # 状态按钮组
        status_btn_group = QHBoxLayout()
        status_btn_group.setSpacing(3)
        status_btn_group.setContentsMargins(0, 0, 0, 0)
        self.notion_status_group = QButtonGroup()
        self.notion_status_buttons = {}
        status_options = ["待处理", "进行中", "已完成", "已搁置"]
        
        for i, option in enumerate(status_options):
            btn = SelectedDotButton(
                option,
                bg=bg_secondary,
                bg_checked=bg_input,
                fg=fg_secondary,
                fg_checked=fg_color,
                border=border_color,
                border_checked=accent_color,
                radius=6,
            )
            btn.setFixedHeight(28)
            # 更紧凑：固定宽度，避免按钮组占用过多空间导致整行拥挤
            btn.setFixedWidth(62)
            if i == 0:  # 默认选中"待处理"
                btn.setChecked(True)
            self.notion_status_group.addButton(btn, i)
            self.notion_status_buttons[option] = btn
            status_btn_group.addWidget(btn)
        
        notion_options_layout.addLayout(status_btn_group)
        
        # 优先级选择（改为按钮组）
        priority_label = QLabel("优先级:")
        # 增大字体，使用微软雅黑
        priority_label.setStyleSheet(f"font-size: 13px; color: {fg_secondary}; min-width: 42px; font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;")
        notion_options_layout.addWidget(priority_label)
        
        # 优先级按钮组
        priority_btn_group = QHBoxLayout()
        priority_btn_group.setSpacing(3)
        priority_btn_group.setContentsMargins(0, 0, 0, 0)
        self.notion_priority_group = QButtonGroup()
        self.notion_priority_buttons = {}
        priority_options = ["高", "中", "低"]
        
        for i, option in enumerate(priority_options):
            btn = SelectedDotButton(
                option,
                bg=bg_secondary,
                bg_checked=bg_input,
                fg=fg_secondary,
                fg_checked=fg_color,
                border=border_color,
                border_checked=accent_color,
                radius=6,
            )
            btn.setFixedHeight(28)
            btn.setFixedWidth(46)
            if i == 1:  # 默认选中"中"
                btn.setChecked(True)
            self.notion_priority_group.addButton(btn, i)
            self.notion_priority_buttons[option] = btn
            priority_btn_group.addWidget(btn)
        
        notion_options_layout.addLayout(priority_btn_group)
        
        # 标签输入
        tags_label_notion = QLabel("标签:")
        # 增大字体，使用微软雅黑
        tags_label_notion.setStyleSheet(f"font-size: 13px; color: {fg_secondary}; min-width: 35px; font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;")
        notion_options_layout.addWidget(tags_label_notion)

        # 标签快捷按钮（两种输入方式并行：按钮 + 输入框；支持同时选中）
        quick_tags_layout = QHBoxLayout()
        quick_tags_layout.setSpacing(3)
        quick_tags_layout.setContentsMargins(0, 0, 0, 0)
        self.notion_tag_quick_buttons = {}

        quick_tag_options = ["闪念", "AI峡谷"]
        for i, tag_name in enumerate(quick_tag_options):
            btn = SelectedDotButton(
                tag_name,
                bg=bg_secondary,
                bg_checked=bg_input,
                fg=fg_secondary,
                fg_checked=fg_color,
                border=border_color,
                border_checked=accent_color,
                radius=6,
            )
            btn.setFixedHeight(28)
            btn.setFixedWidth(72)
            btn.setChecked(True)  # 默认两个都选中
            self.notion_tag_quick_buttons[tag_name] = btn
            quick_tags_layout.addWidget(btn)

        notion_options_layout.addLayout(quick_tags_layout)

        # 标签输入框（支持空格输入多个标签；边框保持普通深色风格）
        self.notion_tags = QLineEdit()
        self.notion_tags.setText("")
        self.notion_tags.setPlaceholderText("可空格输入多个标签")
        self.notion_tags.setFixedHeight(28)
        # 标签输入宽度缩短30%
        self.notion_tags.setMinimumWidth(168)
        # 使用容器绘制圆角边框，避免右侧圆角在部分环境下丢失
        self._notion_tags_container = PlainLineEditContainer(
            self.notion_tags,
            bg_color=bg_input,
            border_color=border_color,
            focus_border_color=accent_color,
            text_color=fg_color,
            placeholder_color=fg_secondary,
            radius=6,
        )
        self._notion_tags_container.setFixedHeight(28)
        self._notion_tags_container.setMinimumWidth(182)
        notion_options_layout.addWidget(self._notion_tags_container, stretch=2)
        
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
        
        # 冥想选填项: 倒计时和正向计时（同一行）
        self.meditation_options = QWidget()
        meditation_options_layout = QHBoxLayout()
        meditation_options_layout.setContentsMargins(0, 0, 0, 0)
        meditation_options_layout.setSpacing(12)
        
        # 倒计时选项区域
        countdown_label = QLabel("倒计时:")
        countdown_label.setStyleSheet(f"font-size: 13px; color: {fg_secondary}; min-width: 60px; font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;")
        meditation_options_layout.addWidget(countdown_label)
        
        # 倒计时按钮组
        self.meditation_countdown_group = QButtonGroup()
        self.meditation_countdown_buttons = {}
        countdown_options = [
            ("45分钟", 45),
            ("15分钟", 15),
            ("10分钟", 10),
            ("5分钟", 5),
            ("自定义", None)  # None表示自定义
        ]
        
        for i, (text, minutes) in enumerate(countdown_options):
            btn = SelectedDotButton(
                text,
                bg=bg_secondary,
                bg_checked=bg_input,
                fg=fg_secondary,
                fg_checked=fg_color,
                border=border_color,
                border_checked=accent_color,
                radius=6,
            )
            btn.setFixedHeight(28)
            # 根据按钮文字调整宽度：5分钟稍窄一些，自定义稍宽一些
            if text == "5分钟":
                btn.setFixedWidth(65)
            elif text == "自定义":
                btn.setFixedWidth(75)
            else:
                btn.setFixedWidth(70)
            self.meditation_countdown_group.addButton(btn, i)
            self.meditation_countdown_buttons[text] = btn
            btn.minutes = minutes  # 存储分钟数
            btn.clicked.connect(lambda checked, b=btn: self._on_countdown_selected(b) if checked else None)
            meditation_options_layout.addWidget(btn)
        
        # 添加间距
        meditation_options_layout.addSpacing(20)
        
        # 正向计时选项区域
        timer_label = QLabel("正向计时:")
        timer_label.setStyleSheet(f"font-size: 13px; color: {fg_secondary}; min-width: 70px; font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;")
        meditation_options_layout.addWidget(timer_label)
        
        # 正向计时开始按钮
        self.meditation_timer_start_btn = SelectedDotButton(
            "开始",
            bg=bg_secondary,
            bg_checked=bg_input,
            fg=fg_secondary,
            fg_checked=accent_color,
            border=border_color,
            border_checked=accent_color,
            radius=6,
        )
        self.meditation_timer_start_btn.setFixedHeight(28)
        self.meditation_timer_start_btn.setFixedWidth(80)
        self.meditation_timer_start_btn.setCheckable(True)
        self.meditation_timer_start_btn.clicked.connect(self._on_timer_start)
        meditation_options_layout.addWidget(self.meditation_timer_start_btn)
        
        # 添加间距
        meditation_options_layout.addSpacing(20)
        
        # 查看金句按钮
        quote_view_label = QLabel("金句:")
        quote_view_label.setStyleSheet(f"font-size: 13px; color: {fg_secondary}; min-width: 45px; font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;")
        meditation_options_layout.addWidget(quote_view_label)
        
        self.meditation_quote_view_btn = SelectedDotButton(
            "💡 查看",
            bg=bg_secondary,
            bg_checked=bg_input,
            fg=fg_secondary,
            fg_checked=accent_color,
            border=border_color,
            border_checked=accent_color,
            radius=6,
        )
        self.meditation_quote_view_btn.setFixedHeight(28)
        self.meditation_quote_view_btn.setFixedWidth(80)
        self.meditation_quote_view_btn.setCheckable(True)  # 设置为可选中
        self.meditation_quote_view_btn.clicked.connect(self._on_view_quote)
        meditation_options_layout.addWidget(self.meditation_quote_view_btn)
        
        meditation_options_layout.addStretch()
        self.meditation_options.setLayout(meditation_options_layout)
        self.meditation_options.setVisible(False)
        
        # 添加到选项容器
        self.options_layout.addWidget(self.notion_options)
        self.options_layout.addWidget(self.flomo_options)
        self.options_layout.addWidget(self.ticktick_options)
        self.options_layout.addWidget(self.meditation_options)
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
        
        # ========== 冥想金句展示区域（默认隐藏）==========
        self.meditation_quote_widget = QWidget()
        self.meditation_quote_widget.setVisible(False)
        meditation_quote_layout = QVBoxLayout()
        meditation_quote_layout.setContentsMargins(0, 0, 0, 5)  # 上边距设为0，大幅向上移
        meditation_quote_layout.setSpacing(5)  # 最小化间距
        
        # 金句标题（更小）
        quote_title = QLabel("💡 每日智慧")
        quote_title.setStyleSheet(f"""
            QLabel {{
                color: {accent_color};
                font-size: 13px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
                padding: 0px;
                margin: 0px;
            }}
        """)
        quote_title.setAlignment(Qt.AlignCenter)
        meditation_quote_layout.addWidget(quote_title)
        
        # 金句显示（使用HTML格式，一个Label中显示金句和出处）
        self.meditation_quote_label = QLabel("正在加载金句...")
        self.meditation_quote_label.setStyleSheet(f"""
            QLabel {{
                color: {fg_color};
                background: {bg_input};
                border: 2px solid {accent_color};
                border-radius: 14px;
                padding: 30px 25px;
                min-height: 160px;
                max-height: 280px;
            }}
        """)
        self.meditation_quote_label.setAlignment(Qt.AlignCenter)
        self.meditation_quote_label.setWordWrap(True)
        self.meditation_quote_label.setTextFormat(Qt.RichText)
        meditation_quote_layout.addWidget(self.meditation_quote_label, stretch=3)
        
        # 保留author label用于代码兼容，但实际不显示
        self.meditation_quote_author = QLabel("")
        self.meditation_quote_author.setVisible(False)
        
        # 操作按钮行
        quote_btn_layout = QHBoxLayout()
        quote_btn_layout.setSpacing(10)  # 减小按钮间距
        quote_btn_layout.setContentsMargins(0, 3, 0, 0)  # 减小上边距
        quote_btn_layout.addStretch()
        
        # 上一条按钮
        self.quote_prev_btn = QPushButton("← 上一条")
        self.quote_prev_btn.setFixedHeight(32)  # 缩小按钮高度
        self.quote_prev_btn.setFixedWidth(90)  # 缩小按钮宽度
        self.quote_prev_btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {bg_input};
                color: {accent_color};
                border: 2px solid {accent_color};
            }}
        """)
        self.quote_prev_btn.clicked.connect(self._on_quote_previous)
        quote_btn_layout.addWidget(self.quote_prev_btn)
        
        # 随机按钮
        self.quote_random_btn = QPushButton("🎲 随机")
        self.quote_random_btn.setFixedHeight(32)
        self.quote_random_btn.setFixedWidth(90)
        self.quote_random_btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg_secondary};
                color: {fg_color};
                border: 1px solid {accent_color};
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {accent_color};
                color: white;
                border: 2px solid {accent_color};
            }}
        """)
        self.quote_random_btn.clicked.connect(self._on_quote_random)
        quote_btn_layout.addWidget(self.quote_random_btn)
        
        # 下一条按钮
        self.quote_next_btn = QPushButton("下一条 →")
        self.quote_next_btn.setFixedHeight(32)
        self.quote_next_btn.setFixedWidth(90)
        self.quote_next_btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {bg_input};
                color: {accent_color};
                border: 2px solid {accent_color};
            }}
        """)
        self.quote_next_btn.clicked.connect(self._on_quote_next)
        quote_btn_layout.addWidget(self.quote_next_btn)
        
        # 复制按钮
        self.quote_copy_btn = QPushButton("📋 复制")
        self.quote_copy_btn.setFixedHeight(32)
        self.quote_copy_btn.setFixedWidth(90)
        self.quote_copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {bg_input};
                color: {accent_color};
                border: 2px solid {accent_color};
            }}
        """)
        self.quote_copy_btn.clicked.connect(self._on_quote_copy)
        quote_btn_layout.addWidget(self.quote_copy_btn)
        
        # 同步flomo按钮
        self.quote_sync_flomo_btn = QPushButton("🏷️ 同步flomo")
        self.quote_sync_flomo_btn.setFixedHeight(32)
        self.quote_sync_flomo_btn.setFixedWidth(110)
        self.quote_sync_flomo_btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg_secondary};
                color: {fg_secondary};
                border: 1px solid {border_color};
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {bg_input};
                color: {accent_color};
                border: 2px solid {accent_color};
            }}
        """)
        self.quote_sync_flomo_btn.clicked.connect(self._on_quote_sync_flomo)
        quote_btn_layout.addWidget(self.quote_sync_flomo_btn)
        
        quote_btn_layout.addStretch()
        meditation_quote_layout.addLayout(quote_btn_layout)
        
        self.meditation_quote_widget.setLayout(meditation_quote_layout)
        content_layout.addWidget(self.meditation_quote_widget, stretch=1)
        
        # ========== 冥想计时器显示区域（默认隐藏）==========
        self.meditation_timer_widget = QWidget()
        self.meditation_timer_widget.setVisible(False)
        meditation_timer_layout = QVBoxLayout()
        meditation_timer_layout.setContentsMargins(0, 20, 0, 20)
        meditation_timer_layout.setSpacing(20)
        
        # 计时器标题
        self.meditation_title = QLabel("🧘 倒计时")
        self.meditation_title.setStyleSheet(f"""
            QLabel {{
                color: {accent_color};
                font-size: 22px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            }}
        """)
        self.meditation_title.setAlignment(Qt.AlignCenter)
        meditation_timer_layout.addWidget(self.meditation_title)
        
        # 时间显示（超大号粗体）
        self.meditation_time_label = QLabel("00:00:00")
        self.meditation_time_label.setStyleSheet(f"""
            QLabel {{
                color: {fg_color};
                font-size: 90px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                letter-spacing: 8px;
                background: {bg_input};
                border: 2px solid {accent_color};
                border-radius: 20px;
                padding: 30px;
            }}
        """)
        self.meditation_time_label.setAlignment(Qt.AlignCenter)
        meditation_timer_layout.addWidget(self.meditation_time_label, stretch=1)
        
        # 控制按钮
        meditation_btn_layout = QHBoxLayout()
        meditation_btn_layout.setSpacing(15)
        meditation_btn_layout.addStretch()
        
        # 暂停/继续按钮
        self.meditation_pause_btn = QPushButton("⏸ 暂停")
        self.meditation_pause_btn.setFixedSize(140, 50)
        self.meditation_pause_btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent_color};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            }}
            QPushButton:hover {{
                background: {accent_secondary};
            }}
            QPushButton:pressed {{
                background: {accent_glow};
            }}
        """)
        self.meditation_pause_btn.clicked.connect(self._toggle_meditation_pause)
        meditation_btn_layout.addWidget(self.meditation_pause_btn)
        
        # 停止按钮
        self.meditation_stop_btn = QPushButton("⏹ 停止")
        self.meditation_stop_btn.setFixedSize(140, 50)
        self.meditation_stop_btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg_input};
                color: {fg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            }}
            QPushButton:hover {{
                background: {bg_secondary};
                border: 1px solid {accent_color};
            }}
        """)
        self.meditation_stop_btn.clicked.connect(self._stop_meditation)
        meditation_btn_layout.addWidget(self.meditation_stop_btn)
        
        meditation_btn_layout.addStretch()
        meditation_timer_layout.addLayout(meditation_btn_layout)
        
        self.meditation_timer_widget.setLayout(meditation_timer_layout)
        content_layout.addWidget(self.meditation_timer_widget, stretch=1)
        
        # 冥想计时器状态
        self.meditation_timer = QTimer(self)
        self.meditation_timer.timeout.connect(self._update_meditation_time)
        self.meditation_is_countdown = True
        self.meditation_total_seconds = 0
        self.meditation_current_seconds = 0
        self.meditation_is_running = False
        
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
                border: 1px solid rgba(94, 184, 217, 0.5);
            }}
        """)
        cancel_btn.clicked.connect(self._cancel)
        button_layout.addWidget(cancel_btn)
        
        # 发送按钮（流动渐变边框，酷炫 AI 氛围）
        send_btn = FlowGradientButton(
            "🚀 发送",
            bg_color=bg_input,
            text_color=fg_color,
            gradient_colors=[
                (168, 85, 247, 230),   # 紫
                (34, 197, 94, 230),    # 绿
                (59, 130, 246, 230),   # 蓝
            ],
        )
        send_btn.setFixedSize(120, 44)
        send_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
                background: transparent;
            }
        """)
        send_btn.clicked.connect(self._submit_content)
        
        # 为发送按钮添加柔和发光效果（AI风格）
        send_glow = QGraphicsDropShadowEffect()
        send_glow.setBlurRadius(25)
        send_glow.setColor(QColor(94, 184, 217, 100))  # 更柔和的发光
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
        # 默认：黑色，100%不透明（alpha=255）
        mask_color_rgb = self.config.get('mask_color', self.config.get('ui.mask_color', [0, 0, 0]))  # 默认黑色
        mask_alpha = self.config.get('mask_alpha', self.config.get('ui.mask_alpha', 255))

        # 兼容：如果传入的是 0-100（百分比），转换为 0-255（alpha）
        try:
            if isinstance(mask_alpha, str):
                mask_alpha = int(mask_alpha.strip())
            if isinstance(mask_alpha, (int, float)) and mask_alpha <= 100:
                mask_alpha = int((max(0, min(100, mask_alpha)) / 100) * 255)
            mask_alpha = int(max(0, min(255, mask_alpha)))
        except Exception:
            mask_alpha = 255
        
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
            
            # 保存引用以便后续关闭
            self._mask_widgets.append(mask)
            
            logger.debug(f"遮罩已创建: {geometry}, 颜色: {mask_color}, 透明度: {mask_alpha}, 可见: {mask.isVisible()}")
        
        # 延迟确保输入窗口在遮罩上方
        # 使用多次延迟和 Windows API 确保窗口层级正确
        def ensure_on_top():
            try:
                import ctypes
                hwnd = int(self.winId())
                # 先确保输入窗口为 TOPMOST（并保持激活能力）
                ctypes.windll.user32.SetWindowPos(
                    hwnd,
                    -2,  # HWND_TOPMOST
                    0, 0, 0, 0,
                    0x0001 | 0x0002  # SWP_NOMOVE | SWP_NOSIZE
                )

                # 再把所有遮罩窗口放到“输入窗口之下”（同为TOPMOST，但Z序更低）
                for mask in self._mask_widgets:
                    if mask.isVisible():
                        mask_hwnd = int(mask.winId())
                        ctypes.windll.user32.SetWindowPos(
                            mask_hwnd,
                            hwnd,  # 插入到输入窗口之后 => 在输入窗口下方
                            0, 0, 0, 0,
                            0x0001 | 0x0002 | 0x0010  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
                        )
            except Exception as e:
                logger.warning(f"设置窗口层级失败: {e}")
            
            self.raise_()
            self.activateWindow()
        
        # 遮罩创建完成，窗口层级将在show_at_center中统一设置
        # 减少延迟调用，避免IME问题
        logger.info(f"遮罩已创建，数量: {len(self._mask_widgets)}, 屏幕数: {len(screens)}")
    
    def _remove_overlay_mask(self):
        """移除全屏遮罩"""
        if self._mask_widgets:
            for mask in self._mask_widgets:
                try:
                    if mask.isVisible():
                        mask.hide()
                    mask.close()
                    mask.deleteLater()
                except Exception as e:
                    logger.debug(f"移除遮罩时出错: {e}")
            self._mask_widgets.clear()
            # 强制清理，避免内存泄漏
            try:
                QApplication.processEvents()
            except:
                pass
    
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
        # 先移除旧的遮罩（如果存在），避免累积
        if self._mask_widgets:
            self._remove_overlay_mask()
        
        # 只有置顶时才创建遮罩（在显示窗口之前创建）
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
        self.raise_()
        self.activateWindow()
        
        # 优化：减少延迟调用次数，避免IME丢失焦点
        def ensure_on_top_and_focus():
            try:
                import ctypes
                hwnd = int(self.winId())
                
                # 只在置顶模式下使用TOPMOST，避免影响IME
                if self._is_always_on_top:
                    # 设置输入窗口为TOPMOST
                    ctypes.windll.user32.SetWindowPos(
                        hwnd,
                        -2,  # HWND_TOPMOST
                        0, 0, 0, 0,
                        0x0001 | 0x0002  # SWP_NOMOVE | SWP_NOSIZE
                    )
                    
                    # 确保遮罩在输入窗口下方
                    for mask in self._mask_widgets:
                        if mask.isVisible():
                            try:
                                mask_hwnd = int(mask.winId())
                                ctypes.windll.user32.SetWindowPos(
                                    mask_hwnd,
                                    hwnd,  # 插入到输入窗口之后
                                    0, 0, 0, 0,
                                    0x0001 | 0x0002 | 0x0010  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
                                )
                            except:
                                pass
                
                # 激活窗口（只调用一次，避免IME问题）
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                
                # 聚焦到输入框（使用Qt的方式，更温和）
                QTimer.singleShot(100, lambda: self.text_edit.setFocus())
            except Exception as e:
                logger.warning(f"设置窗口层级失败: {e}")
                # 降级方案：使用Qt方式聚焦
                QTimer.singleShot(100, lambda: self.text_edit.setFocus())
        
        # 只调用一次延迟，减少对IME的影响
        QTimer.singleShot(50, ensure_on_top_and_focus)
        
        logger.info(f"快速输入窗口已显示在屏幕: {screen.name()}, 遮罩数量: {len(self._mask_widgets)}")
    
    def hide(self):
        """隐藏窗口并移除遮罩"""
        self._remove_overlay_mask()
        # 注意：不停止冥想计时器，让它在后台继续运行
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
            self.meditation_tab_btn.setChecked(False)
            self.notion_options.setVisible(True)
            self.flomo_options.setVisible(False)
            self.ticktick_options.setVisible(False)
            self.meditation_options.setVisible(False)
            self.options_container.setVisible(True)  # 显示选项容器
            # 隐藏冥想相关widget，显示输入框
            self.meditation_timer_widget.setVisible(False)
            self.meditation_quote_widget.setVisible(False)
            self.text_edit.setVisible(True)
            self.text_edit.setPlaceholderText("输入你的灵感...")
            logger.info("切换到Notion模式")
        elif platform == "flomo":
            self.notion_tab_btn.setChecked(False)
            self.flomo_tab_btn.setChecked(True)
            self.ticktick_tab_btn.setChecked(False)
            self.meditation_tab_btn.setChecked(False)
            self.notion_options.setVisible(False)
            self.flomo_options.setVisible(True)
            self.ticktick_options.setVisible(False)
            self.meditation_options.setVisible(False)
            self.options_container.setVisible(True)  # 显示选项容器
            # 隐藏冥想相关widget，显示输入框
            self.meditation_timer_widget.setVisible(False)
            self.meditation_quote_widget.setVisible(False)
            self.text_edit.setVisible(True)
            # 如果标签为空，设置为默认值
            if not self.flomo_tags.text().strip():
                self.flomo_tags.setText("闪念 QuickNote AI")
            self.text_edit.setPlaceholderText("输入金句、知识或方法论...")
            logger.info("切换到Flomo模式")
        elif platform == "ticktick":
            self.notion_tab_btn.setChecked(False)
            self.flomo_tab_btn.setChecked(False)
            self.ticktick_tab_btn.setChecked(True)
            self.meditation_tab_btn.setChecked(False)
            self.notion_options.setVisible(False)
            self.flomo_options.setVisible(False)
            self.ticktick_options.setVisible(False)  # TickTick无选填项，隐藏
            self.meditation_options.setVisible(False)
            self.options_container.setVisible(False)  # 隐藏整个选项容器，减少间隔
            # 隐藏冥想相关widget，显示输入框
            self.meditation_timer_widget.setVisible(False)
            self.meditation_quote_widget.setVisible(False)
            self.text_edit.setVisible(True)
            self.text_edit.setPlaceholderText("输入待办任务...")
            logger.info("切换到滴答清单模式")
        elif platform == "meditation":
            self.notion_tab_btn.setChecked(False)
            self.flomo_tab_btn.setChecked(False)
            self.ticktick_tab_btn.setChecked(False)
            self.meditation_tab_btn.setChecked(True)
            self.notion_options.setVisible(False)
            self.flomo_options.setVisible(False)
            self.ticktick_options.setVisible(False)
            self.meditation_options.setVisible(True)
            
            # 如果计时器正在运行或已暂停，显示计时器；否则显示金句和选项
            if self.meditation_is_running or self.meditation_current_seconds > 0:
                # 正在计时或已暂停，显示计时器
                self.options_container.setVisible(False)
                self.text_edit.setVisible(False)
                self.meditation_quote_widget.setVisible(False)
                self.meditation_timer_widget.setVisible(True)
                logger.info("切换到冥想模式（计时器运行中）")
            else:
                # 未开始计时，显示金句和选项
                self.options_container.setVisible(True)
                self.text_edit.setVisible(False)  # 不显示输入框
                self.meditation_quote_widget.setVisible(True)  # 显示金句
                self.meditation_timer_widget.setVisible(False)
                # 只显示默认文字，不自动调用API
                self._show_default_quote()
                # 重置所有按钮状态
                for btn in self.meditation_countdown_buttons.values():
                    btn.setChecked(False)
                self.meditation_timer_start_btn.setChecked(False)
                self.meditation_quote_view_btn.setChecked(False)
                logger.info("切换到冥想模式（默认状态）")
    
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
                
                # 标签：按钮选择（支持多选）+ 输入框（空格分隔）合并保存
                combined_tags = []
                try:
                    for btn in getattr(self, "notion_tag_quick_buttons", {}).values():
                        if btn and btn.isChecked():
                            combined_tags.append(btn.text())
                except Exception:
                    pass

                tags_text = self.notion_tags.text().strip()
                if tags_text:
                    combined_tags.extend([tag.strip() for tag in tags_text.split() if tag.strip()])

                # 去重/规范化（移除多余#）
                normalized = []
                seen = set()
                for t in combined_tags:
                    nt = (t or "").strip().lstrip("#")
                    if nt and nt not in seen:
                        normalized.append(nt)
                        seen.add(nt)
                if normalized:
                    extra_params["tags"] = normalized
                
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
                # 重置标签：输入框清空 + 默认选中“闪念”
                self.notion_tags.setText("")
                if hasattr(self, "notion_tag_quick_buttons"):
                    for btn in self.notion_tag_quick_buttons.values():
                        if btn:
                            btn.setChecked(True)
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
    
    def _on_countdown_selected(self, button):
        """倒计时选择处理"""
        if button.text() == "自定义":
            # 弹出输入框让用户输入分钟数
            minutes, ok = QInputDialog.getInt(
                self,
                "自定义倒计时",
                "请输入倒计时分钟数:",
                value=15,
                min=1,
                max=999
            )
            if not ok:
                button.setChecked(False)
                return
            total_seconds = minutes * 60
        else:
            # 使用预设的分钟数
            total_seconds = button.minutes * 60
        
        # 取消其他按钮的选中状态（包括"查看"按钮）
        for btn in self.meditation_countdown_buttons.values():
            if btn != button:
                btn.setChecked(False)
        self.meditation_timer_start_btn.setChecked(False)
        self.meditation_quote_view_btn.setChecked(False)
        
        # 开始倒计时（在当前窗口显示）
        self._start_meditation_timer(is_countdown=True, total_seconds=total_seconds)
        
        logger.info(f"开始倒计时: {total_seconds}秒")
    
    def _on_timer_start(self):
        """正向计时开始处理"""
        if self.meditation_timer_start_btn.isChecked():
            # 取消其他按钮的选中状态
            for btn in self.meditation_countdown_buttons.values():
                btn.setChecked(False)
            self.meditation_quote_view_btn.setChecked(False)
            
            # 开始正向计时（在当前窗口显示）
            self._start_meditation_timer(is_countdown=False, total_seconds=0)
            
            logger.info("开始正向计时")
            
            # 重置按钮状态
            self.meditation_timer_start_btn.setChecked(False)
    
    def _on_view_quote(self):
        """查看金句"""
        try:
            # 只有当按钮被选中时才执行
            if not self.meditation_quote_view_btn.isChecked():
                return
            
            # 取消其他按钮的选中状态
            for btn in self.meditation_countdown_buttons.values():
                btn.setChecked(False)
            self.meditation_timer_start_btn.setChecked(False)
            
            # 显示金句区域，隐藏计时器
            if self.target_platform == "meditation":
                self.options_container.setVisible(True)
                self.text_edit.setVisible(False)
                self.meditation_quote_widget.setVisible(True)
                self.meditation_timer_widget.setVisible(False)
                
                # 显示"正在加载..."
                html_text = '''
                    <div style="text-align: center; line-height: 2.2; font-size: 20px; color: #e8e8e8; font-weight: 500;">
                        正在加载金句...
                    </div>
                    <div style="text-align: right; margin-top: 30px; font-size: 13px; color: #888888; padding-right: 12px;">
                        —— AI思考中
                    </div>
                '''
                self.meditation_quote_label.setText(html_text)
                
                # 异步加载金句
                from PyQt5.QtCore import QThread
                
                class ViewQuoteLoaderThread(QThread):
                    def __init__(self, quote_service, parent=None):
                        super().__init__(parent)
                        self.quote_service = quote_service
                        self.result = None
                    
                    def run(self):
                        try:
                            # 优先使用当前金句
                            self.result = self.quote_service.get_current_quote()
                            if not self.result:
                                # 如果没有，则获取随机金句
                                self.result = self.quote_service.get_random_quote()
                        except Exception as e:
                            logger.error(f"查看金句失败: {e}", exc_info=True)
                            self.result = None
                
                # 创建线程
                self._view_quote_loader_thread = ViewQuoteLoaderThread(self.quote_service, self)
                self._view_quote_loader_thread.finished.connect(
                    lambda: self._on_view_quote_loaded(self._view_quote_loader_thread.result)
                )
                self._view_quote_loader_thread.start()
                
                logger.info("点击查看金句，开始加载")
        except Exception as e:
            logger.error(f"查看金句失败: {e}", exc_info=True)
    
    def _on_view_quote_loaded(self, quote_data):
        """查看金句加载完成的回调"""
        if quote_data:
            self._load_quote(quote_data)
            logger.info("查看金句加载完成")
        else:
            html_text = '''
                <div style="text-align: center; line-height: 2.2; font-size: 20px; color: #e8e8e8; font-weight: 500;">
                    加载金句失败，请稍后重试
                </div>
                <div style="text-align: right; margin-top: 30px; font-size: 13px; color: #888888; padding-right: 12px;">
                    —— 系统
                </div>
            '''
            self.meditation_quote_label.setText(html_text)
    
    def _start_meditation_timer(self, is_countdown=True, total_seconds=0):
        """开始冥想计时器"""
        self.meditation_is_countdown = is_countdown
        self.meditation_total_seconds = total_seconds
        self.meditation_current_seconds = total_seconds if is_countdown else 0
        self.meditation_is_running = True
        
        # 更新UI
        title_text = "倒计时" if is_countdown else "正向计时"
        self.meditation_title.setText(f"🧘 {title_text}")
        self.meditation_time_label.setText(self._format_meditation_time(self.meditation_current_seconds))
        self.meditation_pause_btn.setText("⏸ 暂停")
        
        # 只在冥想标签页时显示计时器
        if self.target_platform == "meditation":
            # 隐藏输入框、选项和金句，显示计时器
            self.text_edit.setVisible(False)
            self.options_container.setVisible(False)
            self.meditation_quote_widget.setVisible(False)  # 修复：隐藏金句widget
            self.meditation_timer_widget.setVisible(True)
        
        # 开始计时（独立运行，不受标签切换影响）
        self.meditation_timer.start(1000)  # 每秒更新一次
        
        logger.info(f"冥想计时器已启动: {'倒计时' if is_countdown else '正向计时'}, 初始值: {total_seconds}秒")
    
    def _update_meditation_time(self):
        """更新冥想计时器时间（独立运行，不受标签切换影响）"""
        if not self.meditation_is_running:
            return
        
        if self.meditation_is_countdown:
            self.meditation_current_seconds -= 1
            if self.meditation_current_seconds <= 0:
                self.meditation_current_seconds = 0
                self.meditation_timer.stop()
                self.meditation_is_running = False
                self.meditation_pause_btn.setText("▶ 继续")
                logger.info("倒计时结束")
                
                # 倒计时结束后，如果在冥想标签页，显示默认金句
                if self.target_platform == "meditation":
                    self._finish_meditation()
        else:
            self.meditation_current_seconds += 1
        
        # 更新时间显示（始终更新，即使不在冥想标签页）
        self.meditation_time_label.setText(self._format_meditation_time(self.meditation_current_seconds))
    
    def _format_meditation_time(self, seconds):
        """格式化冥想时间显示"""
        if self.meditation_is_countdown:
            if seconds <= 0:
                return "00:00:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _toggle_meditation_pause(self):
        """切换冥想计时器的暂停/继续"""
        if self.meditation_is_running:
            self.meditation_timer.stop()
            self.meditation_is_running = False
            self.meditation_pause_btn.setText("▶ 继续")
            logger.info("冥想计时器已暂停")
        else:
            # 检查倒计时是否已结束
            if self.meditation_is_countdown and self.meditation_current_seconds <= 0:
                logger.info("倒计时已结束，无法继续")
                return
            self.meditation_timer.start(1000)
            self.meditation_is_running = True
            self.meditation_pause_btn.setText("⏸ 暂停")
            logger.info("冥想计时器已继续")
    
    def _stop_meditation(self):
        """停止冥想计时器（手动结束）"""
        self.meditation_timer.stop()
        self.meditation_is_running = False
        self.meditation_current_seconds = 0
        
        # 重置所有倒计时按钮的选中状态
        for btn in self.meditation_countdown_buttons.values():
            btn.setChecked(False)
        
        # 只在冥想标签页时恢复UI，显示默认金句
        if self.target_platform == "meditation":
            self._finish_meditation()
        
        logger.info("冥想计时器已停止")
    
    def _finish_meditation(self):
        """冥想结束后的UI处理（显示默认金句）"""
        try:
            # 隐藏计时器，显示金句和选项
            self.meditation_timer_widget.setVisible(False)
            self.text_edit.setVisible(False)  # 不显示输入框
            self.options_container.setVisible(True)
            self.meditation_quote_widget.setVisible(True)
            
            # 显示默认金句
            self._show_default_quote()
            
            # 重置所有按钮状态
            for btn in self.meditation_countdown_buttons.values():
                btn.setChecked(False)
            self.meditation_timer_start_btn.setChecked(False)
            self.meditation_quote_view_btn.setChecked(False)
            
            logger.info("冥想结束，显示默认金句")
        except Exception as e:
            logger.error(f"冥想结束处理失败: {e}", exc_info=True)
    
    def focusOutEvent(self, event):
        """失去焦点时不自动隐藏（用户可能需要切换窗口）"""
        # 不再自动隐藏，让用户主动关闭
        super().focusOutEvent(event)
    
    # ========== 金句相关方法 ==========
    
    def _show_default_quote(self):
        """显示默认金句文字（不调用API）"""
        try:
            # 显示默认文字（使用HTML格式，金句和出处分开样式）
            default_quote = "厉行价值创造，守正向上，一起感受文字力量......"
            default_author = "—— QuickNote AI"
            html_text = f'''
                <div style="text-align: center; line-height: 2.2; font-size: 20px; color: #e8e8e8; font-weight: 500;">
                    {default_quote}
                </div>
                <div style="text-align: right; margin-top: 30px; font-size: 13px; color: #888888; padding-right: 12px;">
                    {default_author}
                </div>
            '''
            self.meditation_quote_label.setText(html_text)
            logger.info("显示默认金句文字")
        except Exception as e:
            logger.error(f"显示默认金句失败: {e}", exc_info=True)
    
    def _load_quote(self, quote_data=None):
        """加载并显示金句（使用HTML格式）"""
        try:
            if quote_data is None:
                quote_data = self.quote_service.get_current_quote()
                if not quote_data:
                    quote_data = self.quote_service.get_random_quote()
            
            if quote_data:
                # 金句和出处使用HTML格式显示
                quote_text = quote_data["quote"]
                author_text = f"—— {quote_data['author']}"
                if "category" in quote_data and quote_data["category"]:
                    author_text += f"  ·  {quote_data['category']}"
                
                # 使用HTML格式，金句居中大字号，出处右下角小字号灰色
                html_text = f'''
                    <div style="text-align: center; line-height: 2.2; font-size: 20px; color: #e8e8e8; font-weight: 500;">
                        {quote_text}
                    </div>
                    <div style="text-align: right; margin-top: 30px; font-size: 13px; color: #888888; padding-right: 12px;">
                        {author_text}
                    </div>
                '''
                self.meditation_quote_label.setText(html_text)
                logger.info(f"加载金句: {quote_data['quote'][:30]}...")
        except Exception as e:
            logger.error(f"加载金句失败: {e}", exc_info=True)
            html_text = '''
                <div style="text-align: center; line-height: 2.2; font-size: 20px; color: #e8e8e8; font-weight: 500;">
                    加载金句失败，请点击随机按钮重试
                </div>
                <div style="text-align: right; margin-top: 30px; font-size: 13px; color: #888888; padding-right: 12px;">
                    —— 系统
                </div>
            '''
            self.meditation_quote_label.setText(html_text)
    
    def _on_quote_previous(self):
        """显示上一条金句"""
        try:
            quote_data = self.quote_service.get_previous_quote()
            if quote_data:
                self._load_quote(quote_data)
                logger.info("切换到上一条金句")
        except Exception as e:
            logger.error(f"获取上一条金句失败: {e}", exc_info=True)
    
    def _on_quote_next(self):
        """显示下一条金句（异步加载，提升响应速度）"""
        try:
            # 禁用按钮，防止重复点击
            self.quote_next_btn.setEnabled(False)
            self.quote_next_btn.setText("加载中...")
            
            # 使用线程安全的信号机制
            from PyQt5.QtCore import QThread
            
            class QuoteLoaderThread(QThread):
                def __init__(self, quote_service, parent=None):
                    super().__init__(parent)
                    self.quote_service = quote_service
                    self.result = None
                
                def run(self):
                    try:
                        self.result = self.quote_service.get_next_quote()
                    except Exception as e:
                        logger.error(f"获取下一条金句失败: {e}", exc_info=True)
                        self.result = None
            
            # 创建线程
            self._quote_loader_thread = QuoteLoaderThread(self.quote_service, self)
            self._quote_loader_thread.finished.connect(
                lambda: self._on_next_quote_loaded(self._quote_loader_thread.result)
            )
            self._quote_loader_thread.start()
            
        except Exception as e:
            logger.error(f"获取下一条金句失败: {e}", exc_info=True)
            self.quote_next_btn.setEnabled(True)
            self.quote_next_btn.setText("下一条 →")
    
    def _on_next_quote_loaded(self, quote_data):
        """下一条金句加载完成的回调"""
        self.quote_next_btn.setEnabled(True)
        self.quote_next_btn.setText("下一条 →")
        if quote_data:
            self._load_quote(quote_data)
            logger.info("切换到下一条金句")
    
    def _on_quote_random(self):
        """获取随机金句（异步加载，提升响应速度）"""
        try:
            # 显示加载提示
            html_text = '''
                <div style="text-align: center; line-height: 2.2; font-size: 20px; color: #e8e8e8; font-weight: 500;">
                    正在生成金句...
                </div>
                <div style="text-align: right; margin-top: 30px; font-size: 13px; color: #888888; padding-right: 12px;">
                    —— AI思考中
                </div>
            '''
            self.meditation_quote_label.setText(html_text)
            
            # 禁用按钮，防止重复点击
            self.quote_random_btn.setEnabled(False)
            self.quote_random_btn.setText("生成中...")
            
            # 使用线程安全的信号机制
            from PyQt5.QtCore import QThread
            
            class RandomQuoteLoaderThread(QThread):
                def __init__(self, quote_service, parent=None):
                    super().__init__(parent)
                    self.quote_service = quote_service
                    self.result = None
                
                def run(self):
                    try:
                        self.result = self.quote_service.get_random_quote()
                    except Exception as e:
                        logger.error(f"获取随机金句失败: {e}", exc_info=True)
                        self.result = None
            
            # 创建线程
            self._random_quote_loader_thread = RandomQuoteLoaderThread(self.quote_service, self)
            self._random_quote_loader_thread.finished.connect(
                lambda: self._on_random_quote_loaded(self._random_quote_loader_thread.result)
            )
            self._random_quote_loader_thread.start()
            
        except Exception as e:
            logger.error(f"获取随机金句失败: {e}", exc_info=True)
            html_text = '''
                <div style="text-align: center; line-height: 2.2; font-size: 20px; color: #e8e8e8; font-weight: 500;">
                    获取金句失败，请稍后重试
                </div>
                <div style="text-align: right; margin-top: 30px; font-size: 13px; color: #888888; padding-right: 12px;">
                    —— 系统
                </div>
            '''
            self.meditation_quote_label.setText(html_text)
            self.quote_random_btn.setEnabled(True)
            self.quote_random_btn.setText("🎲 随机")
    
    def _on_random_quote_loaded(self, quote_data):
        """随机金句加载完成的回调"""
        self.quote_random_btn.setEnabled(True)
        self.quote_random_btn.setText("🎲 随机")
        if quote_data:
            self._load_quote(quote_data)
            logger.info("生成随机金句成功")
        else:
            html_text = '''
                <div style="text-align: center; line-height: 2.2; font-size: 20px; color: #e8e8e8; font-weight: 500;">
                    获取金句失败，请稍后重试
                </div>
                <div style="text-align: right; margin-top: 30px; font-size: 13px; color: #888888; padding-right: 12px;">
                    —— 系统
                </div>
            '''
            self.meditation_quote_label.setText(html_text)
    
    def _on_quote_copy(self):
        """复制金句到剪贴板"""
        try:
            quote_text = self.quote_service.get_quote_text()
            if quote_text:
                clipboard = QApplication.clipboard()
                clipboard.setText(quote_text)
                
                # 临时显示复制成功提示
                original_text = self.quote_copy_btn.text()
                self.quote_copy_btn.setText("✓ 已复制")
                
                # 2秒后恢复原文本
                QTimer.singleShot(2000, lambda: self.quote_copy_btn.setText(original_text))
                
                logger.info(f"已复制金句到剪贴板: {quote_text[:30]}...")
        except Exception as e:
            logger.error(f"复制金句失败: {e}", exc_info=True)
    
    def _on_quote_sync_flomo(self):
        """同步金句到flomo"""
        try:
            current_quote = self.quote_service.get_current_quote()
            if not current_quote:
                logger.warning("没有可同步的金句")
                return
            
            # 格式化金句内容
            quote_content = f"{current_quote['quote']}\n\n—— {current_quote['author']}"
            if current_quote.get('category'):
                quote_content += f" · {current_quote['category']}"
            
            # 构建flomo标签（包含分类和固定标签）
            tags = "Quick_Note_AI 智慧金句"
            if current_quote.get('category'):
                tags += f" {current_quote['category']}"
            
            # 发送到flomo（使用现有的content_submitted信号）
            extra_params = {
                "tags": tags
            }
            
            # 发出提交信号
            self.content_submitted.emit("flomo", quote_content, extra_params)
            
            # 临时显示同步成功提示
            original_text = self.quote_sync_flomo_btn.text()
            self.quote_sync_flomo_btn.setText("✓ 已同步")
            
            # 2秒后恢复原文本
            QTimer.singleShot(2000, lambda: self.quote_sync_flomo_btn.setText(original_text))
            
            logger.info(f"已同步金句到flomo: {current_quote['quote'][:30]}... (标签: {tags})")
        except Exception as e:
            logger.error(f"同步金句到flomo失败: {e}", exc_info=True)
            # 显示错误提示
            original_text = self.quote_sync_flomo_btn.text()
            self.quote_sync_flomo_btn.setText("✗ 同步失败")
            QTimer.singleShot(2000, lambda: self.quote_sync_flomo_btn.setText(original_text))
