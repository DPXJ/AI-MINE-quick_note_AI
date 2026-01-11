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
            # 构建提示词（用户提示词可能不包含{content}，需要添加）
            if "{content}" in prompt_template:
                prompt = prompt_template.format(content=content)
            else:
                # 如果提示词中没有{content}，自动添加
                prompt = prompt_template + f"\n\n待分析内容：\n{content}"
            
            # 自动添加JSON格式要求（用户提示词中不包含这些技术细节）
            json_instruction = """

请以JSON格式返回结果：
- 如果内容符合条件，返回：{"valuable": true, "type": "flomo"或"notion"或"ticktick", "category": "分类", "tags": ["标签1", "标签2"], "title": "简短标题（25字内）", "priority": "高/中/低"}
- 如果内容不符合条件，返回：{"valuable": false}
- tags字段必须返回，用于标记内容的关键分类（如"会议"、"产品"、"评审"等）
- title字段是对内容的精炼总结，不超过25个字符"""
            
            prompt = prompt + json_instruction
            
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
        
        # 检查是否启用自动同步
        clipboard_monitor_enabled = config.get("ai_rules.clipboard_monitor", True)
        if not clipboard_monitor_enabled:
            logger.debug("剪切板监控已禁用")
            return {"valuable": False, "type": None}
        
        # 1️⃣ 优先尝试滴答清单规则（如果启用且包含时间信息）
        ticktick_enabled = config.get("ai_rules.ticktick.enabled", True)
        if ticktick_enabled:
            # 先快速检查是否有时间相关关键词
            time_keywords = ["明天", "今天", "后天", "下周", "点", "时", "上午", "下午", "晚上", "会议", "评审", "开会"]
            has_time_keyword = any(keyword in content for keyword in time_keywords)
            
            if has_time_keyword:
<<<<<<< HEAD
                ticktick_prompt = config.get("ai_rules.ticktick.prompt", "")
                if ticktick_prompt:
                    # 添加类型标识和标签提取要求
                    ticktick_prompt_with_type = ticktick_prompt + "\n\n如果符合条件，返回的type必须是\"ticktick\"，并且需要提取tags（任务标签，如['会议', '产品评审']）。"
                    result = self.analyze_content(content, ticktick_prompt_with_type)
                    if result and result.get("valuable") and result.get("type") == "ticktick":
                        logger.info(f"AI分类结果：TickTick - {result}")
                        return result
=======
                # 【严格预检查】在调用AI前先过滤明显不符合的内容
                content_length = len(content)
                
                # 🚫 拦截规则1：长度超过100字，直接拒绝
                if content_length > 100:
                    logger.debug(f"滴答清单预检查：内容过长({content_length}字)，已拒绝")
                    # 不调用AI，继续检查其他规则
                else:
                    # 🚫 拦截规则2：包含结构化文档特征（Markdown标题、提示词模板）
                    structure_keywords = ["# Role:", "## Background", "## Goals", "## Workflow", 
                                        "## Skills", "## Constraints", "## Output", "## Example",
                                        "## Initialization", "### ", "**Input", "**Output"]
                    has_structure = any(keyword in content for keyword in structure_keywords)
                    
                    if has_structure:
                        logger.debug(f"滴答清单预检查：包含结构化文档特征，已拒绝")
                        # 不调用AI，继续检查其他规则
                    else:
                        # 通过预检查，调用AI进行详细分析
                        ticktick_prompt = config.get("ai_rules.ticktick.prompt", "")
                        if ticktick_prompt:
                            # 添加类型标识和标签提取要求
                            ticktick_prompt_with_type = ticktick_prompt + "\n\n如果符合条件，返回的type必须是\"ticktick\"，并且需要提取tags（任务标签，如['会议', '产品评审']）。"
                            result = self.analyze_content(content, ticktick_prompt_with_type)
                            if result and result.get("valuable") and result.get("type") == "ticktick":
                                logger.info(f"AI分类结果：TickTick - {result}")
                                return result
>>>>>>> eb855f52a4ab5168a598f63b5d06f0e2d8ae5db3
        
        # 2️⃣ 再尝试Flomo规则（如果启用）
        flomo_enabled = config.get("ai_rules.flomo.enabled", True)
        if flomo_enabled:
<<<<<<< HEAD
            flomo_prompt = config.get("ai_rules.flomo.prompt", "")
            if flomo_prompt:
                # 添加类型标识
                flomo_prompt_with_type = flomo_prompt + "\n\n如果符合条件，返回的type必须是\"flomo\"。"
                result = self.analyze_content(content, flomo_prompt_with_type)
                if result and result.get("valuable") and result.get("type") == "flomo":
                    logger.info(f"AI分类结果：Flomo - {result}")
                    return result
