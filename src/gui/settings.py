"""设置界面"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTabWidget, QWidget,
    QTextEdit, QCheckBox, QMessageBox, QGroupBox,
    QComboBox, QScrollArea, QColorDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon
from loguru import logger
from src.gui.hotkey_input import HotkeyInput


# 默认提示词（用户友好版本，不包含JSON格式说明）
DEFAULT_FLOMO_PROMPT = """你是一个内容分类助手。请判断以下内容是否有价值，以及应该发送到哪里。

内容类型定义：
- 金句：深刻的见解、启发性的语句
- 产品知识：产品设计、用户体验相关
- AI知识：人工智能技术、趋势、应用
- 方法论：可复用的思维框架和方法

请根据内容类型，自动识别并分类内容。如果内容符合以上任一类型，则同步到Flomo，并自动添加相应的标签。"""

DEFAULT_NOTION_PROMPT = """你是一个任务识别助手。请判断以下内容是否包含任务、待办或灵感。

如果内容包含以下特征，则同步到Notion：
- 包含"需要"、"要做"、"计划"、"想法"、"灵感"等关键词
- 表达了一个待完成的任务或事项
- 是一个想法或灵感，需要后续处理

请根据内容自动识别，如果符合以上特征，则同步到Notion作为待办事项。"""

DEFAULT_TICKTICK_PROMPT = """你是一个待办任务识别助手。请判断以下内容是否包含明确的待办任务。

如果内容包含以下特征，则同步到滴答清单：
- 明确包含具体时间或日期（如"明天上午9点"、"下周一"、"12月20号"）
- 是一个具体的、可执行的待办任务
- 包含"提醒"、"记得"、"别忘了"等明确的待办提示词

