"""全局快捷键监听模块"""
from pynput import keyboard
from typing import Callable, Dict
from loguru import logger
import threading
import time


class HotkeyListener:
    """全局快捷键监听器"""
    
    def __init__(self):
        """初始化快捷键监听器"""
        self.listener = None
        self.hotkeys: Dict[str, Callable] = {}
        self.current_keys = set()
        self.is_running = False
        self.watchdog_thread = None
        self.stop_watchdog = False
        self.last_activity_time = None  # 最后一次按键活动时间
        self.last_hotkey_trigger_time = None  # 最后一次快捷键触发时间（关键！）
        self.last_check_time = None  # 最后一次看门狗检查时间
        self.start_time = None  # 监听器启动时间
        self.restart_count = 0  # 重启次数统计
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
        if self.is_running:
            logger.warning("快捷键监听已经在运行")
            return
        
        self.is_running = True
        self.stop_watchdog = False
        self._start_listener()
        
        # 启动看门狗线程，监控监听器状态
        self.watchdog_thread = threading.Thread(target=self._watchdog, daemon=True)
        self.watchdog_thread.start()
        logger.info("快捷键监听已启动（含看门狗）")
    
    def stop(self):
        """停止监听"""
        self.is_running = False
        self.stop_watchdog = True
        
        if self.listener:
            try:
                self.listener.stop()
            except:
                pass
            self.listener = None
        
        logger.info("快捷键监听已停止")
    
    def _start_listener(self):
        """内部方法：启动监听器"""
        try:
            # 完全停止并清理旧监听器
            if self.listener:
                try:
                    self.listener.stop()
                    self.listener.join(timeout=1.0)  # 等待线程结束，最多1秒
                except Exception as e:
                    logger.warning(f"停止旧监听器时出错: {e}")
                finally:
                    self.listener = None
            
            # 重置状态
            self.current_keys.clear()
            
            # suppress=False 确保异常不会终止监听线程
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
                suppress=False
            )
            self.listener.start()
            
            # 等待一小段时间确保监听器真正启动
            time.sleep(0.2)
            
            # 验证是否成功启动
            if self.listener.is_alive():
                current_time = time.time()
                self.start_time = current_time  # 记录启动时间
                self.last_activity_time = current_time  # 初始化活动时间
                # 注意：last_hotkey_trigger_time 初始为 None，只有真正触发快捷键后才设置
                # 这样看门狗可以区分"从未触发"和"长时间未触发"
                logger.info("快捷键监听器已启动并验证成功")
            else:
                logger.error("快捷键监听器启动失败，线程未存活")
                raise RuntimeError("监听器线程启动失败")
                
        except Exception as e:
            logger.error(f"启动快捷键监听器失败: {e}", exc_info=True)
            self.listener = None
            raise
    
    def _watchdog(self):
        """看门狗线程：监控监听器是否存活，如果死掉则自动重启"""
        logger.info("快捷键看门狗已启动")
        self.last_check_time = time.time()
        
        while not self.stop_watchdog and self.is_running:
            try:
                time.sleep(10)  # 每10秒检查一次（降低检查频率，减少CPU占用和误判）
                current_time = time.time()
                self.last_check_time = current_time
                
                # 检查1：监听器线程是否存活
                listener_dead = False
                if self.listener:
                    if not self.listener.is_alive():
                        logger.warning("检测到快捷键监听器线程已停止，正在重启...")
                        listener_dead = True
                else:
                    logger.warning("监听器对象丢失，正在重新创建...")
                    listener_dead = True
                
                # 检查2：快捷键触发检测（放宽条件，避免误判）
                # 情况A：如果从未触发过快捷键，且启动超过5分钟，才认为可能失效
                if not listener_dead and self.last_hotkey_trigger_time is None and self.start_time:
                    time_since_start = current_time - self.start_time
                    if time_since_start > 300:  # 5分钟从未触发过快捷键（放宽条件）
                        logger.warning(f"检测到监听器可能失效（启动{int(time_since_start)}秒从未触发快捷键），强制重启...")
                        listener_dead = True
                # 情况B：如果之前触发过，但超过10分钟没有触发，认为失效（放宽条件）
                elif not listener_dead and self.last_hotkey_trigger_time is not None:
                    time_since_hotkey = current_time - self.last_hotkey_trigger_time
                    if time_since_hotkey > 600:  # 10分钟无快捷键触发（放宽条件）
                        logger.warning(f"检测到监听器可能失效（{int(time_since_hotkey)}秒无快捷键触发），强制重启...")
                        listener_dead = True
                
                # 检查3：心跳检测 - 放宽条件，只有超过2分钟没有按键活动才认为失效
                if not listener_dead and self.last_activity_time:
                    time_since_activity = current_time - self.last_activity_time
                    if time_since_activity > 120:  # 2分钟无活动（放宽条件）
                        logger.warning(f"检测到监听器可能失效（{int(time_since_activity)}秒无按键活动），强制重启...")
                        listener_dead = True
                
                # 检查4：主动测试 - 定期清理可能卡住的按键状态
                if not listener_dead and self.current_keys:
                    # 如果按键集合不为空，但超过5秒没有活动，可能是状态卡住了
                    if self.last_activity_time:
                        time_since_activity = current_time - self.last_activity_time
                        if time_since_activity > 5:  # 5秒无活动但按键集合不为空
                            logger.debug(f"检测到按键状态可能卡住，清理按键集合: {self.current_keys}")
                            self.current_keys.clear()  # 清理可能卡住的状态
                
                # 如果需要重启
                if listener_dead:
                    self.restart_count += 1
                    logger.info(f"开始第 {self.restart_count} 次重启...")
                    
                    # 完全停止旧监听器
                    if self.listener:
                        try:
                            self.listener.stop()
                        except:
                            pass
                        self.listener = None
                    
                    # 等待一小段时间确保完全停止
                    time.sleep(0.5)
                    
                    # 重新启动
                    self._start_listener()
                    # start_time 已在 _start_listener 中设置
                    self.last_activity_time = time.time()  # 重置活动时间
                    self.last_hotkey_trigger_time = None  # 重置快捷键触发时间（等待首次触发）
                    logger.info(f"快捷键监听器已重启（第 {self.restart_count} 次）")
                else:
                    # 正常状态，记录日志（每30秒一次，避免日志过多）
                    if self.last_hotkey_trigger_time:
                        time_since_hotkey = current_time - self.last_hotkey_trigger_time
                        if int(time_since_hotkey) % 30 == 0 and time_since_hotkey > 0:
                            logger.debug(f"监听器正常，距离上次快捷键触发 {int(time_since_hotkey)} 秒")
                    elif self.last_activity_time:
                        time_since_activity = current_time - self.last_activity_time
                        if int(time_since_activity) % 30 == 0 and time_since_activity > 0:
                            logger.debug(f"监听器正常，距离上次活动 {int(time_since_activity)} 秒")
                    
            except Exception as e:
                logger.error(f"看门狗检查异常: {e}", exc_info=True)
        
        logger.info("快捷键看门狗已停止")
    
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
            # 特殊键（如 Key.space, Key.ctrl 等）
            if hasattr(key, 'name'):
                key_name = key.name.lower()
                # 处理 pynput 的特殊键名称
                if key_name == 'space':
                    return 'space'
                return key_name
            # 字符键
            elif hasattr(key, 'char') and key.char:
                char = key.char
                # 空格字符特殊处理
                if char == ' ':
                    return 'space'
                return char.lower()
            else:
                # 尝试从字符串表示中提取
                key_str = str(key).lower()
                if 'space' in key_str:
                    return 'space'
                return key_str
        except Exception as e:
            logger.debug(f"获取按键名称失败: {e}, key={key}")
            return ""
    
    def _on_press(self, key):
        """按键按下事件"""
        try:
            # 更新活动时间（心跳）
            self.last_activity_time = time.time()
            
            key_name = self._get_key_name(key)
            if not key_name:
                return True  # 返回 True 继续监听
            
            # 添加到当前按键集合
            self.current_keys.add(key_name)
            
            # 调试：记录修饰键的按下（帮助诊断问题）
            if key_name in ['ctrl', 'control', 'ctrl_l', 'ctrl_r', 'shift', 'shift_l', 'shift_r']:
                logger.debug(f"检测到修饰键按下: {key_name}, 当前按键集合: {self.current_keys}")
            
            # 检查是否匹配已注册的快捷键
            self._check_hotkeys()
            
        except Exception as e:
            logger.error(f"按键处理异常: {e}", exc_info=True)
        
        return True  # 始终返回 True，确保监听继续
    
    def _on_release(self, key):
        """按键释放事件"""
        try:
            # 更新活动时间
            self.last_activity_time = time.time()
            
            key_name = self._get_key_name(key)
            if not key_name:
                return True  # 返回 True 继续监听
            
            # 标准化修饰键名称
            normalized_name = key_name
            if key_name in ['ctrl', 'ctrl_l', 'ctrl_r']:
                normalized_name = 'control'
            elif key_name in ['shift_l', 'shift_r']:
                normalized_name = 'shift'
            
            # 移除所有可能的变体（包括标准化后的名称）
            keys_to_remove = [key_name, normalized_name]
            for k in keys_to_remove:
                self.current_keys.discard(k)
            
            # 对于普通键（如space），延迟一小段时间再移除，确保快捷键匹配有机会完成
            if key_name not in ['ctrl', 'control', 'ctrl_l', 'ctrl_r', 'shift', 'shift_l', 'shift_r', 'alt', 'cmd']:
                def delayed_remove():
                    time.sleep(0.05)  # 缩短延迟到50ms
                    self.current_keys.discard(key_name)
                    if normalized_name != key_name:
                        self.current_keys.discard(normalized_name)
                threading.Thread(target=delayed_remove, daemon=True).start()
            
        except Exception as e:
            logger.error(f"按键释放处理异常: {e}", exc_info=True)
        
        return True  # 始终返回 True，确保监听继续
    
    def is_alive(self) -> bool:
        """检查监听器是否存活"""
        return (
            self.is_running and 
            self.listener is not None and 
            self.listener.is_alive()
        )
    
    def get_status(self) -> dict:
        """获取监听器状态信息"""
        current_time = time.time()
        time_since_activity = None
        if self.last_activity_time:
            time_since_activity = current_time - self.last_activity_time
        
        time_since_hotkey = None
        if self.last_hotkey_trigger_time is not None:
            time_since_hotkey = current_time - self.last_hotkey_trigger_time
        
        return {
            'is_running': self.is_running,
            'listener_exists': self.listener is not None,
            'listener_alive': self.listener.is_alive() if self.listener else False,
            'watchdog_running': self.watchdog_thread.is_alive() if self.watchdog_thread else False,
            'registered_hotkeys': list(self.hotkeys.keys()),
            'restart_count': self.restart_count,
            'last_activity_seconds_ago': int(time_since_activity) if time_since_activity else None,
            'last_hotkey_trigger_seconds_ago': int(time_since_hotkey) if time_since_hotkey is not None else None,
            'last_check_seconds_ago': int(current_time - self.last_check_time) if self.last_check_time else None
        }
    
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
        
        # 调试日志：记录按键组合（仅在调试模式下）
        if len(modifiers) >= 2 and len(keys) >= 1:  # 只记录可能的快捷键组合
            logger.debug(f"检测到按键组合: {current_combo}, 已注册快捷键: {list(self.hotkeys.keys())}")
        
        # 检查是否匹配
        if current_combo in self.hotkeys:
            logger.info(f"触发快捷键: {current_combo}")
            # 更新快捷键触发时间（关键！用于检测监听器是否真正工作）
            self.last_hotkey_trigger_time = time.time()
            callback = self.hotkeys[current_combo]
            try:
                # 在新线程中执行回调，避免阻塞监听线程
                threading.Thread(target=self._safe_callback, args=(callback,), daemon=True).start()
            except Exception as e:
                logger.error(f"启动快捷键回调线程失败: {e}", exc_info=True)
    
    def _safe_callback(self, callback: Callable):
        """安全执行回调函数"""
        try:
            callback()
        except Exception as e:
            logger.error(f"快捷键回调执行失败: {e}", exc_info=True)