=======
            # 【严格预检查】过滤明显不符合的内容（提升性能）
            content_length = len(content)
            
            # Flomo笔记特点：绝大多数100字以下，个别段落450字以下，一般不超过500字
            # 超过500字的内容基本都是文章/长文，不适合作为单条笔记
            if content_length > 500:
                logger.debug(f"Flomo预检查：内容过长({content_length}字)，已拒绝（建议500字以内）")
            else:
                # 检查是否为操作手册、教程类（这类内容Flomo明确拒绝）
                tutorial_keywords = ["操作步骤", "使用方法", "配置指南", "安装教程", "第一步", "第二步", "第三步"]
                is_tutorial = any(keyword in content for keyword in tutorial_keywords)
                
                if is_tutorial:
                    logger.debug(f"Flomo预检查：教程类内容，已拒绝")
                else:
                    flomo_prompt = config.get("ai_rules.flomo.prompt", "")
                    if flomo_prompt:
                        # 添加类型标识
                        flomo_prompt_with_type = flomo_prompt + "\n\n如果符合条件，返回的type必须是\"flomo\"。"
                        result = self.analyze_content(content, flomo_prompt_with_type)
                        if result and result.get("valuable") and result.get("type") == "flomo":
                            logger.info(f"AI分类结果：Flomo - {result}")
                            return result
>>>>>>> eb855f52a4ab5168a598f63b5d06f0e2d8ae5db3
        
        # 3️⃣ 最后尝试Notion规则（如果启用）
        notion_enabled = config.get("ai_rules.notion.enabled", True)
        if notion_enabled:
<<<<<<< HEAD
            notion_prompt = config.get("ai_rules.notion.prompt", "")
            if notion_prompt:
                # 添加类型标识和标签提取要求
                notion_prompt_with_type = notion_prompt + "\n\n如果符合条件，返回的type必须是\"notion\"，并且需要提取tags（标签，如['产品', '待办']）。"
                result = self.analyze_content(content, notion_prompt_with_type)
                if result and result.get("valuable") and result.get("type") == "notion":
                    logger.info(f"AI分类结果：Notion - {result}")
                    return result
=======
            # 【预检查】过滤明显不符合的内容
            content_length = len(content)
            
            # Notion主要用于任务和灵感，通常不会太长
            if content_length > 1000:
                logger.debug(f"Notion预检查：内容过长({content_length}字)，已拒绝")
            else:
                notion_prompt = config.get("ai_rules.notion.prompt", "")
                if notion_prompt:
                    # 添加类型标识和标签提取要求
                    notion_prompt_with_type = notion_prompt + "\n\n如果符合条件，返回的type必须是\"notion\"，并且需要提取tags（标签，如['产品', '待办']）。"
                    result = self.analyze_content(content, notion_prompt_with_type)
                    if result and result.get("valuable") and result.get("type") == "notion":
                        logger.info(f"AI分类结果：Notion - {result}")
                        return result
>>>>>>> eb855f52a4ab5168a598f63b5d06f0e2d8ae5db3
        
        # 都不符合
        return {"valuable": False, "type": None}
    
    def extract_time_info(self, content: str) -> Optional[Dict[str, Any]]:
        """
        从文本中提取时间信息
        
        Args:
            content: 待分析的文本
            
        Returns:
            包含时间信息的字典，如 {"has_time": true, "datetime": "2025-12-16 07:30", "original": "明天上午7点半"}
            如果没有时间信息，返回 {"has_time": false}
        """
        try:
            from datetime import datetime, timezone, timedelta
            
            # 获取当前时间（东八区 UTC+8）
            tz_cn = timezone(timedelta(hours=8))
            current_time = datetime.now(tz_cn)
            current_str = current_time.strftime("%Y-%m-%d %H:%M")
            current_weekday = current_time.strftime("%A")  # Monday, Tuesday, etc.
            
            prompt = f"""你是一个时间提取助手。请从以下文本中提取时间信息，并转换为标准格式。

文本：{content}

当前时间：{current_str}（{current_weekday}，东八区时间）

请以JSON格式返回：
- 如果包含时间信息：{{"has_time": true, "datetime": "YYYY-MM-DD HH:MM", "original_text": "原文中的时间描述"}}
- 如果没有时间信息：{{"has_time": false}}

注意：
1. 请基于当前时间准确计算相对时间（明天、后天、下周一等）
2. 时间格式统一为 24 小时制
3. 如果只有日期没有具体时间，默认设为 09:00
4. "上午7点半" = 07:30, "下午3点" = 15:00
5. "晚上8点" = 20:00"""

            if self.provider in ["openai", "deepseek"]:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的时间信息提取助手，请严格按照JSON格式返回结果。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                result_text = response.choices[0].message.content
                
            elif self.provider == "claude":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=512,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                result_text = response.content[0].text
            
            result = json.loads(result_text)
            
            # 如果识别到时间，转换为滴答清单需要的格式
            if result.get("has_time") and result.get("datetime"):
                try:
                    dt_str = result.get("datetime")
                    # 解析 AI 返回的时间（格式: YYYY-MM-DD HH:MM）
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                    # 转换为滴答清单需要的格式（带时区）
                    ticktick_format = dt.strftime("%Y-%m-%dT%H:%M:%S") + "+0800"
                    result["datetime_ticktick"] = ticktick_format
                    logger.info(f"时间格式已转换: {dt_str} -> {ticktick_format}")
                except Exception as e:
                    logger.warning(f"时间格式转换失败: {e}")
            
            logger.info(f"时间提取完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"时间提取失败: {e}")
            return {"has_time": False, "error": str(e)}

