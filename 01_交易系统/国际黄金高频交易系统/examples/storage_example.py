import time
import random
from datetime import datetime, timedelta
from src.system.performance import PerformanceMetrics
from src.system.status_report import SystemStatusReport, SystemStatus, ComponentStatus
from src.system.alert import Alert, AlertLevel
from src.system.storage import MonitoringStorage
from src.system.logger import logger

def simulate_performance_metrics():
    """模拟生成性能指标"""
    return PerformanceMetrics(
        timestamp=datetime.now(),
        response_time=random.uniform(50, 200),
        throughput=random.randint(5, 20),
        error_rate=random.uniform(0, 0.1),
        queue_size=random.randint(0, 10),
        active_connections=random.randint(1, 5),
        memory_usage=random.uniform(50, 200),
        gc_stats={"collections": random.randint(0, 5)}
    )

def simulate_component_status():
    """模拟生成组件状态"""
    status = random.choice([SystemStatus.HEALTHY, SystemStatus.WARNING, SystemStatus.CRITICAL])
    components = ["database", "cache", "api", "queue"]
    component = random.choice(components)
    
    if status == SystemStatus.HEALTHY:
        message = f"{component}运行正常"
    elif status == SystemStatus.WARNING:
        message = f"{component}性能下降"
    else:
        message = f"{component}出现严重问题"
    
    return ComponentStatus(
        name=component,
        status=status,
        message=message,
        last_update=datetime.now(),
        metrics={"usage": random.uniform(0, 1)}
    )

def simulate_status_report(metrics, components):
    """模拟生成系统状态报告"""
    # 根据组件状态确定整体状态
    if any(c.status == SystemStatus.CRITICAL for c in components):
        overall_status = SystemStatus.CRITICAL
    elif any(c.status == SystemStatus.WARNING for c in components):
        overall_status = SystemStatus.WARNING
    else:
        overall_status = SystemStatus.HEALTHY
    
    return SystemStatusReport(
        timestamp=datetime.now(),
        overall_status=overall_status,
        components=components,
        performance_metrics=metrics,
        issues=None
    )

def simulate_alert(status_report):
    """模拟生成告警"""
    if status_report.overall_status == SystemStatus.CRITICAL:
        level = AlertLevel.CRITICAL
        title = "系统严重故障"
        message = "系统出现严重问题，需要立即处理"
    elif status_report.overall_status == SystemStatus.WARNING:
        level = AlertLevel.WARNING
        title = "系统警告"
        message = "系统性能下降，需要注意"
    else:
        level = AlertLevel.INFO
        title = "系统状态正常"
        message = "系统运行正常"
    
    return Alert(
        id=f"alert_{int(time.time())}",
        level=level,
        title=title,
        message=message,
        timestamp=datetime.now(),
        source="system_monitor",
        metadata={"report_id": str(status_report.timestamp)}
    )

def main():
    """主函数"""
    # 初始化存储管理器
    storage = MonitoringStorage("monitoring.db")
    
    try:
        # 模拟系统运行5分钟
        end_time = time.time() + 300  # 5分钟
        while time.time() < end_time:
            # 生成模拟数据
            metrics = simulate_performance_metrics()
            components = [simulate_component_status() for _ in range(3)]  # 模拟3个组件
            status_report = simulate_status_report(metrics, components)
            alert = simulate_alert(status_report)
            
            # 保存数据
            storage.save_performance_metrics(metrics)
            for component in components:
                storage.save_component_status(component)
            storage.save_status_report(status_report)
            storage.save_alert(alert)
            
            # 获取并显示历史数据
            logger.info("\n=== 系统监控数据 ===")
            
            # 显示最近的性能指标
            recent_metrics = storage.get_performance_metrics(limit=5)
            logger.info("\n最近的性能指标:")
            for m in recent_metrics:
                logger.info(f"时间: {m.timestamp}")
                logger.info(f"响应时间: {m.response_time:.2f}ms")
                logger.info(f"吞吐量: {m.throughput}")
                logger.info(f"错误率: {m.error_rate:.2%}")
            
            # 显示组件状态
            for component in components:
                statuses = storage.get_component_status(component_name=component.name, limit=1)
                if statuses:
                    status = statuses[0]
                    logger.info(f"\n组件 {status.name} 状态:")
                    logger.info(f"状态: {status.status}")
                    logger.info(f"消息: {status.message}")
                    logger.info(f"更新时间: {status.last_update}")
            
            # 显示最近的告警
            recent_alerts = storage.get_alerts(limit=5)
            logger.info("\n最近的告警:")
            for a in recent_alerts:
                logger.info(f"ID: {a.id}")
                logger.info(f"级别: {a.level}")
                logger.info(f"标题: {a.title}")
                logger.info(f"消息: {a.message}")
                logger.info(f"时间: {a.timestamp}")
            
            # 清理30天前的数据
            storage.cleanup_old_data(days=30)
            
            # 等待1秒
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
    finally:
        # 关闭数据库连接
        storage.close()

if __name__ == "__main__":
    main() 