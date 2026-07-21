import os
import yaml
from src.system.config import ConfigManager
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_example_config():
    """创建示例配置"""
    return {
        "monitoring": {
            "collection_interval": 30,
            "retention_days": 60,
            "performance_thresholds": {
                "cpu_usage": 90.0,
                "memory_usage": 85.0,
                "disk_usage": 90.0,
                "network_latency": 150.0
            }
        },
        "alert": {
            "enabled": True,
            "min_interval": 600,
            "max_alerts_per_day": 50,
            "alert_levels": {
                "INFO": {"enabled": False},
                "WARNING": {"enabled": True},
                "ERROR": {"enabled": True},
                "CRITICAL": {"enabled": True}
            }
        },
        "notification": {
            "email": {
                "enabled": True,
                "smtp_server": "smtp.example.com",
                "smtp_port": 587,
                "username": "alert@example.com",
                "password": "your_password",
                "from_email": "alert@example.com",
                "to_emails": ["admin@example.com"]
            },
            "webhook": {
                "enabled": True,
                "url": "http://example.com/webhook",
                "headers": {"Authorization": "Bearer your_token"}
            }
        },
        "storage": {
            "db_type": "sqlite",
            "db_path": "data/monitoring.db",
            "backup_enabled": True,
            "backup_interval": 43200,
            "backup_path": "data/backups"
        }
    }

def main():
    """主函数"""
    # 创建配置目录
    config_dir = "config"
    os.makedirs(config_dir, exist_ok=True)
    
    # 配置文件路径
    yaml_path = os.path.join(config_dir, "system_config.yaml")
    
    # 初始化配置管理器
    config_manager = ConfigManager(yaml_path)
    
    # 创建并保存示例配置
    logger.info("创建示例配置...")
    example_config = create_example_config()
    config_manager.update_config(example_config)
    
    # 验证配置
    logger.info("验证配置...")
    if not config_manager.validate_config():
        logger.error("配置验证失败")
        return
    
    # 保存配置
    logger.info("保存配置到文件...")
    if not config_manager.save_config():
        logger.error("保存配置失败")
        return
    
    # 从文件加载配置
    logger.info("从文件加载配置...")
    if not config_manager.load_config():
        logger.error("加载配置失败")
        return
    
    # 获取当前配置
    config = config_manager.get_config()
    
    # 打印配置信息
    logger.info("\n当前配置信息:")
    logger.info("监控配置:")
    logger.info(f"  采集间隔: {config.monitoring.collection_interval}秒")
    logger.info(f"  数据保留天数: {config.monitoring.retention_days}天")
    logger.info("  性能阈值:")
    for metric, threshold in config.monitoring.performance_thresholds.items():
        logger.info(f"    {metric}: {threshold}")
    
    logger.info("\n告警配置:")
    logger.info(f"  是否启用: {config.alert.enabled}")
    logger.info(f"  最小告警间隔: {config.alert.min_interval}秒")
    logger.info(f"  每天最大告警数: {config.alert.max_alerts_per_day}")
    logger.info("  告警级别:")
    for level, settings in config.alert.alert_levels.items():
        logger.info(f"    {level}: {'启用' if settings['enabled'] else '禁用'}")
    
    logger.info("\n通知配置:")
    logger.info("  邮件通知:")
    logger.info(f"    是否启用: {config.notification.email['enabled']}")
    if config.notification.email['enabled']:
        logger.info(f"    SMTP服务器: {config.notification.email['smtp_server']}")
        logger.info(f"    发件人: {config.notification.email['from_email']}")
        logger.info(f"    收件人: {', '.join(config.notification.email['to_emails'])}")
    
    logger.info("  Webhook通知:")
    logger.info(f"    是否启用: {config.notification.webhook['enabled']}")
    if config.notification.webhook['enabled']:
        logger.info(f"    URL: {config.notification.webhook['url']}")
    
    logger.info("\n存储配置:")
    logger.info(f"  数据库类型: {config.storage.db_type}")
    logger.info(f"  数据库路径: {config.storage.db_path}")
    logger.info(f"  是否启用备份: {config.storage.backup_enabled}")
    if config.storage.backup_enabled:
        logger.info(f"  备份间隔: {config.storage.backup_interval}秒")
        logger.info(f"  备份路径: {config.storage.backup_path}")
    
    # 更新部分配置
    logger.info("\n更新部分配置...")
    partial_config = {
        "monitoring": {
            "collection_interval": 45,
            "performance_thresholds": {
                "cpu_usage": 95.0
            }
        },
        "alert": {
            "max_alerts_per_day": 75
        }
    }
    
    if not config_manager.update_config(partial_config):
        logger.error("更新配置失败")
        return
    
    # 重新获取配置
    config = config_manager.get_config()
    
    # 打印更新后的配置
    logger.info("\n更新后的配置:")
    logger.info(f"  采集间隔: {config.monitoring.collection_interval}秒")
    logger.info(f"  CPU使用率阈值: {config.monitoring.performance_thresholds['cpu_usage']}%")
    logger.info(f"  每天最大告警数: {config.alert.max_alerts_per_day}")
    
    logger.info("\n配置管理演示完成")

if __name__ == "__main__":
    main() 