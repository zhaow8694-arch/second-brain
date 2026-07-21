from src.system.config_manager import ConfigManager
from src.system.log_manager import LogManager

def main():
    # 初始化配置管理器
    config_manager = ConfigManager("config/config.yaml")
    
    # 初始化日志管理器
    log_manager = LogManager(config_manager)
    logger = log_manager.get_logger()
    
    # 记录系统启动日志
    logger.info("系统启动")
    
    try:
        # 获取数据库配置
        db_config = config_manager.get_database_config()
        logger.info(f"数据库配置: {db_config}")
        
        # 获取Redis配置
        redis_config = config_manager.get_redis_config()
        logger.info(f"Redis配置: {redis_config}")
        
        # 获取日志配置
        log_config = config_manager.get_log_config()
        logger.info(f"日志配置: {log_config}")
        
        # 获取风控配置
        risk_config = config_manager.get_risk_config()
        logger.info(f"风控配置: {risk_config}")
        
        # 更新配置示例
        config_manager.update_config("database", "port", 3307)
        logger.info("数据库端口已更新为3307")
        
        # 添加新的日志文件
        log_manager.add_file_logger("custom")
        logger.info("已添加自定义日志文件")
        
        # 更新日志级别
        log_manager.update_log_level("DEBUG")
        logger.debug("日志级别已更新为DEBUG")
        
        # 模拟一些操作
        logger.info("开始执行系统操作")
        
        # 模拟错误
        try:
            raise ValueError("模拟系统错误")
        except ValueError as e:
            logger.error(f"系统错误: {e}")
        
        logger.info("系统操作完成")
        
    except Exception as e:
        logger.error(f"系统异常: {e}")
        raise
    
    finally:
        # 记录系统关闭日志
        logger.info("系统关闭")

if __name__ == "__main__":
    main() 