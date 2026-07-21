import os
import sys
from typing import Optional
from loguru import logger
from .config_manager import ConfigManager, LogConfig

class LogManager:
    """日志管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.log_config = config_manager.get_log_config()
        self._setup_logger()
        
    def _setup_logger(self):
        """配置日志系统"""
        try:
            # 移除默认处理器
            logger.remove()
            
            # 添加控制台处理器
            logger.add(
                sys.stderr,
                format=self.log_config.format,
                level=self.log_config.level,
                colorize=True
            )
            
            # 创建日志目录
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            
            # 添加文件处理器
            logger.add(
                os.path.join(log_dir, "system.log"),
                format=self.log_config.format,
                level=self.log_config.level,
                rotation=self.log_config.rotation,
                retention=self.log_config.retention,
                compression=self.log_config.compression,
                encoding=self.log_config.encoding
            )
            
            # 添加错误日志处理器
            logger.add(
                os.path.join(log_dir, "error.log"),
                format=self.log_config.format,
                level="ERROR",
                rotation=self.log_config.rotation,
                retention=self.log_config.retention,
                compression=self.log_config.compression,
                encoding=self.log_config.encoding
            )
            
            logger.info("日志系统初始化完成")
            
        except Exception as e:
            print(f"配置日志系统时发生错误: {e}")
            sys.exit(1)
            
    def add_file_logger(self, name: str, level: Optional[str] = None):
        """添加文件日志处理器"""
        try:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            
            logger.add(
                os.path.join(log_dir, f"{name}.log"),
                format=self.log_config.format,
                level=level or self.log_config.level,
                rotation=self.log_config.rotation,
                retention=self.log_config.retention,
                compression=self.log_config.compression,
                encoding=self.log_config.encoding
            )
            
            logger.info(f"已添加文件日志处理器: {name}")
            
        except Exception as e:
            logger.error(f"添加文件日志处理器时发生错误: {e}")
            
    def update_log_level(self, level: str):
        """更新日志级别"""
        try:
            self.log_config.level = level
            self._setup_logger()
            logger.info(f"日志级别已更新为: {level}")
            
        except Exception as e:
            logger.error(f"更新日志级别时发生错误: {e}")
            
    def get_logger(self):
        """获取日志记录器"""
        return logger 