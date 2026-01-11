"""配置管理模块"""
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
from loguru import logger


class Config:
    """配置管理类"""
    
    def __init__(self):
        # 获取项目根目录
        # 如果是打包后的EXE，使用EXE所在目录；否则使用项目根目录
        if getattr(sys, 'frozen', False):
            # 打包后的EXE模式：使用EXE所在目录
            self.root_dir = Path(sys.executable).parent
        else:
            # 开发模式：使用项目根目录
            self.root_dir = Path(__file__).parent.parent.parent
        
        self.config_file = self.root_dir / "config.yaml"
        self.env_file = self.root_dir / ".env"
        
        # 加载环境变量
        if self.env_file.exists():
            load_dotenv(self.env_file)
            logger.info("已加载环境变量")
        else:
            logger.warning(f".env文件不存在: {self.env_file}")
        
        # 加载配置文件
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载YAML配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info("配置文件加载成功")
                return config
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            return {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（支持点号路径）"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def get_env(self, key: str, default: str = "") -> str:
        """获取环境变量"""
        return os.getenv(key, default)
    
    @property
    def openai_api_key(self) -> str:
        """OpenAI/DeepSeek API Key"""
        return self.get_env("OPENAI_API_KEY")
    
    @property
    def openai_base_url(self) -> str:
        """OpenAI/DeepSeek Base URL"""
        # 如果provider是deepseek，使用DeepSeek的URL，否则使用配置的值或默认OpenAI
        provider = self.ai_provider
        if provider == "deepseek":
            return self.get_env("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
        return self.get_env("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    @property
    def openai_model(self) -> str:
        """OpenAI/DeepSeek Model"""
        # 根据provider返回对应的默认模型
        provider = self.ai_provider
        if provider == "deepseek":
            return self.get_env("OPENAI_MODEL", "deepseek-chat")
        return self.get_env("OPENAI_MODEL", "gpt-4o-mini")
    
    @property
    def anthropic_api_key(self) -> str:
        """Anthropic API Key"""
        return self.get_env("ANTHROPIC_API_KEY")
    
    @property
    def ai_provider(self) -> str:
        """AI提供商（openai/deepseek/claude）"""
        return self.get_env("AI_PROVIDER", "deepseek")  # 默认改为deepseek
    
    @property
    def notion_api_key(self) -> str:
        """Notion API Key"""
        return self.get_env("NOTION_API_KEY")
    
    @property
    def notion_database_id(self) -> str:
        """Notion Database ID"""
        return self.get_env("NOTION_DATABASE_ID")
    
    @property
    def flomo_api_url(self) -> str:
        """Flomo Webhook URL"""
        return self.get_env("FLOMO_API_URL")
    
    @property
    def ticktick_smtp_host(self) -> str:
        """TickTick 邮件发送 - SMTP服务器地址"""
        return self.get_env("TICKTICK_SMTP_HOST", "smtp.qq.com")
    
    @property
    def ticktick_smtp_port(self) -> int:
        """TickTick 邮件发送 - SMTP端口"""
        port_str = self.get_env("TICKTICK_SMTP_PORT", "465")
        try:
            return int(port_str)
        except ValueError:
            return 465
    
    @property
    def ticktick_smtp_user(self) -> str:
        """TickTick 邮件发送 - 发件邮箱地址"""
        return self.get_env("TICKTICK_SMTP_USER")
    
    @property
    def ticktick_smtp_pass(self) -> str:
        """TickTick 邮件发送 - SMTP授权码"""
        return self.get_env("TICKTICK_SMTP_PASS")
    
    @property
    def ticktick_email(self) -> str:
        """TickTick 专属邮箱地址（格式：todo+xxxxx@mail.dida365.com）"""
        return self.get_env("TICKTICK_EMAIL")
    
    @property
    def hotkey_quick_input(self) -> str:
        """快速输入快捷键"""
        return self.get("hotkeys.quick_input", "ctrl+shift+space")
    
    @property
    def hotkey_toggle_clipboard(self) -> str:
        """切换剪切板监控快捷键"""
        return self.get("hotkeys.toggle_clipboard", "ctrl+shift+c")
    
    @property
    def clipboard_enabled(self) -> bool:
        """剪切板监控是否启用"""
        return self.get("clipboard.enabled", True)
    
    @property
    def clipboard_check_interval(self) -> float:
        """剪切板检查间隔"""
        return self.get("clipboard.check_interval", 1.0)
    
    @property
    def clipboard_min_length(self) -> int:
        """剪切板内容最小长度"""
        return self.get("clipboard.min_length", 10)
    
    @property
    def clipboard_max_length(self) -> int:
        """剪切板内容最大长度"""
        return self.get("clipboard.max_length", 5000)
    
    def validate(self) -> bool:
        """验证配置是否完整"""
        errors = []
        
        # 检查AI配置
        provider = self.ai_provider
        if provider in ["openai", "deepseek"]:
            if not self.openai_api_key:
                errors.append(f"未配置OPENAI_API_KEY（用于{provider}）")
        elif provider == "claude":
            if not self.anthropic_api_key:
                errors.append("未配置ANTHROPIC_API_KEY")
        else:
            errors.append(f"不支持的AI提供商: {provider}，支持: openai/deepseek/claude")
        
        # 检查Notion配置
        if not self.notion_api_key:
            errors.append("未配置NOTION_API_KEY")
        if not self.notion_database_id:
            errors.append("未配置NOTION_DATABASE_ID")
        
        # 检查Flomo配置（可选）
        if not self.flomo_api_url:
            logger.warning("未配置FLOMO_API_URL，Flomo功能将不可用")
        
        # 检查TickTick配置（可选）
        ticktick_configured = (
            self.ticktick_smtp_user and
            self.ticktick_smtp_pass and
            self.ticktick_email
        )
        if not ticktick_configured:
            logger.warning("未配置TickTick邮箱信息，滴答清单功能将不可用（需要：TICKTICK_SMTP_USER, TICKTICK_SMTP_PASS, TICKTICK_EMAIL）")
        
        if errors:
            for error in errors:
                logger.error(error)
            return False
        
        logger.info("配置验证通过")
        return True


# 全局配置实例
config = Config()

