"""设置界面"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTabWidget, QWidget,
    QTextEdit, QCheckBox, QMessageBox, QGroupBox,
    QComboBox, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from loguru import logger
from src.gui.hotkey_input import HotkeyInput


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
        widget = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel("配置AI识别规则（编辑 config.yaml 文件）：")
        label.setStyleSheet("font-weight: bold; margin: 10px;")
        layout.addWidget(label)
        
        self.rules_text = QTextEdit()
        self.rules_text.setPlaceholderText("在这里显示AI规则配置...")
        self.rules_text.setReadOnly(True)
        self.rules_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        layout.addWidget(self.rules_text)
        
        hint = QLabel("💡 提示：请直接编辑项目目录下的 config.yaml 文件来修改AI规则")
        hint.setStyleSheet("color: #666; font-size: 11px; margin: 5px;")
        layout.addWidget(hint)
        
        widget.setLayout(layout)
        return widget
    
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
        
        # 加载快捷键配置（使用HotkeyInput控件）
        self.hotkey_quick.setText(self.config_obj.hotkey_quick_input)
        self.hotkey_clipboard.setText(self.config_obj.hotkey_toggle_clipboard)
        
        # 加载AI规则（只读显示）
        import yaml
        rules = self.config_obj.config.get('ai_rules', {})
        self.rules_text.setText(yaml.dump(rules, allow_unicode=True))
    
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
            
            # 更新快捷键配置
            if 'hotkeys' not in config_data:
                config_data['hotkeys'] = {}
            
            config_data['hotkeys']['quick_input'] = self.hotkey_quick.text().strip()
            config_data['hotkeys']['toggle_clipboard'] = self.hotkey_clipboard.text().strip()
            
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
            
            # 显示结果
            if not result_text:
                result_text = "测试完成，但未检测到任何结果"
            
            QMessageBox.information(self, "连接测试结果", result_text)
            
        except Exception as e:
            logger.error(f"测试连接失败: {e}")
            error_msg = str(e)[:200] if len(str(e)) > 200 else str(e)
            QMessageBox.critical(self, "测试失败", f"测试连接时出错：\n{error_msg}")

