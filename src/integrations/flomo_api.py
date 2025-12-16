"""Flomo API集成"""
import requests
from typing import Optional, List
from loguru import logger


class FlomoAPI:
    """Flomo API封装类"""
    
    def __init__(self, webhook_url: str):
        """
        初始化Flomo客户端
        
        Args:
            webhook_url: Flomo Webhook URL
        """
        self.webhook_url = webhook_url
        logger.info("Flomo API已初始化")
    
    def add_memo(
        self, 
        content: str, 
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        添加Memo到Flomo
        
        Args:
            content: 内容
            tags: 标签列表（可选）
            
        Returns:
            是否成功
        """
        try:
            # 构建内容（包含标签）
            full_content = content
            if tags:
                # Flomo的标签格式是 #标签名
                # 清理标签：去除已有的#号，然后统一添加
                cleaned_tags = [tag.lstrip('#').strip() for tag in tags if tag.strip()]
                tag_str = " ".join([f"#{tag}" for tag in cleaned_tags if tag])
                if tag_str:
                    full_content = f"{content}\n\n{tag_str}"
            
            # 发送POST请求
            response = requests.post(
                self.webhook_url,
                json={"content": full_content},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"成功添加Memo到Flomo: {content[:50]}...")
                return True
            else:
                logger.error(f"添加到Flomo失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"添加到Flomo失败: {e}")
            return False
    
    def test_connection(self) -> bool:
        """测试Flomo连接"""
        try:
            # 发送一个测试memo
            response = requests.post(
                self.webhook_url,
                json={"content": "QuickNote AI 连接测试"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Flomo连接测试成功")
                return True
            else:
                logger.error(f"Flomo连接测试失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Flomo连接测试失败: {e}")
            return False