注意：仅同步明确的、带时间的待办任务，普通想法或灵感不要同步到滴答清单。"""


class SettingsDialog(QDialog):
    """设置对话框"""
    
    # 信号：设置已保存
    settings_saved = pyqtSignal()
    
    def __init__(self, config_obj, parent=None):
        """
        初始化设置对话框
        
        Args:
            config_obj: 配置对象
            parent: 父窗口
        """
        super().__init__(parent)
        self.config_obj = config_obj
        self.main_app = None  # 主程序实例引用（稍后由主程序设置）
        self._init_ui()
        self._load_settings()
        logger.info("设置界面已初始化")
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("QuickNote AI - 设置")
        # 固定窗口尺寸，避免DPI缩放问题
        self.setFixedSize(1000, 700)
        
        # 设置全局样式
        self.setStyleSheet("""
            QDialog {
                background: #f5f5f5;
            }
            QLabel {
                font-size: 14px;
            }
            QLineEdit, QTextEdit, QComboBox {
                font-size: 14px;
            }
            QPushButton {
                font-size: 14px;
            }
        """)
        
        # 主布局
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("⚙️ 应用设置")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title.setStyleSheet("color: #007acc; padding: 10px;")
        layout.addWidget(title)
        
        # 标签页
        self.tabs = QTabWidget()
        # 设置标签页样式，增大高度和宽度
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                background: white;
            }
            QTabBar::tab {
                background: #f0f0f0;
                color: #333;
                padding: 12px 30px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 14px;
                min-height: 25px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: white;
                color: #007acc;
                border-bottom: 2px solid #007acc;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #e0e0e0;
            }
        """)
        self.tabs.addTab(self._create_api_tab(), "🔑 API配置")
        self.tabs.addTab(self._create_rules_tab(), "🤖 AI规则")
        self.tabs.addTab(self._create_hotkey_tab(), "⌨️ 快捷键")
        self.tabs.addTab(self._create_system_tab(), "⚙️ 系统设置")
        self.tabs.addTab(self._create_about_tab(), "ℹ️ 关于")
        
        layout.addWidget(self.tabs)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 统一按钮样式
        button_style = """
            QPushButton {
                padding: 12px 25px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-height: 20px;
                min-width: 100px;
            }
        """
        
        self.test_btn = QPushButton("🧪 测试连接")
        self.test_btn.setStyleSheet(button_style + """
            QPushButton {
                background: #f0f0f0;
                color: #666;
                border: 1px solid #d0d0d0;
            }
            QPushButton:hover {
                background: #e0e0e0;
                border: 1px solid #b0b0b0;
            }
        """)
        self.test_btn.clicked.connect(self._test_connection)
        button_layout.addWidget(self.test_btn)
        
        self.save_btn = QPushButton("💾 保存设置")
        self.save_btn.setStyleSheet(button_style + """
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        self.save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.setStyleSheet(button_style + """
            QPushButton {
                background: #f0f0f0;
                color: #666;
                border: 1px solid #d0d0d0;
            }
            QPushButton:hover {
                background: #e0e0e0;
                border: 1px solid #b0b0b0;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _create_api_tab(self) -> QWidget:
        """创建API配置标签页"""
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #f5f5f5;
            }
        """)
        
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # AI提供商选择
        provider_layout = QVBoxLayout()
        provider_label = QLabel("AI 提供商:")
        provider_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        provider_layout.addWidget(provider_label)
        
        self.ai_provider = QComboBox()
        self.ai_provider.addItems(["deepseek", "openai", "claude"])
        self.ai_provider.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
            }
            QComboBox:focus {
                border: 2px solid #007acc;
            }
        """)
        self.ai_provider.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.ai_provider)
        
        provider_hint = QLabel("💡 DeepSeek: 国产AI，价格便宜，推荐使用")
        provider_hint.setStyleSheet("color: #666; font-size: 14px; margin: 10px 0; padding: 10px; background: #e8f5e9; border-radius: 6px;")
        provider_layout.addWidget(provider_hint)
        
        layout.addLayout(provider_layout)
        
        # AI配置 - 使用自定义标题样式
        ai_group = QGroupBox()
        ai_group.setTitle("")  # 先设置为空，使用自定义标签
        ai_layout = QVBoxLayout()
        
        # 自定义标题，带颜色和竖条
        ai_title = QLabel("│ AI 配置")
        ai_title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 15px;
                font-weight: bold;
                padding: 8px 0px;
                margin-bottom: 10px;
            }
        """)
        ai_layout.addWidget(ai_title)
        
        self.openai_key = self._create_input_row("API Key:", "sk-...", ai_layout)
        self.openai_base_url = self._create_input_row("Base URL:", "自动", ai_layout)
        self.openai_model = self._create_input_row("Model:", "自动", ai_layout)
        
        ai_hint = QLabel("💡 Base URL和Model会根据提供商自动设置，也可以手动修改")
        ai_hint.setStyleSheet("color: #666; font-size: 14px; margin: 10px 0; padding: 10px; background: #e3f2fd; border-radius: 6px;")
        ai_layout.addWidget(ai_hint)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        # Notion配置 - 使用自定义标题样式
        notion_group = QGroupBox()
        notion_group.setTitle("")
        notion_layout = QVBoxLayout()
        
        # 自定义标题，带颜色和竖条
        notion_title = QLabel("│ Notion 配置")
        notion_title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 15px;
                font-weight: bold;
                padding: 8px 0px;
                margin-bottom: 10px;
                margin-top: 10px;
            }
        """)
        notion_layout.addWidget(notion_title)
        
        self.notion_key = self._create_input_row("API Key:", "secret_...", notion_layout)
        self.notion_db = self._create_input_row("Database ID:", "", notion_layout)
        
        notion_group.setLayout(notion_layout)
        layout.addWidget(notion_group)
        
        # Flomo配置 - 使用自定义标题样式
        flomo_group = QGroupBox()
        flomo_group.setTitle("")
        flomo_layout = QVBoxLayout()
        
        # 自定义标题，带颜色和竖条
        flomo_title = QLabel("│ Flomo 配置")
        flomo_title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 15px;
                font-weight: bold;
                padding: 8px 0px;
                margin-bottom: 10px;
                margin-top: 10px;
            }
        """)
        flomo_layout.addWidget(flomo_title)
        
        self.flomo_url = self._create_input_row("Webhook URL:", "https://flomoapp.com/iwh/...", flomo_layout)
        
        flomo_group.setLayout(flomo_layout)
        layout.addWidget(flomo_group)
        
        # 滴答清单配置 - 使用自定义标题样式
        ticktick_group = QGroupBox()
        ticktick_group.setTitle("")
        ticktick_layout = QVBoxLayout()
        
        # 自定义标题，带颜色和竖条
        ticktick_title = QLabel("│ 滴答清单配置（通过邮件）")
        ticktick_title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 15px;
                font-weight: bold;
                padding: 8px 0px;
                margin-bottom: 10px;
                margin-top: 10px;
            }
        """)
        ticktick_layout.addWidget(ticktick_title)
        
        # SMTP服务器配置
        self.ticktick_smtp_host = self._create_input_row("SMTP服务器:", "smtp.qq.com", ticktick_layout)
        self.ticktick_smtp_port = self._create_input_row("SMTP端口:", "465", ticktick_layout)
        
        # 发件邮箱配置
        self.ticktick_smtp_user = self._create_input_row("发件邮箱:", "your_email@qq.com", ticktick_layout)
        self.ticktick_smtp_pass = self._create_input_row("SMTP授权码:", "xxxxxxxxxxxx", ticktick_layout)
        self.ticktick_smtp_pass.setEchoMode(QLineEdit.Password)  # 密码输入框
        
        # 滴答清单专属邮箱
        self.ticktick_email = self._create_input_row("滴答清单邮箱:", "todo+xxxxx@mail.dida365.com", ticktick_layout)
        
        ticktick_hint = QLabel("💡 配置说明：\n"
                               "1. 在滴答清单设置中获取专属邮箱地址（设置 → 日历与邮件 → 通过邮件创建任务）\n"
                               "2. 使用QQ/163等邮箱，需开启SMTP服务并获取授权码（不是登录密码）\n"
                               "3. 邮件标题支持智能识别：时间、优先级（!!!高/!!中/!低）、清单（^清单名）")
        ticktick_hint.setStyleSheet("color: #666; font-size: 13px; margin: 10px 0; padding: 10px; background: #fff3e0; border-radius: 6px;")
        ticktick_hint.setWordWrap(True)
        ticktick_layout.addWidget(ticktick_hint)
        
        ticktick_group.setLayout(ticktick_layout)
        layout.addWidget(ticktick_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        
        # 将widget放入滚动区域
        scroll.setWidget(widget)
        
        # 创建容器
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll)
        container.setLayout(container_layout)
        
        return container
    
    def _create_rules_tab(self) -> QWidget:
        """创建AI规则标签页"""
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #f5f5f5;
            }
        """)
        
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("🤖 AI识别规则配置")
        title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 18px;
                font-weight: bold;
                padding: 10px 0;
            }
        """)
        layout.addWidget(title)
        
        # 总开关：剪切板监控
        total_switch_group = QGroupBox()
        total_switch_layout = QHBoxLayout()
        
        total_switch_title = QLabel("│ 剪切板监控总开关")
        total_switch_title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 15px;
                font-weight: bold;
                padding: 8px 0;
            }
        """)
        total_switch_layout.addWidget(total_switch_title)
        total_switch_layout.addStretch()
        
        self.clipboard_monitor_enabled = QCheckBox("启用剪切板监控")
        self.clipboard_monitor_enabled.setChecked(True)
        self.clipboard_monitor_enabled.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        total_switch_layout.addWidget(self.clipboard_monitor_enabled)
        
        total_switch_group.setLayout(total_switch_layout)
        layout.addWidget(total_switch_group)
        
        # Flomo规则配置
        flomo_group = QGroupBox()
        flomo_layout = QVBoxLayout()
        
        flomo_title_layout = QHBoxLayout()
        flomo_title = QLabel("│ Flomo 自动同步规则")
        flomo_title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 15px;
                font-weight: bold;
                padding: 8px 0;
            }
        """)
        flomo_title_layout.addWidget(flomo_title)
        flomo_title_layout.addStretch()
        
        # Flomo开关
        self.flomo_auto_sync = QCheckBox("启用自动同步")
        self.flomo_auto_sync.setChecked(True)
        self.flomo_auto_sync.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        flomo_title_layout.addWidget(self.flomo_auto_sync)
        
        flomo_layout.addLayout(flomo_title_layout)
        
        flomo_label = QLabel("AI识别提示词：")
        flomo_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        flomo_layout.addWidget(flomo_label)
        
        self.flomo_prompt = QTextEdit()
        self.flomo_prompt.setPlaceholderText("输入Flomo识别提示词...")
        self.flomo_prompt.setMinimumHeight(150)
        self.flomo_prompt.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 2px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
                line-height: 1.6;
            }
            QTextEdit:focus {
                border: 2px solid #007acc;
            }
        """)
        # 监听文本变化，启用保存按钮
        self.flomo_prompt.textChanged.connect(self._on_prompt_changed)
        flomo_layout.addWidget(self.flomo_prompt)
        
        flomo_btn_layout = QHBoxLayout()
        flomo_btn_layout.addStretch()
        
        # 保存按钮（初始隐藏，文本变化时显示）
        self.flomo_save_btn = QPushButton("💾 保存提示词")
        self.flomo_save_btn.setVisible(False)
        self.flomo_save_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #005a9e;
            }
        """)
        self.flomo_save_btn.clicked.connect(lambda: self._save_prompt('flomo'))
        flomo_btn_layout.addWidget(self.flomo_save_btn)
        
        flomo_reset_btn = QPushButton("🔄 重置为默认")
        flomo_reset_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background: #5cb85c;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4cae4c;
            }
        """)
        flomo_reset_btn.clicked.connect(self._reset_flomo_prompt)
        flomo_btn_layout.addWidget(flomo_reset_btn)
        
        flomo_layout.addLayout(flomo_btn_layout)
        flomo_group.setLayout(flomo_layout)
        layout.addWidget(flomo_group)
        
        # Notion规则配置
        notion_group = QGroupBox()
        notion_layout = QVBoxLayout()
        
        notion_title_layout = QHBoxLayout()
        notion_title = QLabel("│ Notion 自动同步规则")
        notion_title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 15px;
                font-weight: bold;
                padding: 8px 0;
            }
        """)
        notion_title_layout.addWidget(notion_title)
        notion_title_layout.addStretch()
        
        # Notion开关
        self.notion_auto_sync = QCheckBox("启用自动同步")
        self.notion_auto_sync.setChecked(True)
        self.notion_auto_sync.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        notion_title_layout.addWidget(self.notion_auto_sync)
        
        notion_layout.addLayout(notion_title_layout)
        
        notion_label = QLabel("AI识别提示词：")
        notion_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        notion_layout.addWidget(notion_label)
        
        self.notion_prompt = QTextEdit()
        self.notion_prompt.setPlaceholderText("输入Notion识别提示词...")
        self.notion_prompt.setMinimumHeight(150)
        self.notion_prompt.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 2px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
                line-height: 1.6;
            }
            QTextEdit:focus {
                border: 2px solid #007acc;
            }
        """)
        # 监听文本变化，启用保存按钮
        self.notion_prompt.textChanged.connect(self._on_prompt_changed)
        notion_layout.addWidget(self.notion_prompt)
        
        notion_btn_layout = QHBoxLayout()
        notion_btn_layout.addStretch()
        
        # 保存按钮（初始隐藏，文本变化时显示）
        self.notion_save_btn = QPushButton("💾 保存提示词")
        self.notion_save_btn.setVisible(False)
        self.notion_save_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #005a9e;
            }
        """)
        self.notion_save_btn.clicked.connect(lambda: self._save_prompt('notion'))
        notion_btn_layout.addWidget(self.notion_save_btn)
        
        notion_reset_btn = QPushButton("🔄 重置为默认")
        notion_reset_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background: #5cb85c;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4cae4c;
            }
        """)
        notion_reset_btn.clicked.connect(self._reset_notion_prompt)
        notion_btn_layout.addWidget(notion_reset_btn)
        
        notion_layout.addLayout(notion_btn_layout)
        notion_group.setLayout(notion_layout)
        layout.addWidget(notion_group)
        
        # 滴答清单规则配置
        ticktick_group = QGroupBox()
        ticktick_layout = QVBoxLayout()
        
        ticktick_title_layout = QHBoxLayout()
        ticktick_title = QLabel("│ 滴答清单 自动同步规则")
        ticktick_title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 15px;
                font-weight: bold;
                padding: 8px 0;
            }
        """)
        ticktick_title_layout.addWidget(ticktick_title)
        ticktick_title_layout.addStretch()
        
        # 滴答清单开关
        self.ticktick_auto_sync = QCheckBox("启用自动同步")
        self.ticktick_auto_sync.setChecked(True)
        self.ticktick_auto_sync.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)
        ticktick_title_layout.addWidget(self.ticktick_auto_sync)
        
        ticktick_layout.addLayout(ticktick_title_layout)
        
        ticktick_label = QLabel("AI识别提示词：")
        ticktick_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        ticktick_layout.addWidget(ticktick_label)
        
        self.ticktick_prompt = QTextEdit()
        self.ticktick_prompt.setPlaceholderText("输入滴答清单识别提示词...")
        self.ticktick_prompt.setMinimumHeight(150)
        self.ticktick_prompt.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 2px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
                line-height: 1.6;
            }
            QTextEdit:focus {
                border: 2px solid #007acc;
            }
        """)
        # 监听文本变化，启用保存按钮
        self.ticktick_prompt.textChanged.connect(self._on_prompt_changed)
        ticktick_layout.addWidget(self.ticktick_prompt)
        
        ticktick_btn_layout = QHBoxLayout()
        ticktick_btn_layout.addStretch()
        
        # 保存按钮（初始隐藏，文本变化时显示）
        self.ticktick_save_btn = QPushButton("💾 保存提示词")
        self.ticktick_save_btn.setVisible(False)
        self.ticktick_save_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #005a9e;
            }
        """)
        self.ticktick_save_btn.clicked.connect(lambda: self._save_prompt('ticktick'))
        ticktick_btn_layout.addWidget(self.ticktick_save_btn)
        
        ticktick_reset_btn = QPushButton("🔄 重置为默认")
        ticktick_reset_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background: #5cb85c;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4cae4c;
            }
        """)
        ticktick_reset_btn.clicked.connect(self._reset_ticktick_prompt)
        ticktick_btn_layout.addWidget(ticktick_reset_btn)
        
        ticktick_layout.addLayout(ticktick_btn_layout)
        ticktick_group.setLayout(ticktick_layout)
        layout.addWidget(ticktick_group)
        
        # 提示信息
        hint = QLabel("""
