import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from src.system.alert import Alert, AlertLevel
from src.system.logger import logger

class NotificationChannel(ABC):
    """通知渠道基类"""
    
    @abstractmethod
    def send(self, alert: Alert) -> bool:
        """发送通知
        
        Args:
            alert: 告警信息
            
        Returns:
            bool: 是否发送成功
        """
        pass

class EmailNotification(NotificationChannel):
    """邮件通知渠道"""
    
    def __init__(self, 
                 smtp_server: str,
                 smtp_port: int,
                 username: str,
                 password: str,
                 from_email: str,
                 to_emails: List[str]):
        """初始化邮件通知渠道
        
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP服务器端口
            username: 用户名
            password: 密码
            from_email: 发件人邮箱
            to_emails: 收件人邮箱列表
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
    
    def send(self, alert: Alert) -> bool:
        """发送邮件通知
        
        Args:
            alert: 告警信息
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 创建邮件内容
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.level.name}] {alert.title}"
            
            # 构建邮件正文
            body = f"""
            告警级别: {alert.level.name}
            标题: {alert.title}
            消息: {alert.message}
            时间: {alert.timestamp}
            来源: {alert.source}
            """
            
            if alert.metadata:
                body += "\n元数据:\n"
                for key, value in alert.metadata.items():
                    body += f"{key}: {value}\n"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"邮件通知已发送: {alert.title}")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件通知失败: {str(e)}")
            return False

class WebhookNotification(NotificationChannel):
    """Webhook通知渠道"""
    
    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        """初始化Webhook通知渠道
        
        Args:
            webhook_url: Webhook URL
            headers: 请求头
        """
        self.webhook_url = webhook_url
        self.headers = headers or {}
    
    def send(self, alert: Alert) -> bool:
        """发送Webhook通知
        
        Args:
            alert: 告警信息
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 构建请求数据
            data = {
                'level': alert.level.name,
                'title': alert.title,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'source': alert.source,
                'metadata': alert.metadata
            }
            
            # 发送请求
            response = requests.post(
                self.webhook_url,
                json=data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook通知已发送: {alert.title}")
                return True
            else:
                logger.error(f"发送Webhook通知失败: {response.status_code}")
                return False
            
        except Exception as e:
            logger.error(f"发送Webhook通知失败: {str(e)}")
            return False

class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        """初始化通知管理器"""
        self.channels: Dict[str, NotificationChannel] = {}
    
    def add_channel(self, name: str, channel: NotificationChannel) -> None:
        """添加通知渠道
        
        Args:
            name: 渠道名称
            channel: 通知渠道实例
        """
        self.channels[name] = channel
    
    def remove_channel(self, name: str) -> None:
        """移除通知渠道
        
        Args:
            name: 渠道名称
        """
        if name in self.channels:
            del self.channels[name]
    
    def send_notification(self, alert: Alert, channel_names: Optional[List[str]] = None) -> bool:
        """发送通知
        
        Args:
            alert: 告警信息
            channel_names: 要使用的渠道名称列表，如果为None则使用所有渠道
            
        Returns:
            bool: 是否至少有一个渠道发送成功
        """
        if not self.channels:
            logger.warning("没有配置任何通知渠道")
            return False
        
        # 确定要使用的渠道
        channels_to_use = self.channels
        if channel_names:
            channels_to_use = {
                name: channel 
                for name, channel in self.channels.items() 
                if name in channel_names
            }
        
        # 发送通知
        success = False
        for name, channel in channels_to_use.items():
            if channel.send(alert):
                success = True
        
        return success
    
    def get_channel_names(self) -> List[str]:
        """获取所有渠道名称
        
        Returns:
            List[str]: 渠道名称列表
        """
        return list(self.channels.keys()) 