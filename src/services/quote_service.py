"""AI金句服务"""
import os
import json
import random
from typing import Dict, Optional, List
from loguru import logger
import requests
import yaml


class QuoteService:
    """AI金句服务"""
    
    def __init__(self):
        """初始化金句服务"""
        self.config = self._load_config()
        self.api_key = os.getenv("SILICON_API_KEY", "")
        self.base_url = self.config.get("base_url", "https://api.siliconflow.cn/v1")
        self.model = self.config.get("model", "Qwen/Qwen2.5-7B-Instruct")
        self.prompt = self.config.get("prompt", "")
        
        # 本地金句缓存（用于上一条/下一条导航）
        self.quotes_history: List[Dict] = []
        self.current_index = -1
        
        # 备用金句（当API调用失败时使用）
        self.fallback_quotes = [
            {
                "quote": "我们无法选择生命中的卡牌，但可以决定如何出牌。",
                "author": "兰迪·鲍许",
                "category": "人生智慧"
            },
            {
                "quote": "真正的知识不在于知道答案，而在于知道如何提出正确的问题。",
                "author": "爱因斯坦",
                "category": "哲学"
            },
            {
                "quote": "在AI时代，无法被算法量化的'决策力'和'审美力'，才是人类最后的护城河。",
                "author": "凯文·凯利",
                "category": "科技"
            },
            {
                "quote": "复利的本质不是金钱，而是时间和认知的叠加效应。",
                "author": "查理·芒格",
                "category": "商业"
            },
            {
                "quote": "人类从历史中学到的唯一教训，就是人类无法从历史中学到任何教训。",
                "author": "黑格尔",
                "category": "历史"
            },
            {
                "quote": "最难的不是做出选择，而是为选择负责。",
                "author": "让-保罗·萨特",
                "category": "哲学"
            },
            {
                "quote": "信息过载时代，稀缺的不是信息，而是注意力和判断力。",
                "author": "赫伯特·西蒙",
                "category": "心理学"
            },
            {
                "quote": "优秀是一种习惯，卓越是一种选择。",
                "author": "亚里士多德",
                "category": "人生智慧"
            },
        ]
        
        logger.info(f"金句服务已初始化 (API: {self.base_url}, Model: {self.model})")
    
    def _load_config(self) -> Dict:
        """加载配置"""
        try:
            with open("config.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                meditation_config = config.get("meditation_quotes", {})
                return meditation_config.get("api", {})
        except Exception as e:
            logger.error(f"加载金句配置失败: {e}")
            return {}
    
    def get_random_quote(self) -> Dict[str, str]:
        """获取随机金句（优先从AI生成，失败则使用备用）"""
        try:
            if self.api_key:
                quote = self._fetch_quote_from_ai()
                if quote:
                    self._add_to_history(quote)
                    return quote
        except Exception as e:
            logger.error(f"AI生成金句失败: {e}")
        
        # 使用备用金句
        quote = random.choice(self.fallback_quotes)
        self._add_to_history(quote)
        logger.info(f"使用备用金句: {quote['quote'][:20]}...")
        return quote
    
    def _fetch_quote_from_ai(self) -> Optional[Dict[str, str]]:
        """从AI API获取金句"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": self.prompt}
                ],
                "temperature": 0.9,  # 提高创造性
                "max_tokens": 500,
                "stream": False
            }
            
            logger.debug(f"请求AI生成金句: {self.base_url}/chat/completions")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                
                # 提取JSON（有些模型会返回```json...```格式）
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                # 解析JSON
                quote_data = json.loads(content)
                
                # 验证必需字段
                if "quote" in quote_data and "author" in quote_data:
                    logger.info(f"AI生成金句成功: {quote_data['quote'][:30]}...")
                    return {
                        "quote": quote_data["quote"],
                        "author": quote_data.get("author", "佚名"),
                        "category": quote_data.get("category", "智慧")
                    }
            else:
                logger.warning(f"AI API返回错误: {response.status_code} - {response.text}")
        except json.JSONDecodeError as e:
            logger.error(f"解析AI返回的JSON失败: {e}, 内容: {content[:100] if 'content' in locals() else 'N/A'}")
        except Exception as e:
            logger.error(f"调用AI API异常: {e}", exc_info=True)
        
        return None
    
    def _add_to_history(self, quote: Dict):
        """添加到历史记录"""
        # 避免重复
        if not self.quotes_history or self.quotes_history[-1] != quote:
            self.quotes_history.append(quote)
            self.current_index = len(self.quotes_history) - 1
            
            # 限制历史记录数量
            if len(self.quotes_history) > 100:
                self.quotes_history.pop(0)
                self.current_index -= 1
    
    def get_previous_quote(self) -> Optional[Dict[str, str]]:
        """获取上一条金句"""
        if not self.quotes_history:
            return self.get_random_quote()
        
        if self.current_index > 0:
            self.current_index -= 1
            return self.quotes_history[self.current_index]
        else:
            # 已经是第一条
            return self.quotes_history[0]
    
    def get_next_quote(self) -> Optional[Dict[str, str]]:
        """获取下一条金句"""
        if not self.quotes_history:
            return self.get_random_quote()
        
        if self.current_index < len(self.quotes_history) - 1:
            self.current_index += 1
            return self.quotes_history[self.current_index]
        else:
            # 已经是最后一条，生成新的
            return self.get_random_quote()
    
    def get_current_quote(self) -> Optional[Dict[str, str]]:
        """获取当前金句"""
        if self.quotes_history and 0 <= self.current_index < len(self.quotes_history):
            return self.quotes_history[self.current_index]
        return None
    
    def get_quote_text(self, quote: Optional[Dict] = None) -> str:
        """获取金句完整文本（用于复制）"""
        if not quote:
            quote = self.get_current_quote()
        if not quote:
            return ""
        
        return f"{quote['quote']}\n\n—— {quote['author']} · {quote.get('category', '')}"
