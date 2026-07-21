import os
from typing import Dict, Any
from dotenv import load_dotenv
from loguru import logger

class Config:
    def __init__(self):
        # 加载环境变量
        load_dotenv()
        
        # 数据库配置
        self.postgresql_url = os.getenv('POSTGRESQL_URL', 'postgresql+asyncpg://user:password@localhost:5432/dbname')
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_db = int(os.getenv('REDIS_DB', '0'))
        self.mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        self.mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
        self.mysql_user = os.getenv('MYSQL_USER', 'user')
        self.mysql_password = os.getenv('MYSQL_PASSWORD', 'password')
        self.mysql_database = os.getenv('MYSQL_DATABASE', 'dbname')
        
        # 系统配置
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.health_check_interval = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))
        self.cpu_threshold = int(os.getenv('CPU_THRESHOLD', '80'))
        self.memory_threshold = int(os.getenv('MEMORY_THRESHOLD', '80'))
        self.disk_threshold = int(os.getenv('DISK_THRESHOLD', '80'))
        
        # 告警配置
        self.alert_email_enabled = os.getenv('ALERT_EMAIL_ENABLED', 'false').lower() == 'true'
        self.alert_email_host = os.getenv('ALERT_EMAIL_HOST', 'smtp.example.com')
        self.alert_email_port = int(os.getenv('ALERT_EMAIL_PORT', '587'))
        self.alert_email_user = os.getenv('ALERT_EMAIL_USER', 'alert@example.com')
        self.alert_email_password = os.getenv('ALERT_EMAIL_PASSWORD', 'your_password')
        self.alert_email_recipients = os.getenv('ALERT_EMAIL_RECIPIENTS', 'admin@example.com').split(',')
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return {
            'postgresql': {
                'url': self.postgresql_url
            },
            'redis': {
                'host': self.redis_host,
                'port': self.redis_port,
                'db': self.redis_db
            },
            'mysql': {
                'host': self.mysql_host,
                'port': self.mysql_port,
                'user': self.mysql_user,
                'password': self.mysql_password,
                'database': self.mysql_database
            }
        }
    
    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return {
            'log_level': self.log_level,
            'health_check_interval': self.health_check_interval,
            'cpu_threshold': self.cpu_threshold,
            'memory_threshold': self.memory_threshold,
            'disk_threshold': self.disk_threshold
        }
    
    def get_alert_config(self) -> Dict[str, Any]:
        """获取告警配置"""
        return {
            'email_enabled': self.alert_email_enabled,
            'email_host': self.alert_email_host,
            'email_port': self.alert_email_port,
            'email_user': self.alert_email_user,
            'email_password': self.alert_email_password,
            'email_recipients': self.alert_email_recipients
        }

# 创建全局配置实例
config = Config() 