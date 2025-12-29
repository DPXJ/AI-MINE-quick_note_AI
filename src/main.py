"""QuickNote AI - 主程序入口"""
import sys
import os
from pathlib import Path

# 确保项目根目录在Python路径中
_current_dir = Path(__file__).parent.parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, QThread, Qt
from loguru import logger

# 确定根目录（打包后使用EXE所在目录，开发模式使用项目根目录）
if getattr(sys, 'frozen', False):
    root_dir = Path(sys.executable).parent
else:
    root_dir = Path(__file__).parent.parent

# 配置日志（日志文件放在根目录下的logs文件夹）
logs_dir = root_dir / "logs"
logs_dir.mkdir(exist_ok=True)
logger.add(
    str(logs_dir / "quicknote_{time}.log"),
    rotation="10 MB",
    retention="7 days",
    encoding="utf-8",
    enqueue=True
)

from src.utils.config import config
from src.gui.quick_input import QuickInputWindow
from src.gui.tray_icon import TrayIcon
from src.gui.settings import SettingsDialog
from src.core.hotkey import HotkeyListener
from src.core.clipboard import ClipboardMonitor
from src.core.ai_processor import AIProcessor
from src.integrations.notion_api import NotionAPI
from src.integrations.flomo_api import FlomoAPI
from src.integrations.ticktick_api import TickTickAPI
from src.utils.clipboard_dedupe import ClipboardDedupeStore


