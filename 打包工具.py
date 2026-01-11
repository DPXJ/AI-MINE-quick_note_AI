"""
QuickNote AI - 图形化打包工具
提供友好的打包界面
"""
import sys
import subprocess
import shutil
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QTextEdit, 
    QProgressBar, QMessageBox, QCheckBox, QGroupBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QTextCursor


class BuildWorker(QThread):
    """打包工作线程"""
    
    output_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, clean_build=True, one_file=False):
        super().__init__()
        self.clean_build = clean_build
        self.one_file = one_file
        self.project_root = Path(__file__).parent
    
    def run(self):
        """执行打包"""
        try:
            # 步骤1: 检查依赖
            self.output_signal.emit("=== [1/4] 检查依赖 ===\n")
            self.progress_signal.emit(10)
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", "pyinstaller"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.output_signal.emit("未安装 PyInstaller，正在安装...\n")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "pyinstaller"],
                    capture_output=True,
                    text=True
                )
                self.output_signal.emit(result.stdout)
            else:
                self.output_signal.emit("✓ PyInstaller 已安装\n")
            
            self.progress_signal.emit(25)
            
            # 步骤2: 清理旧文件
            if self.clean_build:
                self.output_signal.emit("\n=== [2/4] 清理旧文件 ===\n")
                
                build_dir = self.project_root / "build"
                dist_dir = self.project_root / "dist"
                
                if build_dir.exists():
                    shutil.rmtree(build_dir)
                    self.output_signal.emit("✓ 已删除 build 目录\n")
                
                if dist_dir.exists():
                    shutil.rmtree(dist_dir)
                    self.output_signal.emit("✓ 已删除 dist 目录\n")
            else:
                self.output_signal.emit("\n=== [2/4] 跳过清理 ===\n")
            
            self.progress_signal.emit(40)
            
            # 步骤3: 修改 spec 文件（如果需要单文件）
            spec_file = self.project_root / "build.spec"
            if self.one_file and spec_file.exists():
                self.output_signal.emit("\n=== 配置单文件模式 ===\n")
                # 这里可以动态修改 spec 文件，简化起见暂时跳过
                self.output_signal.emit("⚠ 单文件模式需要手动修改 build.spec\n")
            
            # 步骤3: 执行打包
            self.output_signal.emit("\n=== [3/4] 开始打包 ===\n")
            self.output_signal.emit("这可能需要几分钟，请耐心等待...\n\n")
            self.progress_signal.emit(50)
            
            # 执行 PyInstaller
            process = subprocess.Popen(
                [sys.executable, "-m", "PyInstaller", "build.spec"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(self.project_root)
            )
            
            # 实时输出日志
            for line in process.stdout:
                self.output_signal.emit(line)
                # 模拟进度（50-90%）
                if "Building" in line:
                    self.progress_signal.emit(60)
                elif "Analyzing" in line:
                    self.progress_signal.emit(70)
                elif "Copying" in line:
                    self.progress_signal.emit(80)
            
            process.wait()
            self.progress_signal.emit(90)
            
            # 步骤4: 检查结果
            self.output_signal.emit("\n=== [4/4] 检查打包结果 ===\n")
            
            exe_path = self.project_root / "dist" / "QuickNote_AI" / "QuickNote_AI.exe"
            
            if exe_path.exists():
                exe_size = exe_path.stat().st_size / (1024 * 1024)  # MB
                self.output_signal.emit(f"✓ 打包成功！\n")
                self.output_signal.emit(f"✓ 文件位置: {exe_path}\n")
                self.output_signal.emit(f"✓ 文件大小: {exe_size:.2f} MB\n")
                self.progress_signal.emit(100)
                self.finished_signal.emit(True, str(exe_path))
            else:
                self.output_signal.emit("✗ 打包失败，未找到可执行文件\n")
                self.finished_signal.emit(False, "打包失败")
            
        except Exception as e:
            self.output_signal.emit(f"\n✗ 打包过程出错: {str(e)}\n")
            self.finished_signal.emit(False, str(e))


class BuilderWindow(QMainWindow):
    """打包工具主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuickNote AI - 打包工具")
        self.setMinimumSize(800, 600)
        
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("QuickNote AI 打包工具")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 选项组
        options_group = QGroupBox("打包选项")
        options_layout = QVBoxLayout()
        
        self.clean_check = QCheckBox("清理旧的构建文件（推荐）")
        self.clean_check.setChecked(True)
        options_layout.addWidget(self.clean_check)
        
        self.onefile_check = QCheckBox("单文件模式（需要手动修改 build.spec）")
        self.onefile_check.setChecked(False)
        self.onefile_check.setEnabled(False)  # 暂时禁用
        options_layout.addWidget(self.onefile_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 日志输出
        log_label = QLabel("打包日志：")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.build_button = QPushButton("开始打包")
        self.build_button.clicked.connect(self.start_build)
        self.build_button.setMinimumHeight(40)
        button_layout.addWidget(self.build_button)
        
        self.open_button = QPushButton("打开输出目录")
        self.open_button.clicked.connect(self.open_dist_folder)
        self.open_button.setEnabled(False)
        self.open_button.setMinimumHeight(40)
        button_layout.addWidget(self.open_button)
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.close)
        self.close_button.setMinimumHeight(40)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.worker = None
    
    def start_build(self):
        """开始打包"""
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.build_button.setEnabled(False)
        self.open_button.setEnabled(False)
        
        # 创建工作线程
        self.worker = BuildWorker(
            clean_build=self.clean_check.isChecked(),
            one_file=self.onefile_check.isChecked()
        )
        
        # 连接信号
        self.worker.output_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.build_finished)
        
        # 启动线程
        self.worker.start()
    
    def append_log(self, text: str):
        """追加日志"""
        self.log_text.insertPlainText(text)
        self.log_text.moveCursor(QTextCursor.End)
    
    def update_progress(self, value: int):
        """更新进度"""
        self.progress_bar.setValue(value)
    
    def build_finished(self, success: bool, message: str):
        """打包完成"""
        self.build_button.setEnabled(True)
        
        if success:
            self.open_button.setEnabled(True)
            QMessageBox.information(
                self,
                "打包成功",
                f"QuickNote AI 已成功打包！\n\n"
                f"可执行文件位置：\n{message}\n\n"
                f"使用说明：\n"
                f"1. 确保配置文件 (.env 和 config.yaml) 在 exe 同目录下\n"
                f"2. 双击 QuickNote_AI.exe 运行\n"
                f"3. 程序会最小化到系统托盘"
            )
        else:
            QMessageBox.critical(
                self,
                "打包失败",
                f"打包过程中出现错误：\n{message}\n\n"
                f"请查看日志输出了解详情。"
            )
    
    def open_dist_folder(self):
        """打开输出目录"""
        dist_path = Path(__file__).parent / "dist"
        if dist_path.exists():
            import os
            os.startfile(str(dist_path))


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("QuickNote AI Builder")
    
    window = BuilderWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

