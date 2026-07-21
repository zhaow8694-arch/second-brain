import asyncio
import logging
from loguru import logger
from system.health import SystemHealthMonitor
from system.alert import AlertManager
from system.shutdown import ShutdownManager
from utils.db_test import DatabaseTester
from utils.config import config

class TradingSystem:
    def __init__(self):
        # 初始化告警管理器
        self.alert_manager = AlertManager()
        
        # 初始化健康监控器
        self.health_monitor = SystemHealthMonitor(self.alert_manager)
        self.health_monitor.set_check_interval(config.health_check_interval)
        
        # 初始化关闭管理器
        self.shutdown_manager = ShutdownManager()
        
        # 初始化数据库测试器
        self.db_tester = DatabaseTester(config.get_database_config())
    
    async def start(self):
        """启动交易系统"""
        try:
            # 测试数据库连接
            logger.info("测试数据库连接...")
            db_results = await self.db_tester.test_all()
            for db, success in db_results.items():
                if not success:
                    logger.error(f"{db} 连接失败")
                    return False
            
            # 启动健康监控
            logger.info("启动健康监控...")
            asyncio.create_task(self.health_monitor.start())
            
            # 启动其他组件
            logger.info("启动其他组件...")
            # TODO: 启动其他组件
            
            return True
            
        except Exception as e:
            logger.error(f"系统启动失败: {str(e)}")
            return False
    
    async def stop(self):
        """停止交易系统"""
        try:
            # 停止健康监控
            await self.health_monitor.stop()
            
            # 执行优雅关闭
            await self.shutdown_manager.shutdown()
            
            return True
            
        except Exception as e:
            logger.error(f"系统停止失败: {str(e)}")
            return False

async def main():
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建交易系统实例
    system = TradingSystem()
    
    try:
        # 启动系统
        if await system.start():
            logger.info("交易系统启动成功")
            
            # 保持系统运行
            while True:
                await asyncio.sleep(1)
        else:
            logger.error("交易系统启动失败")
            
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号，开始关闭系统...")
        await system.stop()
    except Exception as e:
        logger.error(f"系统运行错误: {str(e)}")
        await system.stop()

if __name__ == "__main__":
    asyncio.run(main()) 