import asyncio
import psutil
import time
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger
from .alert import Alert, AlertLevel, AlertManager

class SystemHealthMonitor:
    def __init__(self, alert_manager: AlertManager):
        self.components: Dict[str, Dict[str, Any]] = {}
        self.last_check: Dict[str, datetime] = {}
        self.alert_manager = alert_manager
        self.check_interval = 60  # 默认检查间隔（秒）
        self.is_running = False
    
    async def start(self):
        """启动健康监控"""
        self.is_running = True
        while self.is_running:
            await self.check_health()
            await asyncio.sleep(self.check_interval)
    
    async def stop(self):
        """停止健康监控"""
        self.is_running = False
    
    async def check_health(self):
        """检查系统健康状态"""
        try:
            # 检查系统资源
            await self.check_system_resources()
            
            # 检查数据库连接
            await self.check_database_connections()
            
            # 检查组件状态
            await self.check_component_status()
            
            # 检查网络连接
            await self.check_network_connections()
            
            # 检查磁盘空间
            await self.check_disk_space()
            
            # 更新最后检查时间
            self.last_check['last_check'] = datetime.now()
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            await self.alert_manager.create_alert(
                level=AlertLevel.ERROR,
                title="系统健康检查失败",
                message=f"健康检查过程中发生错误: {str(e)}",
                source="health_monitor"
            )
    
    async def check_system_resources(self):
        """检查系统资源使用情况"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.components['system_resources'] = {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'timestamp': datetime.now()
            }
            
            # 检查是否超过阈值
            if cpu_percent > 80:
                await self.alert_manager.create_alert(
                    level=AlertLevel.WARNING,
                    title="CPU使用率过高",
                    message=f"CPU使用率达到 {cpu_percent}%",
                    source="health_monitor"
                )
            
            if memory.percent > 80:
                await self.alert_manager.create_alert(
                    level=AlertLevel.WARNING,
                    title="内存使用率过高",
                    message=f"内存使用率达到 {memory.percent}%",
                    source="health_monitor"
                )
            
            if disk.percent > 80:
                await self.alert_manager.create_alert(
                    level=AlertLevel.WARNING,
                    title="磁盘使用率过高",
                    message=f"磁盘使用率达到 {disk.percent}%",
                    source="health_monitor"
                )
                
        except Exception as e:
            logger.error(f"系统资源检查失败: {str(e)}")
    
    async def check_database_connections(self):
        """检查数据库连接状态"""
        # 这里需要实现具体的数据库连接检查逻辑
        pass
    
    async def check_component_status(self):
        """检查各个组件状态"""
        # 这里需要实现具体的组件状态检查逻辑
        pass
    
    async def check_network_connections(self):
        """检查网络连接状态"""
        try:
            # 检查网络连接
            net_connections = psutil.net_connections()
            net_io = psutil.net_io_counters()
            
            self.components['network'] = {
                'connections': len(net_connections),
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"网络连接检查失败: {str(e)}")
    
    async def check_disk_space(self):
        """检查磁盘空间"""
        try:
            disk_partitions = psutil.disk_partitions()
            disk_usage = {}
            
            for partition in disk_partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    }
                except Exception as e:
                    logger.warning(f"无法获取分区 {partition.mountpoint} 的使用情况: {str(e)}")
            
            self.components['disk_space'] = {
                'partitions': disk_usage,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"磁盘空间检查失败: {str(e)}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态报告"""
        return {
            'components': self.components,
            'last_check': self.last_check,
            'is_running': self.is_running
        }
    
    def set_check_interval(self, interval: int):
        """设置检查间隔"""
        self.check_interval = interval

async def main():
    # 创建告警管理器
    alert_manager = AlertManager()
    
    # 创建健康监控器
    monitor = SystemHealthMonitor(alert_manager)
    
    try:
        # 启动监控
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("正在停止健康监控...")
        await monitor.stop()
    except Exception as e:
        logger.error(f"健康监控发生错误: {str(e)}")
        await monitor.stop()

if __name__ == "__main__":
    asyncio.run(main()) 