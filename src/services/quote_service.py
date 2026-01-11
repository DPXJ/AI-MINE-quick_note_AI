"""AI金句服务"""
import os
import json
import random
import threading
from typing import Dict, Optional, List
from loguru import logger
import requests
import yaml


class QuoteService:
    """AI金句服务"""
    
    def __init__(self):
        """初始化金句服务"""
        self.config = self._load_config()
        
        # 使用现有的DeepSeek/OpenAI配置
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "deepseek-chat")
        
        # 金句生成的prompt
        self.prompt = self.config.get("prompt", "")
        
        # 本地金句缓存（用于上一条/下一条导航）
        self.quotes_history: List[Dict] = []
        self.current_index = -1
        
        # 预加载机制（提升"下一条"速度）
        self._preloaded_quote: Optional[Dict] = None
        self._is_preloading = False
        self._preload_lock = threading.Lock()
        
        # 备用金句（当API调用失败时使用）
        self.fallback_quotes = [
            # 人生智慧
            {
                "quote": "我们无法选择生命中的卡牌，但可以决定如何出牌。",
                "author": "兰迪·鲍许",
                "category": "人生智慧"
            },
            {
                "quote": "优秀是一种习惯，卓越是一种选择。",
                "author": "亚里士多德",
                "category": "人生智慧"
            },
            # 哲学
            {
                "quote": "真正的知识不在于知道答案，而在于知道如何提出正确的问题。",
                "author": "爱因斯坦",
                "category": "哲学"
            },
            {
                "quote": "最难的不是做出选择，而是为选择负责。",
                "author": "让-保罗·萨特",
                "category": "哲学"
            },
            # AI与科技
            {
                "quote": "在AI时代，无法被算法量化的'决策力'和'审美力'，才是人类最后的护城河。",
                "author": "凯文·凯利",
                "category": "AI科技"
            },
            {
                "quote": "AI不会取代人类，但会取代那些不会使用AI的人。",
                "author": "吴恩达",
                "category": "AI科技"
            },
            {
                "quote": "技术的终极意义，是让人类从重复劳动中解放，去做更有创造性的事。",
                "author": "雷·库兹韦尔",
                "category": "AI科技"
            },
            {
                "quote": "算法可以优化效率，但无法替代人类的同理心和判断力。",
                "author": "李开复",
                "category": "AI科技"
            },
            # 产品经理
            {
                "quote": "用户不是想要更快的马，而是想要更快到达目的地。",
                "author": "亨利·福特",
                "category": "产品思维"
            },
            {
                "quote": "产品的本质是解决问题，而不是堆砌功能。",
                "author": "俞军",
                "category": "产品思维"
            },
            {
                "quote": "好的设计是尽可能少的设计，好的产品是用户感知不到设计的存在。",
                "author": "迪特·拉姆斯",
                "category": "产品设计"
            },
            {
                "quote": "做产品最重要的是理解用户的真实需求，而不是他们说的需求。",
                "author": "张小龙",
                "category": "产品思维"
            },
            # 商业
            {
                "quote": "复利的本质不是金钱，而是时间和认知的叠加效应。",
                "author": "查理·芒格",
                "category": "商业"
            },
            # 历史
            {
                "quote": "人类从历史中学到的唯一教训，就是人类无法从历史中学到任何教训。",
                "author": "黑格尔",
                "category": "历史"
            },
            # 心理学
            {
                "quote": "信息过载时代，稀缺的不是信息，而是注意力和判断力。",
                "author": "赫伯特·西蒙",
                "category": "心理学"
            },
            # 古诗词与诗歌
            {
                "quote": "天行健，君子以自强不息；地势坤，君子以厚德载物。",
                "author": "《周易》",
                "category": "古诗词"
            },
            {
                "quote": "路漫漫其修远兮，吾将上下而求索。",
                "author": "屈原《离骚》",
                "category": "古诗词"
            },
            {
                "quote": "宝剑锋从磨砺出，梅花香自苦寒来。",
                "author": "冯梦龙《警世通言》",
                "category": "古诗词"
            },
            {
                "quote": "长风破浪会有时，直挂云帆济沧海。",
                "author": "李白《行路难》",
                "category": "古诗词"
            },
            {
                "quote": "穷且益坚，不坠青云之志。",
                "author": "王勃《滕王阁序》",
                "category": "古诗词"
            },
            {
                "quote": "纸上得来终觉浅，绝知此事要躬行。",
                "author": "陆游《冬夜读书示子聿》",
                "category": "古诗词"
            },
            {
                "quote": "博观而约取，厚积而薄发。",
                "author": "苏轼",
                "category": "古诗词"
            },
        ]
        
        logger.info(f"金句服务已初始化 (API: {self.base_url}, Model: {self.model})")
    
    def _load_config(self) -> Dict:
        """加载配置"""
        try:
            with open("config.yaml", "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                meditation_config = config.get("meditation_quotes", {})
                return meditation_config
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
                    # 触发预加载
                    self._trigger_preload()
                    return quote
        except Exception as e:
            logger.error(f"AI生成金句失败: {e}")
        
        # 使用备用金句
        quote = random.choice(self.fallback_quotes)
        self._add_to_history(quote)
        logger.info(f"使用备用金句: {quote['quote'][:20]}...")
        # 触发预加载
        self._trigger_preload()
        return quote
    
    def _fetch_quote_from_ai(self) -> Optional[Dict[str, str]]:
        """从AI API获取金句"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 构建提示词，包含最近的金句以避免重复
            prompt_with_history = self.prompt
            if len(self.quotes_history) > 0:
                recent_quotes = [q["quote"] for q in self.quotes_history[-5:]]  # 最近5条
                history_text = "\n- ".join(recent_quotes)
                prompt_with_history += f"\n\n⚠️ 请避免重复以下最近生成的金句：\n- {history_text}"
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt_with_history}
                ],
                "temperature": 1.0,  # 提高创造性，增加多样性
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
            result = self.quotes_history[self.current_index]
            # 向前浏览时也触发预加载（为后续"下一条"做准备）
            self._trigger_preload()
            return result
        else:
            # 已经是第一条
            return self.quotes_history[0]
    
    def get_next_quote(self) -> Optional[Dict[str, str]]:
        """获取下一条金句（优化：使用预加载）"""
        if not self.quotes_history:
            result = self.get_random_quote()
            self._trigger_preload()  # 立即触发预加载
            return result
        
        if self.current_index < len(self.quotes_history) - 1:
            # 历史记录中还有下一条
            self.current_index += 1
            result = self.quotes_history[self.current_index]
            logger.debug(f"从历史记录获取金句 (索引: {self.current_index}/{len(self.quotes_history)-1})")
            # 触发预加载（如果接近末尾）
            self._trigger_preload()
            return result
        else:
            # 已经是最后一条，尝试使用预加载的金句
            with self._preload_lock:
                if self._preloaded_quote:
                    quote = self._preloaded_quote
                    self._preloaded_quote = None  # 清空预加载
                    self._add_to_history(quote)
                    logger.info("✨ 使用预加载的金句（瞬间响应）")
                    # 触发新的预加载
                    self._trigger_preload()
                    return quote
            
            # 没有预加载，同步生成新的
            logger.warning("预加载未就绪，同步生成金句（可能稍慢）")
            quote = self.get_random_quote()
            # 触发预加载
            self._trigger_preload()
            return quote
    
    def _trigger_preload(self):
        """触发后台预加载（提前预加载，提升响应速度）"""
        # 如果当前是最后一条或接近末尾（倒数3条内），且没有在预加载，就启动预加载
        # 如果没有预加载的金句，也会触发预加载
        if (self.current_index >= len(self.quotes_history) - 3 and 
            not self._is_preloading and 
            not self._preloaded_quote and
            self.api_key):
            
            def preload_worker():
                try:
                    with self._preload_lock:
                        if self._is_preloading:
                            return
                        self._is_preloading = True
                    
                    logger.debug("后台预加载下一条金句...")
                    quote = self._fetch_quote_from_ai()
                    
                    with self._preload_lock:
                        if quote:
                            self._preloaded_quote = quote
                            logger.info("预加载金句成功（准备就绪）✨")
                        self._is_preloading = False
                except Exception as e:
                    logger.error(f"预加载金句失败: {e}")
                    with self._preload_lock:
                        self._is_preloading = False
            
            # 启动后台线程
            threading.Thread(target=preload_worker, daemon=True).start()
    
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
