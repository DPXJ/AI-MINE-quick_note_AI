"""快捷键输入控件"""
from PyQt5.QtWidgets import QLineEdit, QPushButton, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeyEvent
from loguru import logger


class HotkeyInput(QWidget):
    """快捷键输入控件"""
    
    # 信号：快捷键改变
    hotkey_changed = pyqtSignal(str)
    
    def __init__(self, default_hotkey: str = "", parent=None):
        """
        初始化快捷键输入控件
        
        Args:
            default_hotkey: 默认快捷键
            parent: 父窗口
        """
        super().__init__(parent)
        self.default_hotkey = default_hotkey
        self.current_keys = set()
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 输入框（只读，显示当前快捷键）
        self.input = QLineEdit()
        self.input.setText(self.default_hotkey)
        self.input.setReadOnly(True)
        self.input.setPlaceholderText("点击'录制'按钮，然后按下快捷键")
        self.input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ccc;
                border-radius: 4px;
                background: #f9f9f9;
                font-size: 14px;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #007acc;
                background: white;
            }
        """)
        layout.addWidget(self.input, stretch=1)
        
        # 录制按钮
        self.record_btn = QPushButton("🎙️ 录制")
        self.record_btn.setCheckable(True)
        self.record_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 15px;
                background: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #005a9e;
            }
            QPushButton:checked {
                background: #d9534f;
            }
        """)
        self.record_btn.clicked.connect(self._toggle_recording)
        layout.addWidget(self.record_btn)
        
        # 重置按钮
        self.reset_btn = QPushButton("🔄 重置")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 15px;
                background: #5cb85c;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #4cae4c;
            }
        """)
        self.reset_btn.clicked.connect(self._reset_hotkey)
        layout.addWidget(self.reset_btn)
        
        self.setLayout(layout)
        self.recording = False
    
    def _toggle_recording(self, checked):
        """切换录制状态"""
        self.recording = checked
        if checked:
            self.record_btn.setText("⏹️ 停止")
            self.input.setPlaceholderText("请按下快捷键组合...")
            self.input.clear()
            self.input.setFocus()
            self.current_keys.clear()
            logger.info("开始录制快捷键")
        else:
            self.record_btn.setText("🎙️ 录制")
            self.input.setPlaceholderText("点击'录制'按钮，然后按下快捷键")
            logger.info("停止录制快捷键")
    
    def _reset_hotkey(self):
        """重置快捷键"""
        self.input.setText(self.default_hotkey)
        self.hotkey_changed.emit(self.default_hotkey)
        logger.info(f"快捷键已重置为: {self.default_hotkey}")
    
    def keyPressEvent(self, event: QKeyEvent):
        """按键按下事件"""
        if not self.recording:
            super().keyPressEvent(event)
            return
        
        key = event.key()
        
        # 忽略单独的修饰键
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return
        
        # 收集修饰键
        modifiers = []
        if event.modifiers() & Qt.ControlModifier:
            modifiers.append("ctrl")
        if event.modifiers() & Qt.ShiftModifier:
            modifiers.append("shift")
        if event.modifiers() & Qt.AltModifier:
            modifiers.append("alt")
        if event.modifiers() & Qt.MetaModifier:
            modifiers.append("cmd")
        
        # 获取按键名称
        key_name = self._get_key_name(key)
        if not key_name:
            return
        
        # 构建快捷键字符串
        parts = modifiers + [key_name]
        hotkey = "+".join(parts)
        
        # 显示并保存
        self.input.setText(hotkey)
        self.hotkey_changed.emit(hotkey)
        
        # 自动停止录制
        self.record_btn.setChecked(False)
        self._toggle_recording(False)
        
        logger.info(f"录制到快捷键: {hotkey}")
    
    def _get_key_name(self, key):
        """获取按键名称"""
        # 字母和数字
        if Qt.Key_A <= key <= Qt.Key_Z:
            return chr(key).lower()
        if Qt.Key_0 <= key <= Qt.Key_9:
            return chr(key)
        
        # 特殊键
        key_map = {
            Qt.Key_Space: "space",
            Qt.Key_Return: "enter",
            Qt.Key_Enter: "enter",
            Qt.Key_Escape: "esc",
            Qt.Key_Tab: "tab",
            Qt.Key_Backspace: "backspace",
            Qt.Key_Delete: "delete",
            Qt.Key_Insert: "insert",
            Qt.Key_Home: "home",
            Qt.Key_End: "end",
            Qt.Key_PageUp: "pageup",
            Qt.Key_PageDown: "pagedown",
            Qt.Key_Up: "up",
            Qt.Key_Down: "down",
            Qt.Key_Left: "left",
            Qt.Key_Right: "right",
            Qt.Key_F1: "f1",
            Qt.Key_F2: "f2",
            Qt.Key_F3: "f3",
            Qt.Key_F4: "f4",
            Qt.Key_F5: "f5",
            Qt.Key_F6: "f6",
            Qt.Key_F7: "f7",
            Qt.Key_F8: "f8",
            Qt.Key_F9: "f9",
            Qt.Key_F10: "f10",
            Qt.Key_F11: "f11",
            Qt.Key_F12: "f12",
            Qt.Key_Minus: "minus",
            Qt.Key_Equal: "equal",
            Qt.Key_BracketLeft: "[",
            Qt.Key_BracketRight: "]",
            Qt.Key_Semicolon: ";",
            Qt.Key_Apostrophe: "'",
            Qt.Key_Comma: ",",
            Qt.Key_Period: ".",
            Qt.Key_Slash: "/",
            Qt.Key_Backslash: "\\",
        }
        
        return key_map.get(key)
    
    def text(self):
        """获取当前快捷键文本"""
        return self.input.text()
    
    def setText(self, text):
        """设置快捷键文本"""
        self.input.setText(text)

