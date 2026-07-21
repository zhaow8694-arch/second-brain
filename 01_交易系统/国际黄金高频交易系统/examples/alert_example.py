import time
import random
from datetime import datetime, timedelta
from src.system.performance import PerformanceCollector
from src.system.status_report import StatusReporter, SystemStatus
from src.system.alert import AlertManager, AlertLevel
from loguru import logger

def console_notifier(alert):
    """控制台通知器"""
    logger.info(f"\n收到告警通知:")
    logger.info(f"ID: {alert.id}")
    logger.info(f"级别: {alert.level.value}")
    logger.info(f"标题: {alert.title}")
    logger.info(f"消息: {alert.message}")
    logger.info(f"来源: {alert.source}")
    logger.info(f"时间: {alert.timestamp}")
    if alert.metadata:
        logger.info("元数据:")
        for key, value in alert.metadata.items():
            logger.info(f"  {key}: {value}")

def simulate_component_status(status_reporter: StatusReporter):
    """模拟组件状态更新"""
    # 模拟数据库状态
    db_connections = random.randint(5, 20)
    db_status = SystemStatus.HEALTHY
    db_message = "数据库连接正常"
    if db_connections > 15:
        db_status = SystemStatus.WARNING
        db_message = "数据库连接数接近上限"
    elif db_connections > 18:
        db_status = SystemStatus.CRITICAL
        db_message = "数据库连接数超限"
    status_reporter.update_component_status(
        name="database",
        status=db_status,
        message=db_message,
        metrics={"connections": db_connections}
    )
    
    # 模拟缓存状态
    cache_usage = random.uniform(0.5, 0.9)
    cache_status = SystemStatus.HEALTHY
    cache_message = "缓存使用正常"
    if cache_usage > 0.8:
        cache_status = SystemStatus.WARNING
        cache_message = "缓存使用率过高"
    elif cache_usage > 0.9:
        cache_status = SystemStatus.CRITICAL
        cache_message = "缓存使用率超限"
    status_reporter.update_component_status(
        name="cache",
        status=cache_status,
        message=cache_message,
        metrics={"usage": cache_usage}
    )
    
    # 模拟API状态
    api_latency = random.uniform(50, 500)
    api_status = SystemStatus.HEALTHY
    api_message = "API响应正常"
    if api_latency > 300:
        api_status = SystemStatus.WARNING
        api_message = "API响应延迟"
    elif api_latency > 400:
        api_status = SystemStatus.CRITICAL
        api_message = "API响应超时"
    status_reporter.update_component_status(
        name="api",
        status=api_status,
        message=api_message,
        metrics={"latency": api_latency}
    )

def main():
    # 创建性能指标收集器、状态报告生成器和告警管理器
    collector = PerformanceCollector(window_size=10)
    reporter = StatusReporter(collector)
    alert_manager = AlertManager()
    
    # 添加告警通知器
    alert_manager.add_notifier(AlertLevel.INFO, console_notifier)
    alert_manager.add_notifier(AlertLevel.WARNING, console_notifier)
    alert_manager.add_notifier(AlertLevel.ERROR, console_notifier)
    alert_manager.add_notifier(AlertLevel.CRITICAL, console_notifier)
    
    logger.info("系统监控和告警系统已启动")
    
    try:
        # 模拟系统运行5分钟
        logger.info("开始模拟系统运行...")
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=5)
        
        while datetime.now() < end_time:
            # 模拟请求
            response_time = random.uniform(50, 500)
            collector.record_request(response_time, random.random() < 0.05)
            
            # 收集性能指标
            collector.collect_metrics(
                queue_size=random.randint(0, 100),
                active_connections=random.randint(0, 50),
                memory_usage=random.uniform(100, 500),
                gc_stats={
                    "collections": random.randint(0, 100),
                    "collected": random.randint(0, 1000),
                    "uncollectable": random.randint(0, 10)
                }
            )
            
            # 更新组件状态
            simulate_component_status(reporter)
            
            # 生成状态报告
            report = reporter.generate_report()
            if report:
                # 处理状态报告
                alert_manager.process_status_report(report)
                
                # 显示当前告警统计
                active_alerts = alert_manager.get_active_alerts()
                if active_alerts:
                    logger.info(f"\n当前活动告警数: {len(active_alerts)}")
                    for level in AlertLevel:
                        alerts = alert_manager.get_alerts_by_level(level)
                        if alerts:
                            logger.info(f"{level.value}级别告警: {len(alerts)}个")
                    
            time.sleep(1)  # 每秒更新一次
            
    except Exception as e:
        logger.error(f"系统监控和告警过程中发生错误: {e}")
        raise
        
    finally:
        # 重置所有组件
        collector.reset()
        reporter.reset()
        alert_manager.clear_alerts()
        logger.info("系统监控和告警系统已重置")

if __name__ == "__main__":
    main() 