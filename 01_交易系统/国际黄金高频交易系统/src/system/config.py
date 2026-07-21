import os
import json
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from src.system.logger import logger

@dataclass
class MonitoringConfig:
    """监控配置"""
    collection_interval: int = 60  # 数据采集间隔（秒）
    retention_days: int = 30  # 数据保留天数
    performance_thresholds: Dict[str, float] = None  # 性能指标阈值
    
    def __post_init__(self):
        if self.performance_thresholds is None:
            self.performance_thresholds = {
                "cpu_usage": 80.0,  # CPU使用率阈值
                "memory_usage": 80.0,  # 内存使用率阈值
                "disk_usage": 85.0,  # 磁盘使用率阈值
                "network_latency": 100.0  # 网络延迟阈值（毫秒）
            }

@dataclass
class AlertConfig:
    """告警配置"""
    enabled: bool = True  # 是否启用告警
    min_interval: int = 300  # 最小告警间隔（秒）
    max_alerts_per_day: int = 100  # 每天最大告警数
    alert_levels: Dict[str, Dict[str, Any]] = None  # 告警级别配置
    
    def __post_init__(self):
        if self.alert_levels is None:
            self.alert_levels = {
                "INFO": {"enabled": True},
                "WARNING": {"enabled": True},
                "ERROR": {"enabled": True},
                "CRITICAL": {"enabled": True}
            }

@dataclass
class NotificationConfig:
    """通知配置"""
    email: Dict[str, Any] = None  # 邮件通知配置
    webhook: Dict[str, Any] = None  # Webhook通知配置
    
    def __post_init__(self):
        if self.email is None:
            self.email = {
                "enabled": False,
                "smtp_server": "",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_email": "",
                "to_emails": []
            }
        if self.webhook is None:
            self.webhook = {
                "enabled": False,
                "url": "",
                "headers": {}
            }

@dataclass
class StorageConfig:
    """存储配置"""
    db_type: str = "sqlite"  # 数据库类型
    db_path: str = "data/monitoring.db"  # 数据库路径
    backup_enabled: bool = True  # 是否启用备份
    backup_interval: int = 86400  # 备份间隔（秒）
    backup_path: str = "data/backups"  # 备份路径

@dataclass
class SystemConfig:
    """系统配置"""
    monitoring: MonitoringConfig = None
    alert: AlertConfig = None
    notification: NotificationConfig = None
    storage: StorageConfig = None
    
    def __post_init__(self):
        if self.monitoring is None:
            self.monitoring = MonitoringConfig()
        if self.alert is None:
            self.alert = AlertConfig()
        if self.notification is None:
            self.notification = NotificationConfig()
        if self.storage is None:
            self.storage = StorageConfig()

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config/system_config.yaml"):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_default_config()
        
    def _load_default_config(self) -> SystemConfig:
        """加载默认配置"""
        return SystemConfig()
    
    def load_config(self) -> bool:
        """从文件加载配置
        
        Returns:
            bool: 是否加载成功
        """
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"配置文件不存在: {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.endswith('.json'):
                    config_data = json.load(f)
                else:
                    config_data = yaml.safe_load(f)
            
            # 更新配置
            self._update_config(config_data)
            logger.info("配置加载成功")
            return True
            
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
            return False
    
    def save_config(self) -> bool:
        """保存配置到文件
        
        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # 转换配置为字典
            config_data = self._config_to_dict()
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.endswith('.json'):
                    json.dump(config_data, f, indent=4, ensure_ascii=False)
                else:
                    yaml.safe_dump(config_data, f, allow_unicode=True)
            
            logger.info("配置保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            return False
    
    def _update_config(self, config_data: Dict[str, Any]) -> None:
        """更新配置
        
        Args:
            config_data: 配置数据
        """
        if "monitoring" in config_data:
            self.config.monitoring = MonitoringConfig(**config_data["monitoring"])
        if "alert" in config_data:
            self.config.alert = AlertConfig(**config_data["alert"])
        if "notification" in config_data:
            self.config.notification = NotificationConfig(**config_data["notification"])
        if "storage" in config_data:
            self.config.storage = StorageConfig(**config_data["storage"])
    
    def _config_to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            "monitoring": asdict(self.config.monitoring),
            "alert": asdict(self.config.alert),
            "notification": asdict(self.config.notification),
            "storage": asdict(self.config.storage)
        }
    
    def get_config(self) -> SystemConfig:
        """获取当前配置
        
        Returns:
            SystemConfig: 系统配置
        """
        return self.config
    
    def update_config(self, config_data: Dict[str, Any]) -> bool:
        """更新配置
        
        Args:
            config_data: 新的配置数据
            
        Returns:
            bool: 是否更新成功
        """
        try:
            self._update_config(config_data)
            return True
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False
    
    def validate_config(self) -> bool:
        """验证配置有效性
        
        Returns:
            bool: 配置是否有效
        """
        try:
            # 验证监控配置
            if self.config.monitoring.collection_interval <= 0:
                raise ValueError("数据采集间隔必须大于0")
            if self.config.monitoring.retention_days <= 0:
                raise ValueError("数据保留天数必须大于0")
            
            # 验证告警配置
            if self.config.alert.min_interval <= 0:
                raise ValueError("最小告警间隔必须大于0")
            if self.config.alert.max_alerts_per_day <= 0:
                raise ValueError("每天最大告警数必须大于0")
            
            # 验证通知配置
            if self.config.notification.email["enabled"]:
                if not self.config.notification.email["smtp_server"]:
                    raise ValueError("SMTP服务器地址不能为空")
                if not self.config.notification.email["username"]:
                    raise ValueError("邮箱用户名不能为空")
                if not self.config.notification.email["password"]:
                    raise ValueError("邮箱密码不能为空")
                if not self.config.notification.email["to_emails"]:
                    raise ValueError("收件人列表不能为空")
            
            if self.config.notification.webhook["enabled"]:
                if not self.config.notification.webhook["url"]:
                    raise ValueError("Webhook URL不能为空")
            
            # 验证存储配置
            if self.config.storage.backup_enabled:
                if self.config.storage.backup_interval <= 0:
                    raise ValueError("备份间隔必须大于0")
                if not self.config.storage.backup_path:
                    raise ValueError("备份路径不能为空")
            
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {str(e)}")
            return False 