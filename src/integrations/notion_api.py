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
        tags: Optional[list] = None
    ) -> bool:
        """
        添加灵感到Notion Database
        
        Args:
            content: 内容
            title: 标题（可选，自动生成）
            priority: 优先级（高/中/低）
            tags: 标签列表
            
        Returns:
            是否成功
        """
        try:
            # 如果没有标题，使用内容前30个字符
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
                "状态": {
                    "status": {
                        "name": "待办"
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

