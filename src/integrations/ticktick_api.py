"""TickTick (via Jijiyun Webhook) 集成"""
import requests
from typing import Optional, Dict, Any
from loguru import logger


class TickTickAPI:
    """通过集简云 Webhook 将任务发送到滴答清单"""

    def __init__(self, webhook_url: str):
        """
        初始化 TickTick 客户端

        Args:
            webhook_url: 集简云提供的 Webhook URL
        """
        self.webhook_url = webhook_url
        logger.info("TickTick API (Webhook) 已初始化")

    def add_task(
        self,
        title: str,
        content: Optional[str] = None,
        list_name: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        通过集简云 Webhook 创建滴答清单任务

        Args:
            title: 任务标题
            content: 任务内容/备注
            list_name: 清单名称（可选，仅作为数据字段，由集简云流程决定如何使用）
            extra: 其他自定义字段，将一并发送给集简云

        Returns:
            是否发送成功（仅表示 Webhook 请求成功）
        """
        try:
            payload: Dict[str, Any] = {
                "title": title,
                "content": content or "",
            }

            if list_name:
                payload["list_name"] = list_name

            if extra:
                payload.update(extra)

            logger.info(
                f"发送任务到 TickTick Webhook: title={title[:50]}..., "
                f"list_name={list_name or ''}"
            )

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                logger.info("TickTick Webhook 请求发送成功")
                return True
            else:
                logger.error(
                    f"TickTick Webhook 请求失败: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"TickTick Webhook 请求异常: {e}")
            return False

    def test_connection(self) -> bool:
        """测试 Webhook 是否可用（发送一条简单测试消息）"""
        try:
            response = requests.post(
                self.webhook_url,
                json={
                    "title": "QuickNote AI 连接测试",
                    "content": "来自 QuickNote AI 的 TickTick 集成测试。",
                    "source": "QuickNoteAI",
                },
                timeout=10,
            )

            if response.status_code == 200:
                logger.info("TickTick Webhook 连接测试成功")
                return True
            else:
                logger.error(
                    f"TickTick Webhook 连接测试失败: {response.status_code} - {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"TickTick Webhook 连接测试异常: {e}")
            return False


