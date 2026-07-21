import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.system.notification import (
    NotificationChannel,
    EmailNotification,
    WebhookNotification,
    NotificationManager
)
from src.system.alert import Alert, AlertLevel

@pytest.fixture
def sample_alert():
    """创建测试用的告警"""
    return Alert(
        id="test_alert_1",
        level=AlertLevel.WARNING,
        title="测试告警",
        message="这是一个测试告警",
        timestamp=datetime.now(),
        source="test",
        metadata={"test": "data"}
    )

@pytest.fixture
def email_notification():
    """创建测试用的邮件通知渠道"""
    return EmailNotification(
        smtp_server="smtp.example.com",
        smtp_port=587,
        username="test@example.com",
        password="password",
        from_email="test@example.com",
        to_emails=["recipient@example.com"]
    )

@pytest.fixture
def webhook_notification():
    """创建测试用的Webhook通知渠道"""
    return WebhookNotification(
        webhook_url="http://example.com/webhook",
        headers={"Authorization": "Bearer token"}
    )

@pytest.fixture
def notification_manager():
    """创建测试用的通知管理器"""
    return NotificationManager()

def test_email_notification_success(email_notification, sample_alert):
    """测试邮件通知发送成功"""
    with patch('smtplib.SMTP') as mock_smtp:
        # 配置模拟对象
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # 发送通知
        success = email_notification.send(sample_alert)
        
        # 验证结果
        assert success
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(
            "test@example.com",
            "password"
        )
        mock_server.send_message.assert_called_once()

def test_email_notification_failure(email_notification, sample_alert):
    """测试邮件通知发送失败"""
    with patch('smtplib.SMTP') as mock_smtp:
        # 配置模拟对象抛出异常
        mock_smtp.side_effect = Exception("SMTP错误")
        
        # 发送通知
        success = email_notification.send(sample_alert)
        
        # 验证结果
        assert not success

def test_webhook_notification_success(webhook_notification, sample_alert):
    """测试Webhook通知发送成功"""
    with patch('requests.post') as mock_post:
        # 配置模拟对象
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # 发送通知
        success = webhook_notification.send(sample_alert)
        
        # 验证结果
        assert success
        mock_post.assert_called_once_with(
            "http://example.com/webhook",
            json={
                'level': 'WARNING',
                'title': '测试告警',
                'message': '这是一个测试告警',
                'timestamp': sample_alert.timestamp.isoformat(),
                'source': 'test',
                'metadata': {'test': 'data'}
            },
            headers={"Authorization": "Bearer token"}
        )

def test_webhook_notification_failure(webhook_notification, sample_alert):
    """测试Webhook通知发送失败"""
    with patch('requests.post') as mock_post:
        # 配置模拟对象返回错误状态码
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        # 发送通知
        success = webhook_notification.send(sample_alert)
        
        # 验证结果
        assert not success

def test_notification_manager_add_channel(notification_manager, email_notification):
    """测试添加通知渠道"""
    notification_manager.add_channel("email", email_notification)
    assert "email" in notification_manager.channels
    assert notification_manager.channels["email"] == email_notification

def test_notification_manager_remove_channel(notification_manager, email_notification):
    """测试移除通知渠道"""
    notification_manager.add_channel("email", email_notification)
    notification_manager.remove_channel("email")
    assert "email" not in notification_manager.channels

def test_notification_manager_send_notification(
    notification_manager,
    email_notification,
    webhook_notification,
    sample_alert
):
    """测试发送通知"""
    # 添加通知渠道
    notification_manager.add_channel("email", email_notification)
    notification_manager.add_channel("webhook", webhook_notification)
    
    # 配置模拟对象
    with patch.object(email_notification, 'send', return_value=True), \
         patch.object(webhook_notification, 'send', return_value=True):
        
        # 发送通知
        success = notification_manager.send_notification(sample_alert)
        
        # 验证结果
        assert success

def test_notification_manager_send_notification_with_specific_channels(
    notification_manager,
    email_notification,
    webhook_notification,
    sample_alert
):
    """测试使用特定渠道发送通知"""
    # 添加通知渠道
    notification_manager.add_channel("email", email_notification)
    notification_manager.add_channel("webhook", webhook_notification)
    
    # 配置模拟对象
    with patch.object(email_notification, 'send', return_value=True), \
         patch.object(webhook_notification, 'send', return_value=False):
        
        # 发送通知
        success = notification_manager.send_notification(
            sample_alert,
            channel_names=["email"]
        )
        
        # 验证结果
        assert success

def test_notification_manager_no_channels(notification_manager, sample_alert):
    """测试没有配置通知渠道的情况"""
    success = notification_manager.send_notification(sample_alert)
    assert not success

def test_notification_manager_get_channel_names(
    notification_manager,
    email_notification,
    webhook_notification
):
    """测试获取渠道名称列表"""
    # 添加通知渠道
    notification_manager.add_channel("email", email_notification)
    notification_manager.add_channel("webhook", webhook_notification)
    
    # 获取渠道名称列表
    channel_names = notification_manager.get_channel_names()
    
    # 验证结果
    assert set(channel_names) == {"email", "webhook"} 