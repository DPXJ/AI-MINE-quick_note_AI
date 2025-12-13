"""AI内容处理器"""
import json
from typing import Dict, Any, Optional
from loguru import logger


class AIProcessor:
    """AI内容处理器"""
    
    def __init__(self, provider: str = "openai"):
        """
        初始化AI处理器
        
        Args:
            provider: AI提供商（openai/deepseek/claude）
        """
        self.provider = provider
        self.client = None
        
        if provider in ["openai", "deepseek"]:
            # DeepSeek使用和OpenAI兼容的API格式
            self._init_openai()
        elif provider == "claude":
            self._init_claude()
        else:
            raise ValueError(f"不支持的AI提供商: {provider}，支持: openai/deepseek/claude")
    
    def _init_openai(self):
        """初始化OpenAI/DeepSeek客户端"""
        try:
            from openai import OpenAI
            from src.utils.config import config
            
            provider = config.ai_provider
            self.client = OpenAI(
                api_key=config.openai_api_key,
                base_url=config.openai_base_url
            )
            self.model = config.openai_model
            provider_name = "DeepSeek" if provider == "deepseek" else "OpenAI"
            logger.info(f"{provider_name}客户端已初始化，模型: {self.model}, Base URL: {config.openai_base_url}")
        except Exception as e:
            logger.error(f"AI客户端初始化失败: {e}")
            raise
    
    def _init_claude(self):
        """初始化Claude客户端"""
        try:
            from anthropic import Anthropic
            from src.utils.config import config
            
            self.client = Anthropic(api_key=config.anthropic_api_key)
            self.model = "claude-3-haiku-20240307"
            logger.info(f"Claude客户端已初始化，模型: {self.model}")
        except Exception as e:
            logger.error(f"Claude初始化失败: {e}")
            raise
    
    def analyze_content(
        self, 
        content: str, 
        prompt_template: str
    ) -> Optional[Dict[str, Any]]:
        """
        分析内容
        
        Args:
            content: 待分析内容
            prompt_template: 提示词模板（包含{content}占位符）
            
        Returns:
            分析结果（JSON格式）
        """
        try:
            # 构建提示词
            prompt = prompt_template.format(content=content)
            
            # 调用AI（OpenAI和DeepSeek使用相同的API格式）
            if self.provider in ["openai", "deepseek"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的内容分类助手，请严格按照JSON格式返回结果。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                result_text = response.choices[0].message.content
                
            elif self.provider == "claude":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                result_text = response.content[0].text
            
            # 解析JSON
            result = json.loads(result_text)
            logger.info(f"AI分析完成: {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"AI返回的不是有效的JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return None
    
    def classify_content(self, content: str) -> Dict[str, Any]:
        """
        智能分类内容
        
        Args:
            content: 待分类内容
            
        Returns:
            分类结果
        """
        from src.utils.config import config
        
        # 先尝试Flomo规则
        flomo_prompt = config.get("ai_rules.flomo.prompt", "")
        if flomo_prompt:
            result = self.analyze_content(content, flomo_prompt)
            if result and result.get("valuable") and result.get("type") == "flomo":
                return result
        
        # 再尝试Notion规则
        notion_prompt = config.get("ai_rules.notion.prompt", "")
        if notion_prompt:
            result = self.analyze_content(content, notion_prompt)
            if result and result.get("valuable") and result.get("type") == "notion":
                return result
        
        # 都不符合
        return {"valuable": False, "type": None}