💡 使用说明：
  • 启用自动同步后，AI会根据提示词自动识别剪切板内容
  • 提示词用于指导AI判断内容是否应该同步到对应平台
  • 可以自定义提示词以适应你的使用习惯
  • 点击"重置为默认"可恢复默认提示词
  • 修改后需要保存设置才能生效
        """)
        hint.setStyleSheet("""
            QLabel {
                color: #555;
                font-size: 14px;
                margin: 20px 0;
                padding: 20px;
                background: #fff9e6;
                border-left: 4px solid #ffc107;
                border-radius: 6px;
                line-height: 1.8;
            }
        """)
        layout.addWidget(hint)
        
        layout.addStretch()
        widget.setLayout(layout)
        
        # 放入滚动区域
        scroll.setWidget(widget)
        
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll)
        container.setLayout(container_layout)
        
        return container
    
    def _create_hotkey_tab(self) -> QWidget:
        """创建快捷键标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("⌨️ 全局快捷键配置")
        title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 18px;
                font-weight: bold;
                padding: 10px 0;
            }
        """)
        layout.addWidget(title)
        
        # 快速输入快捷键
        quick_label = QLabel("快速输入窗口：")
        quick_label.setStyleSheet("font-weight: bold; font-size: 15px; margin-top: 10px;")
        layout.addWidget(quick_label)
        
        self.hotkey_quick = HotkeyInput(default_hotkey="ctrl+shift+space")
        layout.addWidget(self.hotkey_quick)
        
        # 剪切板切换快捷键
        clipboard_label = QLabel("切换剪切板监控：")
        clipboard_label.setStyleSheet("font-weight: bold; font-size: 15px; margin-top: 20px;")
        layout.addWidget(clipboard_label)
        
        self.hotkey_clipboard = HotkeyInput(default_hotkey="ctrl+shift+c")
        layout.addWidget(self.hotkey_clipboard)
        
        # 提示信息
        hint = QLabel("""