class QuickNoteApp(QObject):
    """主应用程序类"""
    
    # 定义信号（用于线程安全的 GUI 操作）
    show_quick_input_signal = pyqtSignal()
    toggle_clipboard_signal = pyqtSignal()
    
    def __init__(self, app: QApplication):
        """初始化应用"""
        super().__init__()
        self.app = app
        
        logger.info("=" * 50)
        logger.info("QuickNote AI 启动中...")
        logger.info("=" * 50)
        
        # 验证配置（允许通过设置界面配置，不强制退出）
        if not config.validate():
            logger.warning("配置验证失败，将在设置界面中配置")
            # 不强制退出，允许用户通过设置界面配置
            # 后续在使用时会再次验证
        
        # 初始化组件
        self._init_components()
        self._connect_signals()
        
        # 启动定期状态检查（每2分钟检查一次快捷键状态）
        self._start_status_check()
        
        logger.info("QuickNote AI 启动完成")
    
    def _init_components(self):
        """初始化所有组件"""
        try:
            # GUI组件
            ui_config = config.get("ui.quick_input", {})
            # 遮罩配置：默认黑色 + 100%不透明（alpha=255），且启动即生效
            mask_color = config.get('ui.mask_color', [0, 0, 0])
            mask_alpha = config.get('ui.mask_alpha', 255)
            self.quick_input_window = QuickInputWindow({
                **ui_config,
                'mask_color': mask_color,
                'mask_alpha': mask_alpha,
            })
            self.tray_icon = TrayIcon(self.app)
            self.settings_dialog = None
            
            # 快捷键监听器
            self.hotkey_listener = HotkeyListener()
            # 使用信号发射，确保 GUI 操作在主线程执行
            self.hotkey_listener.register(
                config.hotkey_quick_input,
                lambda: self.show_quick_input_signal.emit()
            )
            self.hotkey_listener.register(
                config.hotkey_toggle_clipboard,
                lambda: self.toggle_clipboard_signal.emit()
            )
            self.hotkey_listener.start()
            
            # API集成
            self.notion_api = NotionAPI(
                config.notion_api_key,
                config.notion_database_id
            )
            
            self.flomo_api = None
            if config.flomo_api_url:
                self.flomo_api = FlomoAPI(config.flomo_api_url)
            
            self.ticktick_api = None
            if (config.ticktick_smtp_user and 
                config.ticktick_smtp_pass and 
                config.ticktick_email):
                self.ticktick_api = TickTickAPI(
                    smtp_host=config.ticktick_smtp_host,
                    smtp_port=config.ticktick_smtp_port,
                    smtp_user=config.ticktick_smtp_user,
                    smtp_pass=config.ticktick_smtp_pass,
                    ticktick_email=config.ticktick_email
                )
            
            # AI处理器
            self.ai_processor = AIProcessor(config.ai_provider)
            
            # 剪切板监控
            self.clipboard_monitor = ClipboardMonitor(
                callback=self._on_clipboard_content,
                check_interval=config.clipboard_check_interval,
                min_length=config.clipboard_min_length,
                max_length=config.clipboard_max_length
            )

            # 剪切板自动同步去重（跨重启持久化；仅影响自动同步，不影响手动输入）
            dedupe_enabled = config.get("clipboard.dedupe.enabled", True)
            dedupe_ttl_hours = config.get("clipboard.dedupe.ttl_hours", 48)
            try:
                dedupe_ttl_seconds = int(float(dedupe_ttl_hours) * 3600)
            except Exception:
                dedupe_ttl_seconds = 48 * 3600
            dedupe_persist = config.get("clipboard.dedupe.persist", True)
            dedupe_path = config.root_dir / "data" / "clipboard_dedupe.json"
            self.clipboard_dedupe = ClipboardDedupeStore(
                path=dedupe_path if dedupe_persist else (config.root_dir / "data" / "clipboard_dedupe.tmp.json"),
                ttl_seconds=dedupe_ttl_seconds,
                enabled=bool(dedupe_enabled),
            )
            
            # 检查总开关（从ai_rules读取）
            clipboard_monitor_enabled = config.config.get('ai_rules', {}).get('clipboard_monitor', True)
            
            # 如果配置启用，则启动剪切板监控
            if config.clipboard_enabled and clipboard_monitor_enabled:
                self.clipboard_monitor.start()
            
            logger.info("所有组件初始化完成")
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 快速输入窗口
        self.quick_input_window.content_submitted.connect(self._on_quick_input_submitted)
        # 【自愈机制】窗口显示时检查快捷键
        self.quick_input_window.window_shown.connect(self._check_and_heal_hotkey)
        
        # 系统托盘
        self.tray_icon.quick_input_triggered.connect(self._show_quick_input)
        self.tray_icon.settings_triggered.connect(self._show_settings)
        self.tray_icon.quit_triggered.connect(self._quit_app)
        self.tray_icon.restart_triggered.connect(self._restart_app)
        self.tray_icon.restart_hotkey_triggered.connect(self._restart_hotkey_listener)
        self.tray_icon.clipboard_toggled.connect(self._on_clipboard_toggled)
        self.tray_icon.clipboard_history_triggered.connect(self._show_clipboard_history)
        
        # 线程安全的快捷键信号（从 pynput 线程到主线程）
        self.show_quick_input_signal.connect(self._show_quick_input)
        self.toggle_clipboard_signal.connect(self._toggle_clipboard)
        
        # 设置保存后重新初始化
        if self.settings_dialog:
            self.settings_dialog.settings_saved.connect(self._reload_config)
    
    def _start_status_check(self):
        """启动定期状态检查"""
        from PyQt5.QtCore import QTimer
        
        def check_status():
            """检查快捷键监听器状态"""
            try:
                status = self.hotkey_listener.get_status()
                
                # 如果监听器不存活，记录警告
                if not status['listener_alive']:
                    logger.warning(f"快捷键监听器状态异常: {status}")
                    # 尝试重启
                    if self.hotkey_listener.is_running:
                        logger.info("检测到快捷键监听器异常，自动重启...")
                        self._restart_hotkey_listener()
                else:
                    # 正常状态，每10分钟记录一次详细信息（避免日志过多）
                    import time
                    # 优先显示快捷键触发时间（更关键）
                    if status.get('last_hotkey_trigger_seconds_ago') is not None:
                        if status['last_hotkey_trigger_seconds_ago'] % 600 < 120:  # 每10分钟记录一次
                            logger.debug(f"快捷键监听器状态正常: 重启次数={status['restart_count']}, "
                                       f"距离上次快捷键触发={status['last_hotkey_trigger_seconds_ago']}秒")
                    elif status.get('last_activity_seconds_ago') is not None:
                        if status['last_activity_seconds_ago'] % 600 < 120:  # 每10分钟记录一次
                            logger.debug(f"快捷键监听器状态正常: 重启次数={status['restart_count']}, "
                                       f"距离上次活动={status['last_activity_seconds_ago']}秒, "
                                       f"尚未触发快捷键")
            except Exception as e:
                logger.error(f"状态检查异常: {e}", exc_info=True)
        
        # 每2分钟检查一次
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(check_status)
        self.status_timer.start(120000)  # 120秒 = 2分钟
        logger.info("快捷键状态定期检查已启动（每2分钟）")
    
    def _show_quick_input(self):
        """显示快速输入窗口"""
        logger.info("显示快速输入窗口")
        self.quick_input_window.show_at_center()
    
    def _show_settings(self):
        """显示设置界面"""
        logger.info("显示设置界面")
        if not self.settings_dialog:
            # QDialog的parent应该是QWidget或None，不能是QApplication
            self.settings_dialog = SettingsDialog(config, parent=None)
            self.settings_dialog.settings_saved.connect(self._reload_config)
            # 设置主程序引用，用于访问剪切板历史
            self.settings_dialog.main_app = self
        self.settings_dialog.exec_()
    
    def _show_clipboard_history(self):
        """显示剪切板历史"""
        logger.info("显示剪切板历史")
        from src.gui.clipboard_history import ClipboardHistoryDialog
        
        history_dialog = ClipboardHistoryDialog(self, parent=None)
        history_dialog.exec_()
    
    def _reload_config(self):
        """重新加载配置（设置保存后）"""
        logger.info("重新加载配置")
        from src.utils.config import config as new_config
        
        # 重新加载环境变量和YAML配置
        if new_config.env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(new_config.env_file, override=True)
        
        # 重新加载YAML配置
        new_config.config = new_config._load_config()
        
        # 更新快速输入窗口的配置（包括遮罩设置）
        if self.quick_input_window:
            try:
                new_ui_config = new_config.get("ui.quick_input", {})
                # 更新遮罩配置（从ui节点读取）
                mask_color = new_config.get('ui.mask_color', [0, 0, 0])
                mask_alpha = new_config.get('ui.mask_alpha', 255)
                # 更新遮罩配置
                self.quick_input_window.config = {
                    **new_ui_config,
                    'mask_color': mask_color,
                    'mask_alpha': mask_alpha,
                }
                logger.info(f"快速输入窗口配置已更新（包括遮罩设置: 颜色={mask_color}, 透明度={mask_alpha}）")
            except Exception as e:
                logger.error(f"更新快速输入窗口配置失败: {e}", exc_info=True)
        
        # 更新剪切板监控状态（根据总开关）
        clipboard_monitor_enabled = new_config.config.get('ai_rules', {}).get('clipboard_monitor', True)
        if clipboard_monitor_enabled and new_config.clipboard_enabled:
            if not self.clipboard_monitor.enabled:
                self.clipboard_monitor.start()
        else:
            if self.clipboard_monitor.enabled:
                self.clipboard_monitor.stop()
        
        # 重新初始化API
        try:
            if new_config.validate():
                self.ai_processor = AIProcessor(new_config.ai_provider)
                logger.info("AI处理器已重新初始化")
            
            if new_config.notion_api_key and new_config.notion_database_id:
                self.notion_api = NotionAPI(
                    new_config.notion_api_key,
                    new_config.notion_database_id
                )
                logger.info("Notion API已重新初始化")
            
            if new_config.flomo_api_url:
                self.flomo_api = FlomoAPI(new_config.flomo_api_url)
                logger.info("Flomo API已重新初始化")
            
                if (new_config.ticktick_smtp_user and 
                    new_config.ticktick_smtp_pass and 
                    new_config.ticktick_email):
                    self.ticktick_api = TickTickAPI(
                        smtp_host=new_config.ticktick_smtp_host,
                        smtp_port=new_config.ticktick_smtp_port,
                        smtp_user=new_config.ticktick_smtp_user,
                        smtp_pass=new_config.ticktick_smtp_pass,
                        ticktick_email=new_config.ticktick_email
                    )
                    logger.info("TickTick API已重新初始化")
            
            # 快捷键配置已保存到config.yaml，但需要重启才能生效
            logger.info("快捷键配置已更新，需要重启应用才能生效")
            
            self.tray_icon.show_message("配置已更新", "设置已保存并重新加载 ✅\n⚠️ 快捷键需重启生效")
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            self.tray_icon.show_message("配置更新失败", f"请检查配置: {str(e)}")
    
    def _toggle_clipboard(self):
        """切换剪切板监控"""
        enabled = self.clipboard_monitor.toggle()
        self.tray_icon.set_clipboard_status(enabled)
        
        status = "已开启" if enabled else "已关闭"
        self.tray_icon.show_message("剪切板监控", f"剪切板监控{status}")
    
    def _on_clipboard_toggled(self, enabled: bool):
        """剪切板监控切换事件"""
        if enabled:
            self.clipboard_monitor.start()
        else:
            self.clipboard_monitor.stop()
    
    def _on_quick_input_submitted(self, platform: str, content: str, extra_params: dict = None):
        """处理快速输入的内容"""
        extra_params = extra_params or {}
        logger.info(f"收到快速输入: 平台={platform}, 内容={content[:50]}..., 参数={extra_params}")
        
        if platform == "notion":
            # 保存到Notion
            if not self.notion_api:
                self.tray_icon.show_message("配置错误", "请先在设置界面配置Notion API")
                logger.error("Notion API未初始化")
                return
            
            self.tray_icon.show_message("处理中", "正在保存到Notion...")
            
            # 从额外参数中提取
            status = extra_params.get("status", "待处理")
            priority = extra_params.get("priority", "中")
            tags = extra_params.get("tags", [])
            
            success = self.notion_api.add_inspiration(
                content,
                priority=priority,
                status=status,
                tags=tags
            )
            
            if success:
                self.tray_icon.show_message("保存成功", "灵感已保存到Notion ✅")
                logger.info(f"快速输入已保存到Notion，优先级: {priority}, 标签: {tags}")
            else:
                self.tray_icon.show_message("保存失败", "保存到Notion失败 ❌")
                logger.error("保存到Notion失败")
                
        elif platform == "flomo":
            # 保存到Flomo
            if not self.flomo_api:
                self.tray_icon.show_message("配置错误", "请先在设置界面配置Flomo API")
                logger.error("Flomo API未初始化")
                return
            
            self.tray_icon.show_message("处理中", "正在保存到Flomo...")
            
            # 从额外参数中获取标签
            tags_str = extra_params.get("tags", "闪念")
            # 解析标签（空格分隔）
            tag_list = [tag.strip() for tag in tags_str.split() if tag.strip()]
            
            success = self.flomo_api.add_memo(content, tags=tag_list)
            
            if success:
                tags_display = ", ".join(tag_list) if tag_list else ""
                self.tray_icon.show_message("保存成功", f"已保存到Flomo ✅\n标签: {tags_display}")
                logger.info(f"快速输入已保存到Flomo，标签: {tag_list}")
            else:
                self.tray_icon.show_message("保存失败", "保存到Flomo失败 ❌")
                logger.error("保存到Flomo失败")
                
        elif platform == "ticktick":
            # 保存到滴答清单（通过邮件）
            if not self.ticktick_api:
                self.tray_icon.show_message("配置错误", "请先在设置界面配置滴答清单邮箱信息")
                logger.error("TickTick API未初始化")
                return
            
            self.tray_icon.show_message("处理中", "正在保存到滴答清单...")
            
            # 生成任务标题（取前50个字符，如果内容较长）
            title = content[:50] + "..." if len(content) > 50 else content
            
            # AI 提取时间信息（从内容中自动提取）
            time_info = None
            due_date = None
            
            if self.ai_processor:
                try:
                    # 从内容中提取时间信息
                    time_info = self.ai_processor.extract_time_info(content)
                    if time_info and time_info.get("datetime_ticktick"):
                        due_date = time_info.get("datetime_ticktick")
                        logger.info(f"识别到时间: {due_date} (原文: {content})")
                except Exception as e:
                    logger.warning(f"时间提取失败，将不设置截止时间: {e}")
            
            # 构建extra参数
            extra_dict = {}
            if due_date:
                extra_dict["due_date"] = due_date
            
            success = self.ticktick_api.add_task(
                title=title,
                content=content,
                extra=extra_dict if extra_dict else None
            )
            
            if success:
                time_display = f" (提醒: {due_date})" if due_date else ""
                self.tray_icon.show_message("保存成功", f"已保存到滴答清单 ✅{time_display}")
                logger.info(f"快速输入已保存到滴答清单，提醒时间: {due_date or '无'}")
            else:
                self.tray_icon.show_message("保存失败", "保存到滴答清单失败 ❌")
                logger.error("保存到滴答清单失败")
        else:
            logger.warning(f"未知的平台: {platform}")
    
    def _on_clipboard_content(self, content: str):
        """处理剪切板内容"""
        logger.info(f"检测到剪切板内容: {content[:50]}...")

        # 自动同步去重：一两天内重复复制的内容直接忽略（不调用AI，不同步）
        dedupe_decision = None
        try:
            if hasattr(self, "clipboard_dedupe") and self.clipboard_dedupe:
                dedupe_decision = self.clipboard_dedupe.check(content)
                if dedupe_decision.is_duplicate:
                    logger.info(
                        f"剪切板内容命中去重缓存，已忽略（age={dedupe_decision.age_seconds}s, fp={dedupe_decision.fingerprint[:8]}）"
                    )
                    return
        except Exception as e:
            logger.warning(f"剪切板去重检查失败，将继续处理: {e}")
        
        if not self.ai_processor:
            logger.warning("AI处理器未初始化，跳过剪切板内容处理")
            return
        
        try:
            # AI识别
            result = self.ai_processor.classify_content(content)
            
            if not result.get("valuable"):
                logger.info("内容不符合保存规则，已忽略")
                return
            
            target_type = result.get("type")
            
            # 根据类型分流
            if target_type == "notion":
                # 保存到Notion
                title = result.get("title")
                priority = result.get("priority", "中")
                tags = result.get("tags", [])
                
                # 强制添加标签：QuickNote_AI自动同步
                forced_tag = "QuickNote_AI自动同步"
                # 合并标签，去重，保持顺序（强制标签在前）
                all_tags = [forced_tag] + [tag for tag in tags if tag != forced_tag]
                
                success = self.notion_api.add_inspiration(
                    content,
                    title=title,
                    priority=priority,
                    tags=all_tags
                )
                
                if success:
                    self.tray_icon.show_message(
                        "已保存到Notion",
                        f"{title or content[:30]}"
                    )
                    logger.info("剪切板内容已保存到Notion")
                    # 记录去重（仅成功后）
                    try:
                        if dedupe_decision and hasattr(self, "clipboard_dedupe") and self.clipboard_dedupe:
                            self.clipboard_dedupe.mark_fingerprint(dedupe_decision.fingerprint)
                    except Exception as e:
                        logger.warning(f"写入剪切板去重缓存失败: {e}")
                
            elif target_type == "flomo" and self.flomo_api:
                # 保存到Flomo
                category = result.get("category")
                tags = result.get("tags", [])
                if category and category not in tags:
                    tags.insert(0, category)
                
                # 强制添加标签：Quick_Note_AI同步
                forced_tag = "Quick_Note_AI同步"
                if forced_tag not in tags:
                    tags.append(forced_tag)
                
                success = self.flomo_api.add_memo(content, tags=tags)
                
                if success:
                    self.tray_icon.show_message(
                        "已保存到Flomo",
                        f"{content[:30]}..."
                    )
                    logger.info("剪切板内容已保存到Flomo")
                    try:
                        if dedupe_decision and hasattr(self, "clipboard_dedupe") and self.clipboard_dedupe:
                            self.clipboard_dedupe.mark_fingerprint(dedupe_decision.fingerprint)
                    except Exception as e:
                        logger.warning(f"写入剪切板去重缓存失败: {e}")
            
            elif target_type == "ticktick" and self.ticktick_api:
                # 保存到滴答清单
                title = content[:50] + "..." if len(content) > 50 else content
                
                # 提取时间信息
                time_info = None
                due_date = None
                try:
                    time_info = self.ai_processor.extract_time_info(content)
                    if time_info and time_info.get("has_time"):
                        due_date = time_info.get("datetime_ticktick") or time_info.get("datetime")
                        logger.info(f"识别到时间: {due_date}")
                except Exception as e:
                    logger.warning(f"时间提取失败: {e}")
                
                extra_params = {}
                if due_date:
                    extra_params["due_date"] = due_date
                
                success = self.ticktick_api.add_task(
                    title=title,
                    content=content,
                    extra=extra_params if extra_params else None
                )
                
                if success:
                    self.tray_icon.show_message(
                        "已保存到滴答清单",
                        f"{content[:30]}..."
                    )
                    logger.info("剪切板内容已保存到滴答清单")
                    try:
                        if dedupe_decision and hasattr(self, "clipboard_dedupe") and self.clipboard_dedupe:
                            self.clipboard_dedupe.mark_fingerprint(dedupe_decision.fingerprint)
                    except Exception as e:
                        logger.warning(f"写入剪切板去重缓存失败: {e}")
            
        except Exception as e:
            logger.error(f"处理剪切板内容失败: {e}")
    
    def _check_and_heal_hotkey(self):
        """【自愈机制】检查快捷键状态，必要时重启"""
        try:
            # 获取快捷键监听器状态
            status = self.hotkey_listener.get_status()
            
            # 检查是否需要重启
            need_restart = False
            
            # 1. 监听器不存活
            if not status.get('listener_alive', False):
                logger.warning("快捷键监听器不存活，准备重启")
                need_restart = True
            
            # 2. 监听器未运行
            elif not status.get('is_running', False):
                logger.warning("快捷键监听器未运行，准备重启")
                need_restart = True
            
            # 3. 检查是否长时间未响应（超过5分钟没有活动可能异常）
            elif status.get('last_activity_seconds_ago') is not None:
                if status['last_activity_seconds_ago'] > 300:  # 5分钟
                    # 避免频繁重启：检查上次重启时间
                    import time
                    if not hasattr(self, '_last_heal_time'):
                        self._last_heal_time = 0
                    
                    if time.time() - self._last_heal_time > 120:  # 至少间隔2分钟
                        logger.warning(f"快捷键监听器长时间无活动 ({status['last_activity_seconds_ago']}秒)，准备重启")
                        need_restart = True
            
            # 执行重启
            if need_restart:
                import time
                self._last_heal_time = time.time()
                logger.info("【自愈】触发快捷键重启")
                self._restart_hotkey_listener_internal()
            else:
                logger.debug(f"【自愈】快捷键状态正常，无需重启 (alive={status.get('listener_alive')}, running={status.get('is_running')})")
                
        except Exception as e:
            logger.error(f"快捷键自愈检查失败: {e}")
    
    def _restart_hotkey_listener(self):
        """手动重启快捷键监听器（从托盘菜单调用）"""
        logger.info("用户手动触发快捷键重启")
        self._restart_hotkey_listener_internal()
    
    def _restart_hotkey_listener_internal(self):
        """内部方法：重启快捷键监听器"""
        try:
            logger.info("正在重启快捷键监听器...")
            
            # 停止当前监听器
            if self.hotkey_listener:
                self.hotkey_listener.stop()
                import time
                time.sleep(0.3)  # 等待完全停止
            
            # 重新注册快捷键
            self.hotkey_listener.register(
                config.hotkey_quick_input,
                lambda: self.show_quick_input_signal.emit()
            )
            self.hotkey_listener.register(
                config.hotkey_toggle_clipboard,
                lambda: self.toggle_clipboard_signal.emit()
            )
            
            # 重新启动
            self.hotkey_listener.start()
            
            logger.info("快捷键监听器已重启")
            
        except Exception as e:
            logger.error(f"重启快捷键监听器失败: {e}", exc_info=True)
    
    def _restart_app(self):
        """重启应用"""
        import subprocess
        import os
        import sys
        from pathlib import Path
        
        logger.info("正在重启应用...")
        
        # 停止所有服务
        try:
            self.clipboard_monitor.stop()
            self.hotkey_listener.stop()
        except:
            pass
        
        # 显示重启提示
        self.tray_icon.show_message("正在重启", "QuickNote AI 正在重启...")
        
        # 导入QTimer
        from PyQt5.QtCore import QTimer
        
        # 判断是打包后的EXE还是开发模式
        if getattr(sys, 'frozen', False):
            # 打包后的EXE模式
            exe_path = sys.executable  # EXE的完整路径
            exe_dir = Path(exe_path).parent
            
            logger.info(f"EXE模式重启，路径: {exe_path}")
            
            # 延迟启动新进程
            QTimer.singleShot(300, lambda: self._do_restart_exe(exe_path, exe_dir))
        else:
            # 开发模式（Python脚本）
            current_dir = Path(__file__).parent.parent
            script_path = current_dir / "src" / "main.py"
            python_exe = sys.executable
            
            logger.info(f"开发模式重启，脚本: {script_path}")
            
            # 延迟启动新进程
            QTimer.singleShot(300, lambda: self._do_restart_script(python_exe, script_path, current_dir))
        
        # 退出当前应用
        QTimer.singleShot(500, lambda: self.app.quit())
    
    def _do_restart_exe(self, exe_path, exe_dir):
        """执行EXE重启操作"""
        import subprocess
        import os
        
        try:
            # 启动新的EXE进程
            subprocess.Popen(
                [str(exe_path)],
                cwd=str(exe_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
                shell=False
            )
            logger.info("新EXE进程已启动")
        except Exception as e:
            logger.error(f"重启EXE失败: {e}", exc_info=True)
            self.tray_icon.show_message("重启失败", f"无法启动新进程: {str(e)}")
    
    def _do_restart_script(self, python_exe, script_path, current_dir):
        """执行脚本重启操作（开发模式）"""
        import subprocess
        import os
        
        try:
            # 切换到项目目录
            os.chdir(str(current_dir))
            
            # 启动新进程
            subprocess.Popen(
                [python_exe, str(script_path)],
                cwd=str(current_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            logger.info("新Python进程已启动")
        except Exception as e:
            logger.error(f"重启脚本失败: {e}", exc_info=True)
    
    def _quit_app(self):
        """退出应用"""
        logger.info("正在退出应用...")
        
        # 停止所有服务
        self.clipboard_monitor.stop()
        self.hotkey_listener.stop()
        
        # 退出应用
        self.app.quit()
        
        logger.info("应用已退出")


def main():
    """主函数"""
    # 设置高DPI支持（在创建QApplication之前）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("QuickNote AI")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出
    
    try:
        # 创建主应用实例
        quick_note = QuickNoteApp(app)
        
        # 显示启动成功提示
        quick_note.tray_icon.show_message(
            "QuickNote AI",
            "已启动！使用 Ctrl+Shift+Space 快速输入"
        )
        
        # 运行应用
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"应用运行异常: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "运行错误",
            f"应用运行时发生错误：\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

