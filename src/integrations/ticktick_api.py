"""TickTick (via Email) 集成"""
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from typing import Optional, Dict, Any
from loguru import logger


class TickTickAPI:
    """通过邮件将任务发送到滴答清单"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_pass: str,
        ticktick_email: str,
    ):
        """
        初始化 TickTick 邮件客户端

        Args:
            smtp_host: SMTP服务器地址（如：smtp.qq.com）
            smtp_port: SMTP端口（如：465）
            smtp_user: 发件邮箱地址
            smtp_pass: SMTP授权码（不是邮箱密码）
            ticktick_email: 滴答清单专属邮箱地址（格式：todo+xxxxx@mail.dida365.com）
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        self.ticktick_email = ticktick_email
        logger.info("TickTick API (Email) 已初始化")

    def add_task(
        self,
        title: str,
        content: Optional[str] = None,
        list_name: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        通过邮件创建滴答清单任务

        Args:
            title: 任务标题（邮件主题）
            content: 任务内容/备注（邮件正文）
            list_name: 清单名称（可选，使用 ^清单名 格式添加到标题）
            extra: 其他自定义字段
                - due_date: 截止时间（格式：YYYY-MM-DDTHH:MM:SS+0800）
                - priority: 优先级（高/中/低，转换为 !!!/!!/! 格式）

        Returns:
            是否发送成功
        """
        try:
            # 构建邮件标题（支持滴答清单的智能识别格式）
            email_subject = title
            
            # 如果有清单名称，添加到标题（格式：^清单名）
            if list_name:
                email_subject = f"{email_subject} ^{list_name}"
            
            # 如果有优先级，转换为滴答清单格式（!!! = 高，!! = 中，! = 低）
            if extra and extra.get("priority"):
                priority = extra.get("priority")
                if priority == "高":
                    email_subject = f"{email_subject} !!!"
                elif priority == "中":
                    email_subject = f"{email_subject} !!"
                elif priority == "低":
                    email_subject = f"{email_subject} !"
            
            # 如果有截止时间，确保时间信息在标题中
            # 滴答清单会自动识别标题中的时间信息（如"明天下午3点"、"下周一"等）
            # 如果 extra 中有 due_date，说明 AI 已经提取了时间，通常时间信息已经在 title 中
            if extra and extra.get("due_date"):
                due_date = extra.get("due_date")
                logger.debug(f"任务截止时间: {due_date}")
                # 注意：时间信息通常已经在 title 中（AI 提取时会保留原始时间描述）
                # 如果 title 中没有时间信息，可以考虑添加，但为了保持标题简洁，这里不自动添加
            
            # 构建邮件正文（只使用原始内容，不添加截止时间）
            email_body = content or ""
            
            logger.info(
                f"发送任务到 TickTick (Email): subject={email_subject[:50]}..., "
                f"list_name={list_name or ''}"
            )

            # 构造邮件
            message = MIMEText(email_body, 'plain', 'utf-8')
            message['Subject'] = Header(email_subject, 'utf-8')
            message['From'] = self.smtp_user
            message['To'] = self.ticktick_email

            # 发送邮件
            server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.smtp_user, [self.ticktick_email], message.as_string())
            server.quit()

            logger.info("TickTick 邮件发送成功")
            return True

        except Exception as e:
            logger.error(f"TickTick 邮件发送异常: {e}")
            return False

    def test_connection(self) -> bool:
        """测试邮件发送是否可用（发送一条简单测试消息）"""
        try:
            test_subject = "QuickNote AI 连接测试"
            test_body = "来自 QuickNote AI 的 TickTick 集成测试。如果收到此邮件，说明配置成功！"
            
            message = MIMEText(test_body, 'plain', 'utf-8')
            message['Subject'] = Header(test_subject, 'utf-8')
            message['From'] = self.smtp_user
            message['To'] = self.ticktick_email

            server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.smtp_user, [self.ticktick_email], message.as_string())
            server.quit()

            logger.info("TickTick 邮件连接测试成功")
            return True
        except Exception as e:
            logger.error(f"TickTick 邮件连接测试异常: {e}")
            return False