💡 使用方法：
  1. 点击"录制"按钮
  2. 按下你想设置的快捷键组合
  3. 快捷键会自动显示在输入框中
  4. 点击"重置"可恢复默认快捷键

⚠️ 注意：
  • 修改后需要重启应用才能生效
  • 建议使用 Ctrl/Shift/Alt 组合键，避免与系统冲突
  • 支持的修饰键：ctrl、shift、alt、cmd
        """)
        hint.setStyleSheet("""
            QLabel {
                color: #555;
                font-size: 14px;
                margin: 20px 0;
                padding: 20px;
                background: #fff9e6;
                border-left: 4px solid #ffc107;
                border-radius: 6px;
                line-height: 1.8;
            }
        """)
        layout.addWidget(hint)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_system_tab(self) -> QWidget:
        """创建系统设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 遮罩设置组
        mask_group = QGroupBox()
        mask_group.setTitle("")
        mask_layout = QVBoxLayout()
        
        # 自定义标题
        mask_title = QLabel("│ 遮罩设置")
        mask_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #007acc;
                padding: 10px 0;
                border-bottom: 2px solid #007acc;
                margin-bottom: 10px;
            }
        """)
        mask_layout.addWidget(mask_title)
        
        # 遮罩颜色设置
        color_layout = QHBoxLayout()
        color_label = QLabel("遮罩颜色 (RGB):")
        color_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        color_layout.addWidget(color_label)
        
        # RGB输入框
        self.mask_color_r = QLineEdit()
        self.mask_color_r.setPlaceholderText("R (0-255)")
        self.mask_color_r.setMaximumWidth(80)
        color_layout.addWidget(self.mask_color_r)
        
        self.mask_color_g = QLineEdit()
        self.mask_color_g.setPlaceholderText("G (0-255)")
        self.mask_color_g.setMaximumWidth(80)
        color_layout.addWidget(self.mask_color_g)
        
        self.mask_color_b = QLineEdit()
        self.mask_color_b.setPlaceholderText("B (0-255)")
        self.mask_color_b.setMaximumWidth(80)
        color_layout.addWidget(self.mask_color_b)
        
        color_layout.addStretch()
        mask_layout.addLayout(color_layout)
        
        # 遮罩透明度设置
        alpha_layout = QHBoxLayout()
        alpha_label = QLabel("遮罩透明度 (%):")
        alpha_label.setStyleSheet("font-weight: bold; min-width: 120px;")
        alpha_layout.addWidget(alpha_label)
        
        self.mask_alpha = QLineEdit()
        self.mask_alpha.setPlaceholderText("0-100 (例如: 60 表示60%透明度)")
        self.mask_alpha.setMaximumWidth(200)
        alpha_layout.addWidget(self.mask_alpha)
        
        alpha_hint = QLabel("💡 透明度范围: 0-100，数值越大越不透明")
        alpha_hint.setStyleSheet("color: #666; font-size: 12px; margin-left: 10px;")
        alpha_layout.addWidget(alpha_hint)
        alpha_layout.addStretch()
        mask_layout.addLayout(alpha_layout)
        
        mask_group.setLayout(mask_layout)
        layout.addWidget(mask_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_about_tab(self) -> QWidget:
        """创建关于标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        about_html = """
        <div style="text-align: center;">
            <h1 style="color: #007acc;">QuickNote AI</h1>
            <p style="font-size: 14px; color: #666;">智能笔记助手</p>
            <p style="font-size: 12px;"><b>版本:</b> 1.0.0</p>
            
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #ccc;">
            
            <h3 style="color: #333;">✨ 核心功能</h3>
            <ul style="text-align: left; display: inline-block;">
                <li>快捷键快速输入灵感</li>
                <li>智能剪切板监控</li>
                <li>AI自动识别和分类</li>
                <li>自动同步到Notion和Flomo</li>
            </ul>
            
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #ccc;">
            
            <p style="color: #999; font-size: 11px; margin-top: 30px;">
                让灵感不再溜走 💡<br>
                © 2025 QuickNote AI
            </p>
        </div>
        """
        
        about_label = QLabel(about_html)
        about_label.setTextFormat(Qt.RichText)
        about_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(about_label)
        
        widget.setLayout(layout)
        return widget
    
    def _create_input_row(self, label_text: str, placeholder: str, layout: QVBoxLayout) -> QLineEdit:
        """创建输入行"""
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; margin-top: 5px; font-size: 14px;")
        layout.addWidget(label)
        
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
                color: #000000;
                font-size: 14px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #007acc;
            }
            QLineEdit::placeholder {
                color: #999999;
            }
        """)
        layout.addWidget(input_field)
        
        return input_field
    
    def _load_settings(self):
        """加载当前设置"""
        # 加载AI提供商
        provider = self.config_obj.ai_provider
        if provider in ["deepseek", "openai", "claude"]:
            index = self.ai_provider.findText(provider)
            if index >= 0:
                self.ai_provider.setCurrentIndex(index)
        
        # 加载API配置
        self.openai_key.setText(self.config_obj.openai_api_key)
        
        # 根据provider显示对应的URL和Model
        self._update_provider_defaults(provider)
        
        # 如果已有自定义配置，则使用自定义配置
        base_url = self.config_obj.get_env("OPENAI_BASE_URL", "")
        model = self.config_obj.get_env("OPENAI_MODEL", "")
        
        if base_url and provider == "deepseek" and "deepseek" in base_url:
            self.openai_base_url.setText(base_url)
        elif base_url and provider == "openai" and "openai" in base_url:
            self.openai_base_url.setText(base_url)
        elif base_url:
            self.openai_base_url.setText(base_url)
        
        if model:
            self.openai_model.setText(model)
        
        self.notion_key.setText(self.config_obj.notion_api_key)
        self.notion_db.setText(self.config_obj.notion_database_id)
        
        self.flomo_url.setText(self.config_obj.flomo_api_url)
        
        # TickTick 邮箱配置
        self.ticktick_smtp_host.setText(self.config_obj.ticktick_smtp_host)
        self.ticktick_smtp_port.setText(str(self.config_obj.ticktick_smtp_port))
        self.ticktick_smtp_user.setText(self.config_obj.ticktick_smtp_user)
        self.ticktick_smtp_pass.setText(self.config_obj.ticktick_smtp_pass)
        self.ticktick_email.setText(self.config_obj.ticktick_email)
        
        # 加载快捷键配置（使用HotkeyInput控件）
        self.hotkey_quick.setText(self.config_obj.hotkey_quick_input)
        self.hotkey_clipboard.setText(self.config_obj.hotkey_toggle_clipboard)
        
        # 加载遮罩设置
        try:
            mask_color = self.config_obj.get('ui.mask_color', [0, 0, 0])  # 默认黑色
            mask_alpha = self.config_obj.get('ui.mask_alpha', 153)  # 默认alpha值
            # 将alpha值转换为百分比（0-100）
            if mask_alpha > 100:
                mask_alpha_percent = int((mask_alpha / 255) * 100)
            else:
                mask_alpha_percent = mask_alpha
            
            # 加载颜色到输入框
            if hasattr(self, 'mask_color_r') and hasattr(self, 'mask_color_g') and hasattr(self, 'mask_color_b'):
                if isinstance(mask_color, list) and len(mask_color) >= 3:
                    self.mask_color_r.setText(str(mask_color[0]))
                    self.mask_color_g.setText(str(mask_color[1]))
                    self.mask_color_b.setText(str(mask_color[2]))
                else:
                    self.mask_color_r.setText("0")
                    self.mask_color_g.setText("0")
                    self.mask_color_b.setText("0")
            
            # 加载透明度
            if hasattr(self, 'mask_alpha'):
                self.mask_alpha.setText(str(mask_alpha_percent))
        except Exception as e:
            logger.warning(f"加载遮罩设置失败: {e}，使用默认值")
            if hasattr(self, 'mask_color_r') and hasattr(self, 'mask_color_g') and hasattr(self, 'mask_color_b'):
                self.mask_color_r.setText("0")
                self.mask_color_g.setText("0")
                self.mask_color_b.setText("0")
            if hasattr(self, 'mask_alpha'):
                self.mask_alpha.setText("60")
        
        # 加载AI规则
        try:
            import yaml
            rules = self.config_obj.config.get('ai_rules', {})
            
            # 加载Flomo提示词
            if hasattr(self, 'flomo_prompt'):
                try:
                    flomo_prompt = rules.get('flomo', {}).get('prompt', self._get_default_flomo_prompt())
                    self.flomo_prompt.setText(flomo_prompt)
                except Exception as e:
                    logger.warning(f"加载Flomo提示词失败: {e}")
            
            # 加载Notion提示词
            if hasattr(self, 'notion_prompt'):
                try:
                    notion_prompt = rules.get('notion', {}).get('prompt', self._get_default_notion_prompt())
                    self.notion_prompt.setText(notion_prompt)
                except Exception as e:
                    logger.warning(f"加载Notion提示词失败: {e}")
            
            # 加载滴答清单提示词
            if hasattr(self, 'ticktick_prompt'):
                try:
                    ticktick_prompt = rules.get('ticktick', {}).get('prompt', self._get_default_ticktick_prompt())
                    self.ticktick_prompt.setText(ticktick_prompt)
                except Exception as e:
                    logger.warning(f"加载滴答清单提示词失败: {e}")
        except Exception as e:
            logger.error(f"加载AI规则失败: {e}")
            rules = {}
        
        # 加载自动同步开关状态（从config读取，默认开启）
        # 检查控件是否存在（可能在AI规则标签页中）
        if hasattr(self, 'clipboard_monitor_enabled'):
            try:
                self.clipboard_monitor_enabled.setChecked(rules.get('clipboard_monitor', True))
            except Exception as e:
                logger.warning(f"加载剪切板监控开关失败: {e}")
        
        if hasattr(self, 'flomo_auto_sync'):
            try:
                self.flomo_auto_sync.setChecked(rules.get('flomo', {}).get('enabled', True))
            except Exception as e:
                logger.warning(f"加载Flomo开关失败: {e}")
        
        if hasattr(self, 'notion_auto_sync'):
            try:
                self.notion_auto_sync.setChecked(rules.get('notion', {}).get('enabled', True))
            except Exception as e:
                logger.warning(f"加载Notion开关失败: {e}")
        
        if hasattr(self, 'ticktick_auto_sync'):
            try:
                self.ticktick_auto_sync.setChecked(rules.get('ticktick', {}).get('enabled', True))
            except Exception as e:
                logger.warning(f"加载滴答清单开关失败: {e}")
        
        # 记录初始提示词，用于检测变化
        if hasattr(self, 'flomo_prompt'):
            self._flomo_prompt_original = self.flomo_prompt.toPlainText()
        if hasattr(self, 'notion_prompt'):
            self._notion_prompt_original = self.notion_prompt.toPlainText()
        if hasattr(self, 'ticktick_prompt'):
            self._ticktick_prompt_original = self.ticktick_prompt.toPlainText()
    
    def _on_provider_changed(self, provider: str):
        """当AI提供商改变时，自动更新默认配置"""
        self._update_provider_defaults(provider)
    
    def _update_provider_defaults(self, provider: str):
        """根据provider更新默认的Base URL和Model"""
        if provider == "deepseek":
            self.openai_base_url.setPlaceholderText("https://api.deepseek.com/v1")
            self.openai_model.setPlaceholderText("deepseek-chat")
            # 如果当前值是空的或者是OpenAI的默认值，则自动填充
            if not self.openai_base_url.text() or "openai.com" in self.openai_base_url.text():
                self.openai_base_url.setText("https://api.deepseek.com/v1")
            if not self.openai_model.text() or "gpt" in self.openai_model.text():
                self.openai_model.setText("deepseek-chat")
        elif provider == "openai":
            self.openai_base_url.setPlaceholderText("https://api.openai.com/v1")
            self.openai_model.setPlaceholderText("gpt-4o-mini")
            if not self.openai_base_url.text() or "deepseek.com" in self.openai_base_url.text():
                self.openai_base_url.setText("https://api.openai.com/v1")
            if not self.openai_model.text() or "deepseek" in self.openai_model.text():
                self.openai_model.setText("gpt-4o-mini")
        elif provider == "claude":
            self.openai_base_url.setPlaceholderText("Claude不需要Base URL")
            self.openai_model.setPlaceholderText("claude-3-haiku-20240307")
    
    def _save_settings(self):
        """保存设置"""
        try:
            import os
            import yaml
            
            # 保存到.env文件
            env_file = self.config_obj.env_file
            
            # 获取当前选择的AI提供商
            provider = self.ai_provider.currentText()
            
            # 构建新的环境变量内容
            env_content = f"""# AI API配置
