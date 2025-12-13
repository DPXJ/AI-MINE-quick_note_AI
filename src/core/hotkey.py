"""全局快捷键监听模块"""
from pynput import keyboard
from typing import Callable, Dict
from loguru import logger


class HotkeyListener:
    """全局快捷键监听器"""
    
    def __init__(self):
        """初始化快捷键监听器"""
        self.listener = None
        self.hotkeys: Dict[str, Callable] = {}
        self.current_keys = set()
        logger.info("快捷键监听器已初始化")
    
    def register(self, hotkey: str, callback: Callable):
        """
        注册快捷键
        
        Args:
            hotkey: 快捷键字符串（如"ctrl+shift+space"）
            callback: 回调函数
        """
        # 标准化快捷键格式
        hotkey_normalized = self._normalize_hotkey(hotkey)
        self.hotkeys[hotkey_normalized] = callback
        logger.info(f"已注册快捷键: {hotkey}")
    
    def start(self):
        """启动监听"""
        if self.listener:
            logger.warning("快捷键监听已经在运行")
            return
        
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        logger.info("快捷键监听已启动")
    
    def stop(self):
        """停止监听"""
        if self.listener:
            self.listener.stop()
            self.listener = None
            logger.info("快捷键监听已停止")
    
    def _normalize_hotkey(self, hotkey: str) -> str:
        """标准化快捷键格式"""
        # 转换为小写
        hotkey = hotkey.lower()
        
        # 替换常见别名
        hotkey = hotkey.replace("ctrl", "control")
        hotkey = hotkey.replace("win", "cmd")
        
        # 分割并排序（保证一致性）
        parts = hotkey.split('+')
        parts = [p.strip() for p in parts]
        
        # 修饰键在前，普通键在后
        modifiers = []
        keys = []
        
        for part in parts:
            if part in ['control', 'ctrl', 'shift', 'alt', 'cmd']:
                if part == 'ctrl':
                    part = 'control'
                modifiers.append(part)
            else:
                keys.append(part)
        
        # 修饰键排序
        modifier_order = {'control': 0, 'shift': 1, 'alt': 2, 'cmd': 3}
        modifiers.sort(key=lambda x: modifier_order.get(x, 99))
        
        return '+'.join(modifiers + keys)
    
    def _get_key_name(self, key) -> str:
        """获取按键名称"""
        try:
            # 特殊键
            if hasattr(key, 'name'):
                return key.name.lower()
            # 字符键
            elif hasattr(key, 'char') and key.char:
                return key.char.lower()
            else:
                return str(key).lower()
        except:
            return ""
    
    def _on_press(self, key):
        """按键按下事件"""
        try:
            key_name = self._get_key_name(key)
            if not key_name:
                return
            
            # 添加到当前按键集合
            self.current_keys.add(key_name)
            
            # 检查是否匹配已注册的快捷键
            self._check_hotkeys()
            
        except Exception as e:
            logger.error(f"按键处理异常: {e}")
    
    def _on_release(self, key):
        """按键释放事件"""
        try:
            key_name = self._get_key_name(key)
            if not key_name:
                return
            
            # 从当前按键集合移除
            self.current_keys.discard(key_name)
            
        except Exception as e:
            logger.error(f"按键释放处理异常: {e}")
    
    def _check_hotkeys(self):
        """检查是否匹配快捷键"""
        # 构建当前按键组合字符串
        if not self.current_keys:
            return
        
        # 分离修饰键和普通键
        modifiers = []
        keys = []
        
        for key in self.current_keys:
            if key in ['ctrl', 'control', 'shift', 'alt', 'cmd', 'ctrl_l', 'ctrl_r', 'shift_l', 'shift_r']:
                # 标准化修饰键名称
                if key in ['ctrl', 'ctrl_l', 'ctrl_r']:
                    key = 'control'
                elif key in ['shift_l', 'shift_r']:
                    key = 'shift'
                if key not in modifiers:
                    modifiers.append(key)
            else:
                keys.append(key)
        
        # 修饰键排序
        modifier_order = {'control': 0, 'shift': 1, 'alt': 2, 'cmd': 3}
        modifiers.sort(key=lambda x: modifier_order.get(x, 99))
        
        # 构建当前组合
        current_combo = '+'.join(modifiers + keys)
        
        # 检查是否匹配
        if current_combo in self.hotkeys:
            logger.info(f"触发快捷键: {current_combo}")
            callback = self.hotkeys[current_combo]
            try:
                callback()
            except Exception as e:
                logger.error(f"快捷键回调执行失败: {e}")

