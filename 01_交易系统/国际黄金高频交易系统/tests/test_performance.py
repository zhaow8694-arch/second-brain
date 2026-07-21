import pytest
from datetime import datetime, timedelta
from src.system.performance import PerformanceCollector, PerformanceMetrics

@pytest.fixture
def collector():
    """创建测试用的性能指标收集器"""
    return PerformanceCollector(window_size=5)

def test_record_request(collector):
    """测试请求记录"""
    # 记录正常请求
    collector.record_request(100.0)  # 100ms响应时间
    collector.record_request(200.0)  # 200ms响应时间
    
    # 记录错误请求
    collector.record_request(300.0, is_error=True)  # 300ms响应时间，错误
    
    # 验证记录
    assert len(collector.request_times) == 3
    assert collector.total_requests == 3
    assert collector.error_count == 1
    
    # 验证滑动窗口
    for _ in range(4):
        collector.record_request(400.0)
    assert len(collector.request_times) == 5  # 窗口大小限制

def test_collect_metrics(collector):
    """测试指标收集"""
    # 记录一些请求
    collector.record_request(100.0)
    collector.record_request(200.0)
    collector.record_request(300.0, is_error=True)
    
    # 收集指标
    gc_stats = {
        "collections": 10,
        "collected": 1000,
        "uncollectable": 0
    }
    metrics = collector.collect_metrics(
        queue_size=10,
        active_connections=5,
        memory_usage=100.0,
        gc_stats=gc_stats
    )
    
    # 验证指标数据
    assert metrics is not None
    assert isinstance(metrics, PerformanceMetrics)
    assert metrics.response_time == 200.0  # (100 + 200 + 300) / 3
    assert metrics.throughput == 3
    assert metrics.error_rate == 1/3
    assert metrics.queue_size == 10
    assert metrics.active_connections == 5
    assert metrics.memory_usage == 100.0
    assert metrics.gc_stats == gc_stats

def test_metrics_history(collector):
    """测试指标历史记录"""
    # 收集多次指标
    for i in range(3):
        collector.record_request(100.0 * (i + 1))
        collector.collect_metrics(
            queue_size=i,
            active_connections=i,
            memory_usage=100.0 * (i + 1),
            gc_stats={"collections": i}
        )
    
    # 验证历史记录
    history = collector.metrics_history
    assert len(history) == 3
    assert all(isinstance(m, PerformanceMetrics) for m in history)
    
    # 验证时间顺序
    for i in range(1, len(history)):
        assert history[i].timestamp >= history[i-1].timestamp

def test_metrics_filtering(collector):
    """测试指标过滤"""
    # 收集一些指标
    for i in range(3):
        collector.record_request(100.0)
        collector.collect_metrics(
            queue_size=i,
            active_connections=i,
            memory_usage=100.0,
            gc_stats={"collections": i}
        )
    
    # 获取当前时间
    now = datetime.now()
    
    # 测试时间范围过滤
    start_time = now - timedelta(minutes=1)
    end_time = now + timedelta(minutes=1)
    
    filtered_history = collector.get_metrics_history(start_time, end_time)
    assert len(filtered_history) > 0
    assert all(start_time <= m.timestamp <= end_time for m in filtered_history)

def test_latest_metrics(collector):
    """测试获取最新指标"""
    # 收集指标
    collector.record_request(100.0)
    collector.collect_metrics(
        queue_size=10,
        active_connections=5,
        memory_usage=100.0,
        gc_stats={"collections": 1}
    )
    
    # 获取最新指标
    latest = collector.get_latest_metrics()
    
    # 验证最新指标
    assert latest is not None
    assert isinstance(latest, PerformanceMetrics)
    assert latest.response_time == 100.0
    assert latest.queue_size == 10

def test_metrics_summary(collector):
    """测试指标摘要"""
    # 收集指标
    collector.record_request(100.0)
    collector.collect_metrics(
        queue_size=10,
        active_connections=5,
        memory_usage=100.0,
        gc_stats={"collections": 1}
    )
    
    # 获取指标摘要
    summary = collector.get_metrics_summary()
    
    # 验证摘要数据
    assert isinstance(summary, dict)
    assert "response_time" in summary
    assert "throughput" in summary
    assert "error_rate" in summary
    assert "queue_size" in summary
    assert "active_connections" in summary
    assert "memory_usage" in summary

def test_reset(collector):
    """测试重置收集器"""
    # 收集一些数据
    collector.record_request(100.0)
    collector.collect_metrics(
        queue_size=10,
        active_connections=5,
        memory_usage=100.0,
        gc_stats={"collections": 1}
    )
    
    # 重置收集器
    collector.reset()
    
    # 验证重置结果
    assert len(collector.metrics_history) == 0
    assert len(collector.request_times) == 0
    assert collector.error_count == 0
    assert collector.total_requests == 0 