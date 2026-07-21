import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import os

from src.system.system_status import SystemStatusManager

@pytest.fixture
def system_status():
    """创建系统状态管理器实例"""
    return SystemStatusManager(
        name='test_status',
        config={
            'update_interval': 1,
            'components': ['trading', 'data', 'strategy', 'model'],
            'status_levels': ['normal', 'warning', 'error', 'critical'],
            'history_size': 100,
            'alert_channels': ['console', 'email']
        }
    )

class TestSystemStatus:
    """系统状态测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, system_status):
        """测试系统状态管理器初始化"""
        assert system_status.name == 'test_status'
        assert system_status.config['update_interval'] == 1
        assert len(system_status.config['components']) == 4
        assert len(system_status.config['status_levels']) == 4
        
    @pytest.mark.asyncio
    async def test_start_monitoring(self, system_status):
        """测试启动状态监控"""
        # 启动监控
        success = await system_status.start_monitoring()
        
        # 验证启动结果
        assert success is True
        assert system_status.is_monitoring() is True
        
    @pytest.mark.asyncio
    async def test_stop_monitoring(self, system_status):
        """测试停止状态监控"""
        # 启动监控
        await system_status.start_monitoring()
        
        # 停止监控
        success = await system_status.stop_monitoring()
        
        # 验证停止结果
        assert success is True
        assert system_status.is_monitoring() is False
        
    @pytest.mark.asyncio
    async def test_update_component_status(self, system_status):
        """测试更新组件状态"""
        # 更新组件状态
        success = await system_status.update_component_status(
            component='trading',
            status='normal',
            message='Trading system is running normally'
        )
        
        # 验证更新结果
        assert success is True
        status = system_status.get_component_status('trading')
        assert status['status'] == 'normal'
        assert status['message'] == 'Trading system is running normally'
        assert 'timestamp' in status
        
    @pytest.mark.asyncio
    async def test_get_system_status(self, system_status):
        """测试获取系统状态"""
        # 更新各个组件状态
        components = ['trading', 'data', 'strategy', 'model']
        for component in components:
            await system_status.update_component_status(
                component=component,
                status='normal',
                message=f'{component} is running normally'
            )
            
        # 获取系统状态
        status = system_status.get_system_status()
        
        # 验证状态
        assert isinstance(status, dict)
        assert 'overall_status' in status
        assert 'components' in status
        assert 'timestamp' in status
        assert status['overall_status'] == 'normal'
        
    @pytest.mark.asyncio
    async def test_get_status_history(self, system_status):
        """测试获取状态历史"""
        # 更新组件状态
        await system_status.update_component_status(
            component='trading',
            status='normal',
            message='Trading system is running normally'
        )
        
        # 获取状态历史
        history = system_status.get_status_history()
        
        # 验证历史
        assert isinstance(history, list)
        assert len(history) > 0
        assert isinstance(history[0], dict)
        assert 'component' in history[0]
        assert 'status' in history[0]
        assert 'timestamp' in history[0]
        
    @pytest.mark.asyncio
    async def test_check_alerts(self, system_status):
        """测试检查告警"""
        # 更新组件状态为错误
        await system_status.update_component_status(
            component='trading',
            status='error',
            message='Trading system error'
        )
        
        # 检查告警
        alerts = system_status.check_alerts()
        
        # 验证告警
        assert isinstance(alerts, list)
        assert len(alerts) > 0
        assert alerts[0]['component'] == 'trading'
        assert alerts[0]['status'] == 'error'
        assert 'timestamp' in alerts[0]
        
    @pytest.mark.asyncio
    async def test_get_status_report(self, system_status):
        """测试获取状态报告"""
        # 更新各个组件状态
        components = ['trading', 'data', 'strategy', 'model']
        for component in components:
            await system_status.update_component_status(
                component=component,
                status='normal',
                message=f'{component} is running normally'
            )
            
        # 获取状态报告
        report = system_status.get_status_report()
        
        # 验证报告
        assert isinstance(report, dict)
        assert 'summary' in report
        assert 'components' in report
        assert 'alerts' in report
        assert 'recommendations' in report
        
    @pytest.mark.asyncio
    async def test_export_status(self, system_status):
        """测试导出状态"""
        # 更新组件状态
        await system_status.update_component_status(
            component='trading',
            status='normal',
            message='Trading system is running normally'
        )
        
        # 导出状态
        export_file = 'test_status.json'
        success = await system_status.export_status(export_file)
        
        # 验证导出结果
        assert success is True
        assert os.path.exists(export_file)
        
    @pytest.mark.asyncio
    async def test_cleanup_history(self, system_status):
        """测试清理历史数据"""
        # 更新超过历史大小的状态
        for i in range(system_status.config['history_size'] + 10):
            await system_status.update_component_status(
                component='trading',
                status='normal',
                message=f'Status update {i}'
            )
            
        # 清理历史数据
        success = await system_status.cleanup_history()
        
        # 验证清理结果
        assert success is True
        assert len(system_status.get_status_history()) <= system_status.config['history_size']
        
    @pytest.mark.asyncio
    async def test_error_handling(self, system_status):
        """测试错误处理"""
        # 测试无效的组件
        with pytest.raises(ValueError):
            await system_status.update_component_status(
                component='invalid_component',
                status='normal',
                message='Test message'
            )
            
        # 测试无效的状态级别
        with pytest.raises(ValueError):
            await system_status.update_component_status(
                component='trading',
                status='invalid_status',
                message='Test message'
            )
            
        # 测试无效的更新间隔
        system_status.config['update_interval'] = -1
        with pytest.raises(ValueError):
            await system_status.start_monitoring()
            
    @pytest.mark.asyncio
    async def test_concurrent_status_updates(self, system_status):
        """测试并发状态更新"""
        # 并发更新组件状态
        tasks = []
        components = ['trading', 'data', 'strategy', 'model']
        for component in components:
            tasks.append(
                system_status.update_component_status(
                    component=component,
                    status='normal',
                    message=f'{component} is running normally'
                )
            )
            
        # 等待所有更新完成
        await asyncio.gather(*tasks)
        
        # 验证所有组件状态
        for component in components:
            status = system_status.get_component_status(component)
            assert status['status'] == 'normal'
            assert status['message'] == f'{component} is running normally' 