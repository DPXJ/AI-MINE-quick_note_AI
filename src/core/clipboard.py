"""剪切板监控模块"""
import time
import pyperclip
from threading import Thread, Event
from typing import Callable, Optional
from loguru import logger


class ClipboardMonitor:
    """剪切板监控器"""
    
    def __init__(
        self, 
        callback: Callable[[str], None],
        check_interval: float = 1.0,
        min_length: int = 10,
        max_length: int = 5000
    ):
        """
        初始化剪切板监控器
        
        Args:
            callback: 检测到新内容时的回调函数
            check_interval: 检查间隔（秒）
            min_length: 最小字符数
            max_length: 最大字符数
        """
        self.callback = callback
        self.check_interval = check_interval
        self.min_length = min_length
        self.max_length = max_length
        
        self.enabled = False
        self.thread: Optional[Thread] = None
        self.stop_event = Event()
        self.last_content = ""
        self.history: list = []  # 剪切板历史记录
        self.max_history = 50  # 最多保存50条历史
        
        logger.info("剪切板监控器已初始化")
    
    def start(self):
        """启动监控"""
        if self.enabled:
            logger.warning("剪切板监控已经在运行")
            return
        
        self.enabled = True
        self.stop_event.clear()
        
        # 获取当前剪切板内容作为初始值
        try:
            self.last_content = pyperclip.paste()
        except Exception as e:
            logger.error(f"获取初始剪切板内容失败: {e}")
            self.last_content = ""
        
        # 启动监控线程
        self.thread = Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        
        logger.info("剪切板监控已启动")
    
    def stop(self):
        """停止监控"""
        if not self.enabled:
            return
        
        self.enabled = False
        self.stop_event.set()
        
        if self.thread:
            self.thread.join(timeout=2)
        
        logger.info("剪切板监控已停止")
    
    def toggle(self) -> bool:
        """切换监控状态"""
        if self.enabled:
            self.stop()
        else:
            self.start()
        return self.enabled
    
    def _monitor_loop(self):
        """监控循环"""
        logger.info("剪切板监控循环已启动")
        
        while not self.stop_event.is_set():
            try:
                # 获取当前剪切板内容
                current_content = pyperclip.paste()
                
                # 检查是否有新内容
                if current_content != self.last_content:
                    # 验证内容
                    if self._validate_content(current_content):
                        logger.info(f"检测到新的剪切板内容: {current_content[:50]}...")
                        
                        # 添加到历史记录
                        self._add_to_history(current_content)
                        
                        # 调用回调函数
                        try:
                            self.callback(current_content)
                        except Exception as e:
                            logger.error(f"回调函数执行失败: {e}")
                    
                    # 更新最后内容
                    self.last_content = current_content
                
            except Exception as e:
                logger.error(f"剪切板监控异常: {e}")
            
            # 等待下一次检查
            self.stop_event.wait(self.check_interval)
        
        logger.info("剪切板监控循环已退出")
    
    def _validate_content(self, content: str) -> bool:
        """验证内容是否有效"""
        # 检查是否为空
        if not content or not content.strip():
            return False
        
        # 检查长度
        content_length = len(content)
        if content_length < self.min_length or content_length > self.max_length:
            logger.debug(f"内容长度不符合要求: {content_length}")
            return False
        
        # 过滤纯数字
        if content.strip().isdigit():
            logger.debug("过滤纯数字内容")
            return False
        
        # 过滤单个URL
        if content.strip().startswith(('http://', 'https://', 'www.')):
            logger.debug("过滤URL")
            return False
        
        return True
    
    def _add_to_history(self, content: str):
        """添加到历史记录"""
        # 避免重复添加相同内容
        if self.history and self.history[-1] == content:
            return
        
        self.history.append(content)
        
        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_history(self, limit: int = 20) -> list:
        """获取历史记录"""
        return self.history[-limit:] if limit else self.history

