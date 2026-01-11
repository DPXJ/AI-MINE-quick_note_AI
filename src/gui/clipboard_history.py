"""剪切板历史窗口"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from loguru import logger
import pyperclip


class ClipboardHistoryDialog(QDialog):
    """剪切板历史对话框"""
    
    def __init__(self, main_app, parent=None):
        """
        初始化剪切板历史对话框
        
        Args:
            main_app: 主程序实例
            parent: 父窗口
        """
        super().__init__(parent)
        self.main_app = main_app
        self._init_ui()
        self._load_history()
        logger.info("剪切板历史窗口已初始化")
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle("剪切板历史")
        self.setFixedSize(800, 600)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("📋 剪切板历史")
        title.setStyleSheet("""
            QLabel {
                color: #007acc;
                font-size: 18px;
                font-weight: bold;
                padding: 10px 0;
            }
        """)
        layout.addWidget(title)
        
        # 提示信息
        hint = QLabel("💡 点击列表项查看详情，点击「复制」按钮复制到剪切板")
        hint.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 13px;
                padding: 5px;
            }
        """)
        layout.addWidget(hint)
        
        # 历史列表
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background: white;
                border: 2px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background: #f0f0f0;
            }
            QListWidget::item:selected {
                background: #e3f2fd;
            }
        """)
        self.history_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.history_list, stretch=1)
        
        # 详情显示区域
        detail_label = QLabel("内容详情：")
        detail_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(detail_label)
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(150)
        self.detail_text.setStyleSheet("""
            QTextEdit {
                background: #f9f9f9;
                border: 2px solid #ccc;
                border-radius: 4px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        self.detail_text.setPlaceholderText("双击列表项查看完整内容...")
        layout.addWidget(self.detail_text)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background: #007acc;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #005a9e;
            }
        """)
        refresh_btn.clicked.connect(self._load_history)
        button_layout.addWidget(refresh_btn)
        
        # 复制按钮
        self.copy_btn = QPushButton("📋 复制选中项")
        self.copy_btn.setEnabled(False)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background: #5cb85c;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4cae4c;
            }
            QPushButton:disabled {
                background: #ccc;
                color: #666;
            }
        """)
        self.copy_btn.clicked.connect(self._copy_selected)
        button_layout.addWidget(self.copy_btn)
        
        # 关闭按钮
        close_btn = QPushButton("✕ 关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background: #f0f0f0;
                color: #666;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 连接列表选择事件
        self.history_list.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _load_history(self):
        """加载剪切板历史"""
        try:
            self.history_list.clear()
            self.detail_text.clear()
            self.copy_btn.setEnabled(False)
            
            # 从主程序获取历史
            history = []
            if self.main_app and hasattr(self.main_app, 'clipboard_monitor'):
                try:
                    history = self.main_app.clipboard_monitor.get_history(limit=50)
                except Exception as e:
                    logger.warning(f"获取剪切板历史失败: {e}")
            
            if not history:
                item = QListWidgetItem("暂无剪切板历史记录")
                item.setFlags(Qt.NoItemFlags)  # 不可选择
                self.history_list.addItem(item)
                return
            
            # 显示历史（最新的在前）
            for i, content in enumerate(reversed(history), 1):
                preview = content[:60] + "..." if len(content) > 60 else content
                item = QListWidgetItem(f"[{i}] {preview}")
                item.setData(Qt.UserRole, content)  # 存储完整内容
                self.history_list.addItem(item)
            
            logger.info(f"已加载 {len(history)} 条剪切板历史")
            
        except Exception as e:
            logger.error(f"加载剪切板历史失败: {e}")
            item = QListWidgetItem("加载失败，请重试")
            item.setFlags(Qt.NoItemFlags)
            self.history_list.addItem(item)
    
    def _on_selection_changed(self):
        """列表选择变化"""
        current_item = self.history_list.currentItem()
        if current_item and current_item.data(Qt.UserRole):
            content = current_item.data(Qt.UserRole)
            self.detail_text.setText(content)
            self.copy_btn.setEnabled(True)
        else:
            self.detail_text.clear()
            self.copy_btn.setEnabled(False)
    
    def _on_item_double_clicked(self, item):
        """双击列表项"""
        if item and item.data(Qt.UserRole):
            content = item.data(Qt.UserRole)
            self.detail_text.setText(content)
            self.copy_btn.setEnabled(True)
    
    def _copy_selected(self):
        """复制选中项到剪切板"""
        current_item = self.history_list.currentItem()
        if current_item and current_item.data(Qt.UserRole):
            content = current_item.data(Qt.UserRole)
            try:
                pyperclip.copy(content)
                logger.info("已复制到剪切板")
                
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "复制成功",
                    "内容已复制到剪切板！"
                )
            except Exception as e:
                logger.error(f"复制失败: {e}")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self,
                    "复制失败",
                    f"复制到剪切板失败：\n{str(e)}"
                )

