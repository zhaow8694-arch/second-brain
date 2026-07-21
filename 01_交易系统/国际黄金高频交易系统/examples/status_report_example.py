import time
import random
from datetime import datetime, timedelta
from src.system.performance import PerformanceCollector
from src.system.status_report import StatusReporter, SystemStatus
from loguru import logger

def simulate_component_status(status_reporter: StatusReporter):
    """模拟组件状态更新"""
    # 模拟数据库状态
    db_connections = random.randint(5, 20)
    db_status = SystemStatus.HEALTHY
    db_message = "数据库连接正常"
    if db_connections > 15:
        db_status = SystemStatus.WARNING
        db_message = "数据库连接数接近上限"
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
    # 创建性能指标收集器和状态报告生成器
    collector = PerformanceCollector(window_size=10)
    reporter = StatusReporter(collector)
    logger.info("系统状态报告生成器已创建")
    
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
                # 显示报告信息
                logger.info(f"\n系统状态报告 ({report.timestamp}):")
                logger.info(f"整体状态: {report.overall_status.value}")
                
                if report.issues:
                    logger.info("\n系统问题:")
                    for issue in report.issues:
                        logger.info(f"- {issue}")
                
                logger.info("\n组件状态:")
                for component in report.components:
                    logger.info(f"\n{component.name}:")
                    logger.info(f"  状态: {component.status.value}")
                    logger.info(f"  消息: {component.message}")
                    if component.metrics:
                        logger.info("  指标:")
                        for key, value in component.metrics.items():
                            logger.info(f"    {key}: {value}")
                
                if report.performance_metrics:
                    logger.info("\n性能指标:")
                    logger.info(f"  响应时间: {report.performance_metrics.response_time:.2f}ms")
                    logger.info(f"  吞吐量: {report.performance_metrics.throughput} 请求/秒")
                    logger.info(f"  错误率: {report.performance_metrics.error_rate:.2%}")
                    logger.info(f"  队列大小: {report.performance_metrics.queue_size}")
                    logger.info(f"  活动连接数: {report.performance_metrics.active_connections}")
                    logger.info(f"  内存使用量: {report.performance_metrics.memory_usage:.2f}MB")
                    
            time.sleep(1)  # 每秒更新一次
            
    except Exception as e:
        logger.error(f"系统状态报告生成过程中发生错误: {e}")
        raise
        
    finally:
        # 重置收集器和报告生成器
        collector.reset()
        reporter.reset()
        logger.info("系统状态报告生成器已重置")

if __name__ == "__main__":
    main() 