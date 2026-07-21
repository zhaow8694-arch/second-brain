import time
import random
from datetime import datetime, timedelta
from src.system.performance import PerformanceCollector
from loguru import logger

def simulate_request(collector: PerformanceCollector):
    """模拟请求处理"""
    # 模拟响应时间（50-500ms）
    response_time = random.uniform(50, 500)
    
    # 模拟错误（5%概率）
    is_error = random.random() < 0.05
    
    # 记录请求
    collector.record_request(response_time, is_error)
    
    # 模拟处理时间
    time.sleep(response_time / 1000)  # 转换为秒

def main():
    # 创建性能指标收集器
    collector = PerformanceCollector(window_size=10)
    logger.info("性能指标收集器已创建")
    
    try:
        # 模拟系统运行5分钟
        logger.info("开始模拟系统运行...")
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=5)
        
        while datetime.now() < end_time:
            # 模拟请求
            simulate_request(collector)
            
            # 收集性能指标
            metrics = collector.collect_metrics(
                queue_size=random.randint(0, 100),
                active_connections=random.randint(0, 50),
                memory_usage=random.uniform(100, 500),
                gc_stats={
                    "collections": random.randint(0, 100),
                    "collected": random.randint(0, 1000),
                    "uncollectable": random.randint(0, 10)
                }
            )
            
            if metrics:
                # 显示指标数据
                logger.info(f"\n性能指标 ({metrics.timestamp}):")
                logger.info(f"响应时间: {metrics.response_time:.2f}ms")
                logger.info(f"吞吐量: {metrics.throughput} 请求/秒")
                logger.info(f"错误率: {metrics.error_rate:.2%}")
                logger.info(f"队列大小: {metrics.queue_size}")
                logger.info(f"活动连接数: {metrics.active_connections}")
                logger.info(f"内存使用量: {metrics.memory_usage:.2f}MB")
                logger.info("GC统计:")
                for key, value in metrics.gc_stats.items():
                    logger.info(f"  {key}: {value}")
                    
            # 每5秒显示一次统计摘要
            if int(time.time()) % 5 == 0:
                summary = collector.get_metrics_summary()
                logger.info("\n性能统计摘要:")
                for key, value in summary.items():
                    logger.info(f"{key}: {value}")
                    
            time.sleep(0.1)  # 控制请求频率
            
        # 显示历史记录统计
        logger.info("\n历史记录统计:")
        history = collector.metrics_history
        if history:
            logger.info(f"总记录数: {len(history)}")
            logger.info(f"时间范围: {history[0].timestamp} 到 {history[-1].timestamp}")
            
            # 计算平均响应时间
            avg_response_time = sum(m.response_time for m in history) / len(history)
            logger.info(f"平均响应时间: {avg_response_time:.2f}ms")
            
            # 计算平均吞吐量
            avg_throughput = sum(m.throughput for m in history) / len(history)
            logger.info(f"平均吞吐量: {avg_throughput:.2f} 请求/秒")
            
            # 计算平均错误率
            avg_error_rate = sum(m.error_rate for m in history) / len(history)
            logger.info(f"平均错误率: {avg_error_rate:.2%}")
            
    except Exception as e:
        logger.error(f"性能指标收集过程中发生错误: {e}")
        raise
        
    finally:
        # 重置收集器
        collector.reset()
        logger.info("性能指标收集器已重置")

if __name__ == "__main__":
    main() 