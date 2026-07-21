import asyncio
import signal
from typing import List, Callable, Awaitable
from loguru import logger

class GracefulShutdown:
    def __init__(self):
        self.shutdown_handlers: List[Callable[[], Awaitable[None]]] = []
        self.is_shutting_down = False
    
    def add_handler(self, handler: Callable[[], Awaitable[None]]):
        """添加关闭处理器"""
        self.shutdown_handlers.append(handler)
    
    async def shutdown(self):
        """执行优雅关闭"""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        logger.info("开始系统优雅关闭...")
        
        try:
            # 按顺序执行所有关闭处理器
            for handler in self.shutdown_handlers:
                try:
                    await handler()
                except Exception as e:
                    logger.error(f"关闭处理器执行失败: {str(e)}")
            
            logger.info("系统优雅关闭完成")
        except Exception as e:
            logger.error(f"系统关闭过程中发生错误: {str(e)}")
        finally:
            self.is_shutting_down = False
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，开始优雅关闭...")
        asyncio.create_task(self.shutdown())

class ShutdownManager:
    def __init__(self):
        self.graceful_shutdown = GracefulShutdown()
        self.setup_handlers()
        self.graceful_shutdown.setup_signal_handlers()
    
    def setup_handlers(self):
        """设置关闭处理器"""
        # 添加数据库连接关闭处理器
        self.graceful_shutdown.add_handler(self.close_database_connections)
        
        # 添加消息队列关闭处理器
        self.graceful_shutdown.add_handler(self.close_message_queue)
        
        # 添加缓存关闭处理器
        self.graceful_shutdown.add_handler(self.close_cache)
        
        # 添加健康监控关闭处理器
        self.graceful_shutdown.add_handler(self.stop_health_monitor)
    
    async def close_database_connections(self):
        """关闭数据库连接"""
        logger.info("正在关闭数据库连接...")
        # 实现数据库连接关闭逻辑
        await asyncio.sleep(1)  # 模拟关闭过程
    
    async def close_message_queue(self):
        """关闭消息队列连接"""
        logger.info("正在关闭消息队列连接...")
        # 实现消息队列关闭逻辑
        await asyncio.sleep(1)  # 模拟关闭过程
    
    async def close_cache(self):
        """关闭缓存连接"""
        logger.info("正在关闭缓存连接...")
        # 实现缓存关闭逻辑
        await asyncio.sleep(1)  # 模拟关闭过程
    
    async def stop_health_monitor(self):
        """停止健康监控"""
        logger.info("正在停止健康监控...")
        # 实现健康监控停止逻辑
        await asyncio.sleep(1)  # 模拟停止过程
    
    async def shutdown(self):
        """执行系统关闭"""
        await self.graceful_shutdown.shutdown()

async def main():
    # 创建关闭管理器
    shutdown_manager = ShutdownManager()
    
    try:
        # 模拟系统运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号，开始关闭...")
        await shutdown_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main()) 