import time
import random
from datetime import datetime, timedelta
from src.system.alert import Alert, AlertLevel
from src.system.notification import (
    EmailNotification,
    WebhookNotification,
    NotificationManager
)
from src.system.storage import MonitoringStorage
from src.system.visualization import DataVisualizer
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def simulate_alert():
    """模拟生成告警"""
    levels = [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]
    components = ["database", "cache", "api", "order_engine", "risk_control"]
    
    level = random.choice(levels)
    component = random.choice(components)
    
    if level == AlertLevel.INFO:
        message = f"组件 {component} 运行正常"
    elif level == AlertLevel.WARNING:
        message = f"组件 {component} 性能下降"
    elif level == AlertLevel.ERROR:
        message = f"组件 {component} 出现错误"
    else:  # CRITICAL
        message = f"组件 {component} 严重故障"
    
    return Alert(
        id=f"alert_{int(time.time())}",
        level=level,
        title=f"{component} 状态告警",
        message=message,
        timestamp=datetime.now(),
        source=component,
        metadata={
            "component": component,
            "level": level.name,
            "timestamp": datetime.now().isoformat()
        }
    )

def main():
    """主函数"""
    # 初始化存储管理器
    storage = MonitoringStorage()
    
    # 初始化通知管理器
    notification_manager = NotificationManager()
    
    # 添加邮件通知渠道
    email_notification = EmailNotification(
        smtp_server="smtp.example.com",  # 替换为实际的SMTP服务器
        smtp_port=587,
        username="your_email@example.com",  # 替换为实际的邮箱
        password="your_password",  # 替换为实际的密码
        from_email="your_email@example.com",
        to_emails=["recipient@example.com"]  # 替换为实际的收件人
    )
    notification_manager.add_channel("email", email_notification)
    
    # 添加Webhook通知渠道
    webhook_notification = WebhookNotification(
        webhook_url="http://example.com/webhook",  # 替换为实际的Webhook URL
        headers={"Authorization": "Bearer your_token"}  # 替换为实际的认证信息
    )
    notification_manager.add_channel("webhook", webhook_notification)
    
    # 初始化数据可视化器
    visualizer = DataVisualizer(storage)
    
    try:
        logger.info("开始模拟系统运行...")
        start_time = time.time()
        
        while time.time() - start_time < 300:  # 运行5分钟
            # 生成告警
            alert = simulate_alert()
            
            # 保存告警
            storage.save_alert(alert)
            
            # 发送通知
            if alert.level in [AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]:
                logger.info(f"发送告警通知: {alert.title}")
                notification_manager.send_notification(alert)
            
            # 每30秒生成一次可视化图表
            if int(time.time() - start_time) % 30 == 0:
                logger.info("生成监控图表...")
                visualizer.generate_dashboard()
            
            time.sleep(1)  # 每秒生成一次数据
            
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    finally:
        # 生成最终的可视化图表
        logger.info("生成最终监控图表...")
        visualizer.generate_dashboard()
        logger.info("程序结束")

if __name__ == "__main__":
    main() 