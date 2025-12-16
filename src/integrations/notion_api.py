"""Notion API集成"""
from typing import Dict, Any, Optional
from notion_client import Client
from loguru import logger
from datetime import datetime


class NotionAPI:
    """Notion API封装类"""
    
    def __init__(self, api_key: str, database_id: str):
        """
        初始化Notion客户端
        
        Args:
            api_key: Notion API密钥
            database_id: Database ID
        """
        self.client = Client(auth=api_key)
        self.database_id = database_id
        logger.info("Notion API已初始化")
    
    def add_inspiration(
        self, 
        content: str, 
        title: Optional[str] = None,
        priority: str = "中",
        status: str = "待办",
        tags: Optional[list] = None,
        ai_extract_title: bool = True
    ) -> bool:
        """
        添加灵感到Notion Database
        
        Args:
            content: 内容
            title: 标题（可选，将由AI提取或使用前30字符）
            priority: 优先级（高/中/低）
            tags: 标签列表
            ai_extract_title: 是否使用AI提取标题（默认True）
            
        Returns:
            是否成功
        """
        try:
            # 如果启用AI提取且没有提供标题，尝试用AI提取
            if ai_extract_title and not title:
                try:
                    from src.core.ai_processor import AIProcessor
                    from src.utils.config import config as app_config
                    ai = AIProcessor(app_config.ai_provider)
                    
                    # 使用特殊提示词，只获取标题文本
                    prompt = f"""请从以下内容中提取一个简短的标题（不超过25个字符），概括核心内容。

内容：{content}

要求：
1. 只返回标题文本，不要返回JSON或其他格式
2. 标题要简洁、准确，突出重点
3. 不超过25个字符

直接返回标题即可。"""
                    
                    if ai.provider in ["openai", "deepseek"]:
                        response = ai.client.chat.completions.create(
                            model=ai.model,
                            messages=[
                                {"role": "system", "content": "你是一个标题提取助手，只返回简短的标题文本，不要返回JSON。"},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.3,
                            max_tokens=50
                        )
                        extracted_title = response.choices[0].message.content.strip()
                        # 移除可能的引号
                        extracted_title = extracted_title.strip('"\'')
                        if extracted_title and len(extracted_title) <= 50:
                            title = extracted_title
                except Exception as e:
                    logger.warning(f"AI提取标题失败，使用默认方式: {e}")
            
            # 如果仍然没有标题，使用内容前30个字符
            if not title:
                title = content[:30] + "..." if len(content) > 30 else content
            
            # 构建页面属性
            properties = {
                "标题": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "描述": {
                    "rich_text": [
                        {
                            "text": {
                                "content": content[:2000]  # Notion限制，最多2000字符
                            }
                        }
                    ]
                },
                "状态": {
                    "status": {
                        "name": status
                    }
                },
                "优先级": {
                    "select": {
                        "name": priority
                    }
                },
                "创建时间": {
                    "date": {
                        "start": datetime.now().astimezone().isoformat()
                    }
                }
            }
            
            # 添加标签（如果有）
            if tags:
                properties["标签"] = {
                    "multi_select": [{"name": tag} for tag in tags]
                }
            
            # 构建内容块
            children = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": content
                                }
                            }
                        ]
                    }
                }
            ]
            
            # 创建页面
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children
            )
            
            logger.info(f"成功添加灵感到Notion: {title}")
            return True
            
        except Exception as e:
            logger.error(f"添加到Notion失败: {e}")
            return False
    
    def test_connection(self) -> bool:
        """测试Notion连接"""
        try:
            # 尝试获取database信息
            self.client.databases.retrieve(database_id=self.database_id)
            logger.info("Notion连接测试成功")
            return True
        except Exception as e:
            logger.error(f"Notion连接测试失败: {e}")
            return False