AI_PROVIDER={provider}
OPENAI_API_KEY={self.openai_key.text()}
OPENAI_BASE_URL={self.openai_base_url.text()}
OPENAI_MODEL={self.openai_model.text()}

# Notion配置
NOTION_API_KEY={self.notion_key.text()}
NOTION_DATABASE_ID={self.notion_db.text()}

# Flomo配置
FLOMO_API_URL={self.flomo_url.text()}

# 滴答清单配置（通过邮件）
TICKTICK_SMTP_HOST={self.ticktick_smtp_host.text()}
TICKTICK_SMTP_PORT={self.ticktick_smtp_port.text()}
TICKTICK_SMTP_USER={self.ticktick_smtp_user.text()}
TICKTICK_SMTP_PASS={self.ticktick_smtp_pass.text()}
TICKTICK_EMAIL={self.ticktick_email.text()}
"""
            
            # 写入.env文件
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            # 保存快捷键配置到config.yaml
            config_file = self.config_obj.config_file
            
            # 读取现有配置
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
            else:
                config_data = {}
            
            # 更新遮罩设置
            if 'ui' not in config_data:
                config_data['ui'] = {}
            
            # 读取遮罩颜色RGB值
            try:
                if hasattr(self, 'mask_color_r') and hasattr(self, 'mask_color_g') and hasattr(self, 'mask_color_b'):
                    mask_r_text = self.mask_color_r.text().strip() if self.mask_color_r.text() else "0"
                    mask_g_text = self.mask_color_g.text().strip() if self.mask_color_g.text() else "0"
                    mask_b_text = self.mask_color_b.text().strip() if self.mask_color_b.text() else "0"
                    
                    mask_r = int(mask_r_text) if mask_r_text else 0
                    mask_g = int(mask_g_text) if mask_g_text else 0
                    mask_b = int(mask_b_text) if mask_b_text else 0
                    
                    # 限制范围
                    mask_r = max(0, min(255, mask_r))
                    mask_g = max(0, min(255, mask_g))
                    mask_b = max(0, min(255, mask_b))
                    config_data['ui']['mask_color'] = [mask_r, mask_g, mask_b]
                elif hasattr(self, '_mask_color'):
                    # 如果使用颜色选择器
                    config_data['ui']['mask_color'] = self._mask_color
                else:
                    config_data['ui']['mask_color'] = [0, 0, 0]
            except (ValueError, AttributeError) as e:
                logger.warning(f"读取遮罩颜色失败: {e}，使用默认值")
                config_data['ui']['mask_color'] = [0, 0, 0]
            
            # 读取遮罩透明度百分比
            try:
                if hasattr(self, 'mask_alpha'):
                    mask_alpha_text = self.mask_alpha.text().strip() if self.mask_alpha.text() else "60"
                    mask_alpha_percent = int(mask_alpha_text) if mask_alpha_text else 60
                    # 限制范围
                    mask_alpha_percent = max(0, min(100, mask_alpha_percent))
                    # 转换为alpha值（0-255）
                    mask_alpha = int((mask_alpha_percent / 100) * 255)
                    config_data['ui']['mask_alpha'] = mask_alpha
                else:
                    config_data['ui']['mask_alpha'] = 153
            except (ValueError, AttributeError) as e:
                logger.warning(f"读取遮罩透明度失败: {e}，使用默认值")
                config_data['ui']['mask_alpha'] = 153
            
            # 更新快捷键配置
            if 'hotkeys' not in config_data:
                config_data['hotkeys'] = {}
            
            config_data['hotkeys']['quick_input'] = self.hotkey_quick.text().strip()
            config_data['hotkeys']['toggle_clipboard'] = self.hotkey_clipboard.text().strip()
            
            # 更新AI规则配置
            if 'ai_rules' not in config_data:
                config_data['ai_rules'] = {}
            
            # 保存剪切板监控总开关
            if hasattr(self, 'clipboard_monitor_enabled'):
                try:
                    config_data['ai_rules']['clipboard_monitor'] = self.clipboard_monitor_enabled.isChecked()
                except Exception as e:
                    logger.warning(f"保存剪切板监控开关失败: {e}")
                    config_data['ai_rules']['clipboard_monitor'] = True  # 默认值
            
            # 保存Flomo规则
            if hasattr(self, 'flomo_auto_sync') and hasattr(self, 'flomo_prompt'):
                try:
                    if 'flomo' not in config_data['ai_rules']:
                        config_data['ai_rules']['flomo'] = {}
                    
                    config_data['ai_rules']['flomo']['enabled'] = self.flomo_auto_sync.isChecked()
                    config_data['ai_rules']['flomo']['prompt'] = self.flomo_prompt.toPlainText().strip()
                except Exception as e:
                    logger.warning(f"保存Flomo规则失败: {e}")
            
            # 保存Notion规则
            if hasattr(self, 'notion_auto_sync') and hasattr(self, 'notion_prompt'):
                try:
                    if 'notion' not in config_data['ai_rules']:
                        config_data['ai_rules']['notion'] = {}
                    
                    config_data['ai_rules']['notion']['enabled'] = self.notion_auto_sync.isChecked()
                    config_data['ai_rules']['notion']['prompt'] = self.notion_prompt.toPlainText().strip()
                except Exception as e:
                    logger.warning(f"保存Notion规则失败: {e}")
            
            # 保存滴答清单规则
            if hasattr(self, 'ticktick_auto_sync') and hasattr(self, 'ticktick_prompt'):
                try:
                    if 'ticktick' not in config_data['ai_rules']:
                        config_data['ai_rules']['ticktick'] = {}
                    
                    config_data['ai_rules']['ticktick']['enabled'] = self.ticktick_auto_sync.isChecked()
                    config_data['ai_rules']['ticktick']['prompt'] = self.ticktick_prompt.toPlainText().strip()
                except Exception as e:
                    logger.warning(f"保存滴答清单规则失败: {e}")
            
            # 写入config.yaml
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
            logger.info("设置已保存（包括快捷键配置）")
            
            QMessageBox.information(
                self,
                "保存成功",
                "设置已保存！\n\n⚠️ 快捷键修改需要重启应用才能生效。\n其他设置已立即生效。"
            )
            
            self.settings_saved.emit()
            self.accept()
            
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            import traceback
            QMessageBox.critical(
                self,
                "保存失败",
                f"保存设置时出错：\n{str(e)}\n\n详细信息：\n{traceback.format_exc()[:200]}"
            )
    
    def _get_default_flomo_prompt(self):
        """获取默认Flomo提示词"""
        return DEFAULT_FLOMO_PROMPT
    
    def _get_default_notion_prompt(self):
        """获取默认Notion提示词"""
        return DEFAULT_NOTION_PROMPT
    
    def _get_default_ticktick_prompt(self):
        """获取默认滴答清单提示词"""
        return DEFAULT_TICKTICK_PROMPT
    
    def _reset_flomo_prompt(self):
        """重置Flomo提示词为默认值"""
        self.flomo_prompt.setText(self._get_default_flomo_prompt())
        self._flomo_prompt_original = self.flomo_prompt.toPlainText()
        if hasattr(self, 'flomo_save_btn'):
            self.flomo_save_btn.setVisible(False)
        logger.info("Flomo提示词已重置为默认值")
    
    def _reset_notion_prompt(self):
        """重置Notion提示词为默认值"""
        self.notion_prompt.setText(self._get_default_notion_prompt())
        self._notion_prompt_original = self.notion_prompt.toPlainText()
        if hasattr(self, 'notion_save_btn'):
            self.notion_save_btn.setVisible(False)
        logger.info("Notion提示词已重置为默认值")
    
    def _reset_ticktick_prompt(self):
        """重置滴答清单提示词为默认值"""
        self.ticktick_prompt.setText(self._get_default_ticktick_prompt())
        self._ticktick_prompt_original = self.ticktick_prompt.toPlainText()
        if hasattr(self, 'ticktick_save_btn'):
            self.ticktick_save_btn.setVisible(False)
        logger.info("滴答清单提示词已重置为默认值")
    
    def _on_prompt_changed(self):
        """提示词文本变化时，显示保存按钮"""
        # 检查Flomo提示词是否变化
        if hasattr(self, 'flomo_prompt') and hasattr(self, '_flomo_prompt_original'):
            current = self.flomo_prompt.toPlainText()
            if current != self._flomo_prompt_original:
                if hasattr(self, 'flomo_save_btn'):
                    self.flomo_save_btn.setVisible(True)
            else:
                if hasattr(self, 'flomo_save_btn'):
                    self.flomo_save_btn.setVisible(False)
        
        # 检查Notion提示词是否变化
        if hasattr(self, 'notion_prompt') and hasattr(self, '_notion_prompt_original'):
            current = self.notion_prompt.toPlainText()
            if current != self._notion_prompt_original:
                if hasattr(self, 'notion_save_btn'):
                    self.notion_save_btn.setVisible(True)
            else:
                if hasattr(self, 'notion_save_btn'):
                    self.notion_save_btn.setVisible(False)
        
        # 检查滴答清单提示词是否变化
        if hasattr(self, 'ticktick_prompt') and hasattr(self, '_ticktick_prompt_original'):
            current = self.ticktick_prompt.toPlainText()
            if current != self._ticktick_prompt_original:
                if hasattr(self, 'ticktick_save_btn'):
                    self.ticktick_save_btn.setVisible(True)
            else:
                if hasattr(self, 'ticktick_save_btn'):
                    self.ticktick_save_btn.setVisible(False)
    
    def _save_prompt(self, prompt_type: str):
        """保存提示词"""
        try:
            import yaml
            config_file = self.config_obj.config_file
            
            # 读取现有配置
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
            else:
                config_data = {}
            
            # 更新AI规则配置
            if 'ai_rules' not in config_data:
                config_data['ai_rules'] = {}
            
            if prompt_type == 'flomo':
                if 'flomo' not in config_data['ai_rules']:
                    config_data['ai_rules']['flomo'] = {}
                config_data['ai_rules']['flomo']['prompt'] = self.flomo_prompt.toPlainText().strip()
                self._flomo_prompt_original = self.flomo_prompt.toPlainText()
                self.flomo_save_btn.setVisible(False)
                logger.info("Flomo提示词已保存")
            elif prompt_type == 'notion':
                if 'notion' not in config_data['ai_rules']:
                    config_data['ai_rules']['notion'] = {}
                config_data['ai_rules']['notion']['prompt'] = self.notion_prompt.toPlainText().strip()
                self._notion_prompt_original = self.notion_prompt.toPlainText()
                self.notion_save_btn.setVisible(False)
                logger.info("Notion提示词已保存")
            elif prompt_type == 'ticktick':
                if 'ticktick' not in config_data['ai_rules']:
                    config_data['ai_rules']['ticktick'] = {}
                config_data['ai_rules']['ticktick']['prompt'] = self.ticktick_prompt.toPlainText().strip()
                self._ticktick_prompt_original = self.ticktick_prompt.toPlainText()
                self.ticktick_save_btn.setVisible(False)
                logger.info("滴答清单提示词已保存")
            
            # 写入config.yaml
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
            from PyQt5.QtWidgets import QMessageBox
            prompt_name = {
                'flomo': 'Flomo',
                'notion': 'Notion',
                'ticktick': '滴答清单'
            }.get(prompt_type, prompt_type)
            
            QMessageBox.information(
                self,
                "保存成功",
                f"{prompt_name}提示词已保存！"
            )
            
        except Exception as e:
            logger.error(f"保存提示词失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "保存失败",
                f"保存提示词时出错：\n{str(e)}"
            )
    
    def _refresh_clipboard_history(self):
        """刷新剪切板历史"""
        try:
            # 检查控件是否存在
            if not hasattr(self, 'clipboard_history_list'):
                return
            
            # 检查main_app是否已设置
            if not hasattr(self, 'main_app') or self.main_app is None:
                self.clipboard_history_list.setText("等待主程序连接...")
                return
            
            # 尝试从主程序获取剪切板历史
            history = []
            try:
                if hasattr(self.main_app, 'clipboard_monitor') and self.main_app.clipboard_monitor:
                    history = self.main_app.clipboard_monitor.get_history(limit=20)
            except AttributeError:
                logger.debug("主程序的clipboard_monitor不存在")
            except Exception as e:
                logger.warning(f"获取剪切板历史失败: {e}")
            
            # 显示历史
            if history:
                history_text = ""
                for i, item in enumerate(history[-10:], 1):  # 显示最近10条
                    preview = item[:80] + "..." if len(item) > 80 else item
                    history_text += f"[{i}] {preview}\n"
                    history_text += "─" * 50 + "\n\n"
                
                self.clipboard_history_list.setText(history_text.strip())
            else:
                self.clipboard_history_list.setText("暂无剪切板历史记录\n\n提示：当剪切板监控启用时，检测到的内容会自动记录在这里")
        except AttributeError as e:
            # 属性不存在，正常情况（main_app未设置）
            logger.debug(f"刷新剪切板历史时main_app未设置: {e}")
            if hasattr(self, 'clipboard_history_list'):
                try:
                    self.clipboard_history_list.setText("等待主程序连接...")
                except:
                    pass
        except Exception as e:
            logger.error(f"刷新剪切板历史失败: {e}")
            if hasattr(self, 'clipboard_history_list'):
                try:
                    self.clipboard_history_list.setText("无法加载剪切板历史")
                except:
                    pass
    
    def _test_connection(self):
        """测试连接"""
        from PyQt5.QtWidgets import QMessageBox
        
        # 直接执行测试，不使用进度对话框（避免弹窗问题）
        result_text = ""
        
        try:
            # 测试AI连接
            provider = self.ai_provider.currentText()
            ai_ok = False
            
            if provider in ["openai", "deepseek"]:
                try:
                    from openai import OpenAI
                    base_url = self.openai_base_url.text() if self.openai_base_url.text() else None
                    if not base_url:
                        if provider == "deepseek":
                            base_url = "https://api.deepseek.com/v1"
                        else:
                            base_url = "https://api.openai.com/v1"
                    
                    client = OpenAI(
                        api_key=self.openai_key.text(),
                        base_url=base_url
                    )
                    # 简单测试：调用models接口
                    list(client.models.list())
                    ai_ok = True
                    provider_name = "DeepSeek" if provider == "deepseek" else "OpenAI"
                    result_text += f"✅ {provider_name} 连接成功\n"
                except Exception as e:
                    provider_name = "DeepSeek" if provider == "deepseek" else "OpenAI"
                    error_msg = str(e)[:100] if len(str(e)) > 100 else str(e)
                    result_text += f"❌ {provider_name} 连接失败: {error_msg}\n"
            
            elif provider == "claude":
                # Claude测试需要ANTHROPIC_API_KEY，这里暂时跳过
                result_text += "⚠️ Claude连接测试暂未实现\n"
                ai_ok = True  # 暂时标记为成功
            
            # 测试Notion连接
            notion_ok = False
            if self.notion_key.text() and self.notion_db.text():
                try:
                    from src.integrations.notion_api import NotionAPI
                    notion = NotionAPI(
                        self.notion_key.text(),
                        self.notion_db.text()
                    )
                    notion_ok = notion.test_connection()
                    if notion_ok:
                        result_text += "✅ Notion 连接成功\n"
                except Exception as e:
                    error_msg = str(e)[:100] if len(str(e)) > 100 else str(e)
                    result_text += f"❌ Notion 连接失败: {error_msg}\n"
            else:
                result_text += "⚠️ Notion 配置不完整\n"
            
            # 测试Flomo连接
            if self.flomo_url.text():
                try:
                    from src.integrations.flomo_api import FlomoAPI
                    flomo = FlomoAPI(self.flomo_url.text())
                    flomo_ok = flomo.test_connection()
                    if flomo_ok:
                        result_text += "✅ Flomo 连接成功\n"
                    else:
                        result_text += "❌ Flomo 连接失败\n"
                except Exception as e:
                    error_msg = str(e)[:100] if len(str(e)) > 100 else str(e)
                    result_text += f"❌ Flomo 连接失败: {error_msg}\n"
            else:
                result_text += "⚠️ Flomo 未配置（可选）\n"
            
            # 测试滴答清单连接
            if (self.ticktick_smtp_user.text() and 
                self.ticktick_smtp_pass.text() and 
                self.ticktick_email.text()):
                try:
                    from src.integrations.ticktick_api import TickTickAPI
                    smtp_port = int(self.ticktick_smtp_port.text() or "465")
                    ticktick = TickTickAPI(
                        smtp_host=self.ticktick_smtp_host.text() or "smtp.qq.com",
                        smtp_port=smtp_port,
                        smtp_user=self.ticktick_smtp_user.text(),
                        smtp_pass=self.ticktick_smtp_pass.text(),
                        ticktick_email=self.ticktick_email.text()
                    )
                    ticktick_ok = ticktick.test_connection()
                    if ticktick_ok:
                        result_text += "✅ 滴答清单 连接成功\n"
                    else:
                        result_text += "❌ 滴答清单 连接失败\n"
                except Exception as e:
                    error_msg = str(e)[:100] if len(str(e)) > 100 else str(e)
                    result_text += f"❌ 滴答清单 连接失败: {error_msg}\n"
            else:
                result_text += "⚠️ 滴答清单 未配置（可选）\n"
            
            # 显示结果
            if not result_text:
                result_text = "测试完成，但未检测到任何结果"
            
            QMessageBox.information(self, "连接测试结果", result_text)
            
        except Exception as e:
            logger.error(f"测试连接失败: {e}")
            error_msg = str(e)[:200] if len(str(e)) > 200 else str(e)
            QMessageBox.critical(self, "测试失败", f"测试连接时出错：\n{error_msg}")

