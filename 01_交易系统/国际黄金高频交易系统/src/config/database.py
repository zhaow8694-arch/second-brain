from typing import Dict, Any
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class DatabaseSettings(BaseSettings):
    """数据库配置类"""
    
    # PostgreSQL配置
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "trading_system"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = None
    
    # 连接池配置
    MAX_CONNECTIONS: int = 20
    MIN_CONNECTIONS: int = 5
    
    class Config:
        env_file = ".env"
        
    @property
    def postgres_dsn(self) -> str:
        """获取PostgreSQL连接字符串"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
    @property
    def redis_url(self) -> str:
        """获取Redis连接URL"""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        
    def get_postgres_config(self) -> Dict[str, Any]:
        """获取PostgreSQL配置字典"""
        return {
            "host": self.POSTGRES_HOST,
            "port": self.POSTGRES_PORT,
            "database": self.POSTGRES_DB,
            "user": self.POSTGRES_USER,
            "password": self.POSTGRES_PASSWORD,
            "max_connections": self.MAX_CONNECTIONS,
            "min_connections": self.MIN_CONNECTIONS
        }
        
    def get_redis_config(self) -> Dict[str, Any]:
        """获取Redis配置字典"""
        return {
            "host": self.REDIS_HOST,
            "port": self.REDIS_PORT,
            "db": self.REDIS_DB,
            "password": self.REDIS_PASSWORD
        }

# 创建全局配置实例
db_settings = DatabaseSettings() 