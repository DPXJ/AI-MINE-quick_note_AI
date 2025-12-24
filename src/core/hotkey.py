"""全局快捷键监听模块 - 使用keyboard库（更稳定）"""
import keyboard
from typing import Callable, Dict
from loguru import logger
import threading
import time


class HotkeyListener:
    """全局快捷键监听器 - 基于keyboard库"""
    
    def __init__(self):
        """初始化快捷键监听器"""
        self.hotkeys: Dict[str, Callable] = {}
        self.hotkey_handles = {}  # 存储快捷键句柄
        self.is_running = False
        self.watchdog_thread = None
        self.stop_watchdog = False
        self.last_trigger_time = {}  # 记录每个快捷键的最后触发时间
        self.start_time = None
        logger.info("快捷键监听器已初始化（keyboard库）")
    
    def register(self, hotkey: str, callback: Callable):
        """
        注册快捷键
        
        Args:
            hotkey: 快捷键字符串（如"ctrl+shift+space"）
            callback: 回调函数
        """
        # 标准化快捷键格式（keyboard库使用的格式）
        hotkey_normalized = self._normalize_hotkey(hotkey)
        self.hotkeys[hotkey_normalized] = callback
        self.last_trigger_time[hotkey_normalized] = None
        logger.info(f"已注册快捷键: {hotkey} -> {hotkey_normalized}")
    
    def start(self):
        """启动监听"""
        if self.is_running:
            logger.warning("快捷键监听已经在运行")
            return
        
        self.is_running = True
        self.stop_watchdog = False
        self.start_time = time.time()
        
        # 注册所有快捷键
        for hotkey, callback in self.hotkeys.items():
            try:
                # 使用keyboard库直接注册快捷键
                # suppress=False 不抑制，避免影响其他应用
                handle = keyboard.add_hotkey(
                    hotkey, 
                    lambda cb=callback, hk=hotkey: self._on_hotkey_triggered(hk, cb),
                    suppress=False
                )
                self.hotkey_handles[hotkey] = handle
                logger.info(f"✓ 快捷键已激活: {hotkey}")
            except Exception as e:
                logger.error(f"✗ 注册快捷键失败 {hotkey}: {e}", exc_info=True)
        
        # 启动简单的看门狗线程（监控整体状态）
        self.watchdog_thread = threading.Thread(target=self._watchdog, daemon=True)
        self.watchdog_thread.start()
        
        logger.info(f"快捷键监听已启动，共注册 {len(self.hotkey_handles)} 个快捷键")
    
    def stop(self):
        """停止监听"""
        self.is_running = False
        self.stop_watchdog = True
        
        # 移除所有快捷键
        for hotkey in list(self.hotkey_handles.keys()):
            try:
                keyboard.remove_hotkey(hotkey)
                logger.debug(f"已移除快捷键: {hotkey}")
            except Exception as e:
                logger.warning(f"移除快捷键失败 {hotkey}: {e}")
        
        self.hotkey_handles.clear()
        logger.info("快捷键监听已停止")
    
    def _watchdog(self):
        """看门狗线程：监控快捷键状态"""
        logger.info("快捷键看门狗已启动")
        
        while not self.stop_watchdog and self.is_running:
            try:
                time.sleep(60)  # 每分钟检查一次
                
                current_time = time.time()
                runtime = int(current_time - self.start_time)
                
                # 统计触发情况
                trigger_stats = []
                for hotkey, last_time in self.last_trigger_time.items():
                    if last_time:
                        time_since = int(current_time - last_time)
                        trigger_stats.append(f"{hotkey}: {time_since}秒前")
                    else:
                        trigger_stats.append(f"{hotkey}: 未触发")
                
                # 记录状态（每10分钟一次）
                if runtime % 600 < 60:  # 每10分钟左右记录一次
                    logger.info(f"快捷键状态: 运行 {runtime//60} 分钟, {', '.join(trigger_stats)}")
                
            except Exception as e:
                logger.error(f"看门狗检查异常: {e}", exc_info=True)
        
        logger.info("快捷键看门狗已停止")
    
    def _normalize_hotkey(self, hotkey: str) -> str:
        """
        标准化快捷键格式（keyboard库格式）
        
        keyboard库使用的格式：
        - "ctrl+shift+space"（小写，用+连接）
        - 支持：ctrl, shift, alt, windows
        """
        # 转换为小写
        hotkey = hotkey.lower()
        
        # keyboard库使用的修饰键名称
        hotkey = hotkey.replace("control", "ctrl")
        hotkey = hotkey.replace("win", "windows")
        
        # 移除多余空格
        parts = [p.strip() for p in hotkey.split('+')]
        
        return '+'.join(parts)
    
    def _on_hotkey_triggered(self, hotkey: str, callback: Callable):
        """快捷键被触发"""
        try:
            current_time = time.time()
            self.last_trigger_time[hotkey] = current_time
            
            logger.info(f"✓ 快捷键触发: {hotkey}")
            
            # 在新线程中执行回调，避免阻塞
            threading.Thread(
                target=self._safe_callback, 
                args=(callback,), 
                daemon=True
            ).start()
            
        except Exception as e:
            logger.error(f"快捷键触发处理异常: {e}", exc_info=True)
    
    def _safe_callback(self, callback: Callable):
        """安全执行回调函数"""
        try:
            callback()
        except Exception as e:
            logger.error(f"快捷键回调执行失败: {e}", exc_info=True)
    
    def is_alive(self) -> bool:
        """检查监听器是否存活"""
        return self.is_running and len(self.hotkey_handles) > 0
    
    def get_status(self) -> dict:
        """获取监听器状态信息"""
        current_time = time.time()
        
        # 计算每个快捷键的触发时间
        trigger_info = {}
        for hotkey, last_time in self.last_trigger_time.items():
            if last_time:
                trigger_info[hotkey] = int(current_time - last_time)
            else:
                trigger_info[hotkey] = None
        
        return {
            'is_running': self.is_running,
            'registered_count': len(self.hotkeys),
            'active_count': len(self.hotkey_handles),
            'registered_hotkeys': list(self.hotkeys.keys()),
            'runtime_seconds': int(current_time - self.start_time) if self.start_time else 0,
            'last_trigger_seconds_ago': trigger_info,
            'library': 'keyboard'
        }
