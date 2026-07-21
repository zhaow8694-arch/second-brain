import pytest
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List

from src.system.performance_monitor import PerformanceMonitor

@pytest.fixture
def performance_monitor():
    """创建性能监控器实例"""
    return PerformanceMonitor(
        name='test_monitor',
        config={
            'monitor_interval': 1,
            'metrics': ['cpu', 'memory', 'disk', 'network'],
            'alert_thresholds': {
                'cpu': 80,
                'memory': 80,
                'disk': 80,
                'network': 1000
            },
            'alert_channels': ['console', 'email'],
            'history_size': 100
        }
    )

class TestPerformanceMonitor:
    """性能监控测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, performance_monitor):
        """测试性能监控器初始化"""
        assert performance_monitor.name == 'test_monitor'
        assert performance_monitor.config['monitor_interval'] == 1
        assert len(performance_monitor.config['metrics']) == 4
        assert 'alert_thresholds' in performance_monitor.config
        
    @pytest.mark.asyncio
    async def test_start_monitoring(self, performance_monitor):
        """测试启动监控"""
        # 启动监控
        success = await performance_monitor.start_monitoring()
        
        # 验证启动结果
        assert success is True
        assert performance_monitor.is_monitoring() is True
        
    @pytest.mark.asyncio
    async def test_stop_monitoring(self, performance_monitor):
        """测试停止监控"""
        # 启动监控
        await performance_monitor.start_monitoring()
        
        # 停止监控
        success = await performance_monitor.stop_monitoring()
        
        # 验证停止结果
        assert success is True
        assert performance_monitor.is_monitoring() is False
        
    @pytest.mark.asyncio
    async def test_collect_metrics(self, performance_monitor):
        """测试收集指标"""
        # 收集指标
        metrics = await performance_monitor.collect_metrics()
        
        # 验证指标
        assert isinstance(metrics, dict)
        assert 'cpu' in metrics
        assert 'memory' in metrics
        assert 'disk' in metrics
        assert 'network' in metrics
        assert isinstance(metrics['cpu'], float)
        assert isinstance(metrics['memory'], float)
        assert isinstance(metrics['disk'], float)
        assert isinstance(metrics['network'], dict)
        
    @pytest.mark.asyncio
    async def test_monitor_metrics(self, performance_monitor):
        """测试监控指标"""
        # 启动监控
        await performance_monitor.start_monitoring()
        
        # 等待一段时间收集数据
        await asyncio.sleep(2)
        
        # 获取监控数据
        monitoring_data = performance_monitor.get_monitoring_data()
        
        # 验证监控数据
        assert isinstance(monitoring_data, list)
        assert len(monitoring_data) > 0
        assert isinstance(monitoring_data[0], dict)
        assert 'timestamp' in monitoring_data[0]
        assert 'metrics' in monitoring_data[0]
        
    @pytest.mark.asyncio
    async def test_check_alerts(self, performance_monitor):
        """测试检查告警"""
        # 启动监控
        await performance_monitor.start_monitoring()
        
        # 模拟高负载
        for _ in range(10):
            _ = [i * i for i in range(10000)]
            await asyncio.sleep(0.1)
            
        # 检查告警
        alerts = performance_monitor.check_alerts()
        
        # 验证告警
        assert isinstance(alerts, list)
        if len(alerts) > 0:
            assert 'level' in alerts[0]
            assert 'message' in alerts[0]
            assert 'timestamp' in alerts[0]
            
    @pytest.mark.asyncio
    async def test_get_performance_report(self, performance_monitor):
        """测试获取性能报告"""
        # 启动监控
        await performance_monitor.start_monitoring()
        
        # 等待一段时间收集数据
        await asyncio.sleep(2)
        
        # 获取性能报告
        report = performance_monitor.get_performance_report()
        
        # 验证报告
        assert isinstance(report, dict)
        assert 'summary' in report
        assert 'metrics' in report
        assert 'alerts' in report
        assert 'recommendations' in report
        
    @pytest.mark.asyncio
    async def test_export_metrics(self, performance_monitor):
        """测试导出指标"""
        # 启动监控
        await performance_monitor.start_monitoring()
        
        # 等待一段时间收集数据
        await asyncio.sleep(2)
        
        # 导出指标
        export_file = 'test_metrics.csv'
        success = await performance_monitor.export_metrics(export_file)
        
        # 验证导出结果
        assert success is True
        assert os.path.exists(export_file)
        
    @pytest.mark.asyncio
    async def test_cleanup_history(self, performance_monitor):
        """测试清理历史数据"""
        # 启动监控
        await performance_monitor.start_monitoring()
        
        # 等待收集超过历史大小的数据
        await asyncio.sleep(performance_monitor.config['history_size'] + 1)
        
        # 清理历史数据
        success = await performance_monitor.cleanup_history()
        
        # 验证清理结果
        assert success is True
        assert len(performance_monitor.get_monitoring_data()) <= performance_monitor.config['history_size']
        
    @pytest.mark.asyncio
    async def test_error_handling(self, performance_monitor):
        """测试错误处理"""
        # 测试无效的监控间隔
        performance_monitor.config['monitor_interval'] = -1
        with pytest.raises(ValueError):
            await performance_monitor.start_monitoring()
            
        # 测试无效的指标
        performance_monitor.config['metrics'] = ['invalid_metric']
        with pytest.raises(ValueError):
            await performance_monitor.collect_metrics()
            
        # 测试无效的告警阈值
        performance_monitor.config['alert_thresholds']['cpu'] = -1
        with pytest.raises(ValueError):
            performance_monitor.check_alerts()
            
    @pytest.mark.asyncio
    async def test_concurrent_monitoring(self, performance_monitor):
        """测试并发监控"""
        # 启动监控
        await performance_monitor.start_monitoring()
        
        # 并发收集指标
        import asyncio
        tasks = []
        for _ in range(5):
            tasks.append(performance_monitor.collect_metrics())
            
        # 等待所有指标收集完成
        results = await asyncio.gather(*tasks)
        
        # 验证结果
        assert len(results) == 5
        assert all(isinstance(result, dict) for result in results)
        assert all('cpu' in result for result in results)
        assert all('memory' in result for result in results) 