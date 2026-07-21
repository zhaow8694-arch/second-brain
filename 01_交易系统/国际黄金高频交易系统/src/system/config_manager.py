import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger

@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str = "utf8mb4"

@dataclass
class RedisConfig:
    """Redis配置"""
    host: str
    port: int
    password: Optional[str] = None
    db: int = 0
    decode_responses: bool = True

@dataclass
class LogConfig:
    """日志配置"""
    level: str
    format: str
    rotation: str
    retention: str
    compression: str
    encoding: str = "utf-8"

@dataclass
class RiskConfig:
    """风控配置"""
    max_position_size: float
    max_daily_loss: float
    max_drawdown: float
    max_leverage: float
    min_margin_ratio: float
    max_order_size: float
    max_orders_per_minute: int

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load_config()
        
    def _load_config(self):
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"配置文件不存在: {self.config_path}")
                self._create_default_config()
                return
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                
            logger.info(f"成功加载配置文件: {self.config_path}")
            
        except Exception as e:
            logger.error(f"加载配置文件时发生错误: {e}")
            self._create_default_config()
            
    def _create_default_config(self):
        """创建默认配置"""
        self.config = {
            "database": {
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "password",
                "database": "trading_system",
                "charset": "utf8mb4"
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "password": None,
                "db": 0,
                "decode_responses": True
            },
            "log": {
                "level": "INFO",
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                "rotation": "500 MB",
                "retention": "10 days",
                "compression": "zip",
                "encoding": "utf-8"
            },
            "risk": {
                "max_position_size": 10.0,
                "max_daily_loss": 1000.0,
                "max_drawdown": 0.1,
                "max_leverage": 5.0,
                "min_margin_ratio": 0.1,
                "max_order_size": 5.0,
                "max_orders_per_minute": 10
            }
        }
        
        # 创建配置目录
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # 保存默认配置
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True)
            
        logger.info(f"已创建默认配置文件: {self.config_path}")
        
    def get_database_config(self) -> DatabaseConfig:
        """获取数据库配置"""
        return DatabaseConfig(**self.config["database"])
        
    def get_redis_config(self) -> RedisConfig:
        """获取Redis配置"""
        return RedisConfig(**self.config["redis"])
        
    def get_log_config(self) -> LogConfig:
        """获取日志配置"""
        return LogConfig(**self.config["log"])
        
    def get_risk_config(self) -> RiskConfig:
        """获取风控配置"""
        return RiskConfig(**self.config["risk"])
        
    def update_config(self, section: str, key: str, value: Any):
        """更新配置"""
        try:
            if section not in self.config:
                self.config[section] = {}
                
            self.config[section][key] = value
            
            # 保存到文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True)
                
            logger.info(f"配置已更新: {section}.{key} = {value}")
            
        except Exception as e:
            logger.error(f"更新配置时发生错误: {e}")
            
    def reload_config(self):
        """重新加载配置"""
        self._load_config() 