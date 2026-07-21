import time
from datetime import datetime, timedelta
from src.system.monitor import SystemMonitor
from loguru import logger

def main():
    # 创建系统监控器
    monitor = SystemMonitor(collect_interval=1.0)
    logger.info("系统监控器已创建")
    
    try:
        # 收集5次指标
        logger.info("开始收集系统指标...")
        for i in range(5):
            metrics = monitor.collect_metrics()
            if metrics:
                logger.info(f"第{i+1}次收集指标:")
                logger.info(f"  CPU使用率: {metrics.cpu_percent:.2f}%")
                logger.info(f"  内存使用率: {metrics.memory_percent:.2f}%")
                logger.info(f"  磁盘使用率: {metrics.disk_usage_percent:.2f}%")
                logger.info(f"  网络发送: {metrics.network_io_bytes_sent / 1024 / 1024:.2f} MB")
                logger.info(f"  网络接收: {metrics.network_io_bytes_recv / 1024 / 1024:.2f} MB")
                logger.info(f"  进程数: {metrics.process_count}")
                logger.info(f"  线程数: {metrics.thread_count}")
                logger.info("---")
            time.sleep(1.5)  # 等待1.5秒，确保超过收集间隔
            
        # 获取指标历史记录
        logger.info("获取指标历史记录...")
        history = monitor.metrics_history
        logger.info(f"共收集到 {len(history)} 条历史记录")
        
        # 获取最近1分钟的历史记录
        logger.info("获取最近1分钟的历史记录...")
        start_time = datetime.now() - timedelta(minutes=1)
        recent_history = monitor.get_metrics_history(start_time=start_time)
        logger.info(f"最近1分钟内有 {len(recent_history)} 条记录")
        
        # 获取最新指标
        logger.info("获取最新指标...")
        latest = monitor.get_latest_metrics()
        if latest:
            logger.info("最新指标:")
            logger.info(f"  CPU使用率: {latest.cpu_percent:.2f}%")
            logger.info(f"  内存使用率: {latest.memory_percent:.2f}%")
            logger.info(f"  磁盘使用率: {latest.disk_usage_percent:.2f}%")
            
        # 获取指标摘要
        logger.info("获取指标摘要...")
        summary = monitor.get_metrics_summary()
        logger.info("指标摘要:")
        for key, value in summary.items():
            logger.info(f"  {key}: {value}")
            
    except Exception as e:
        logger.error(f"系统监控过程中发生错误: {e}")
        raise
        
    finally:
        logger.info("系统监控示例结束")

if __name__ == "__main__":
    main() 