import time
from datetime import datetime
from src.system.monitor import SystemMonitor
from src.system.health_check import HealthChecker, HealthStatus
from loguru import logger

def main():
    # 创建系统监控器
    monitor = SystemMonitor(collect_interval=1.0)
    logger.info("系统监控器已创建")
    
    # 创建健康检查器
    health_checker = HealthChecker(monitor)
    logger.info("健康检查器已创建")
    
    try:
        # 显示当前阈值设置
        thresholds = health_checker.get_thresholds()
        logger.info("当前阈值设置:")
        logger.info("警告阈值:")
        for key, value in thresholds["warning"].items():
            logger.info(f"  {key}: {value}")
        logger.info("严重阈值:")
        for key, value in thresholds["critical"].items():
            logger.info(f"  {key}: {value}")
            
        # 执行5次健康检查
        logger.info("\n开始执行健康检查...")
        for i in range(5):
            # 收集指标
            monitor.collect_metrics()
            
            # 执行健康检查
            result = health_checker.check_health()
            
            # 显示检查结果
            logger.info(f"\n第{i+1}次健康检查结果:")
            logger.info(f"时间: {result.timestamp}")
            logger.info(f"状态: {result.status.value}")
            
            if result.metrics:
                logger.info("系统指标:")
                logger.info(f"  CPU使用率: {result.metrics.cpu_percent:.2f}%")
                logger.info(f"  内存使用率: {result.metrics.memory_percent:.2f}%")
                logger.info(f"  磁盘使用率: {result.metrics.disk_usage_percent:.2f}%")
                logger.info(f"  进程数: {result.metrics.process_count}")
                logger.info(f"  线程数: {result.metrics.thread_count}")
                
            if result.warnings:
                logger.warning("警告信息:")
                for warning in result.warnings:
                    logger.warning(f"  {warning}")
                    
            if result.errors:
                logger.error("错误信息:")
                for error in result.errors:
                    logger.error(f"  {error}")
                    
            # 根据状态执行相应操作
            if result.status == HealthStatus.CRITICAL:
                logger.error("系统状态严重，需要立即处理！")
            elif result.status == HealthStatus.WARNING:
                logger.warning("系统状态异常，需要注意！")
            else:
                logger.info("系统状态正常")
                
            logger.info("---")
            time.sleep(2.0)  # 等待2秒后继续下一次检查
            
        # 更新阈值设置示例
        logger.info("\n更新阈值设置...")
        new_warning_thresholds = {
            "cpu_percent": 75.0,
            "memory_percent": 75.0
        }
        new_critical_thresholds = {
            "cpu_percent": 85.0,
            "memory_percent": 85.0
        }
        health_checker.update_thresholds(
            warning_thresholds=new_warning_thresholds,
            critical_thresholds=new_critical_thresholds
        )
        
        # 显示更新后的阈值设置
        thresholds = health_checker.get_thresholds()
        logger.info("更新后的阈值设置:")
        logger.info("警告阈值:")
        for key, value in thresholds["warning"].items():
            logger.info(f"  {key}: {value}")
        logger.info("严重阈值:")
        for key, value in thresholds["critical"].items():
            logger.info(f"  {key}: {value}")
            
    except Exception as e:
        logger.error(f"健康检查过程中发生错误: {e}")
        raise
        
    finally:
        logger.info("健康检查示例结束")

if __name__ == "__main__":
    main() 