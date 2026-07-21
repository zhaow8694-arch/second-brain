import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.interface.strategy_interface import StrategyInterface
from src.strategy.base_strategy import BaseStrategy

class TestStrategy(BaseStrategy):
    """测试策略类"""
    def __init__(self, name: str, parameters: Dict):
        super().__init__(name, parameters)
        
    async def initialize(self):
        """初始化策略"""
        pass
        
    async def on_market_data(self, market_data: Dict):
        """处理市场数据"""
        pass
        
    async def on_order_update(self, order_update: Dict):
        """处理订单更新"""
        pass
        
    async def on_position_update(self, position_update: Dict):
        """处理持仓更新"""
        pass

@pytest.fixture
def strategy_interface():
    """创建策略接口实例"""
    return StrategyInterface(
        interface_name='test_interface',
        config={
            'max_strategies': 10,
            'max_positions_per_strategy': 5,
            'risk_limits': {
                'max_drawdown': 0.1,
                'max_position_size': 1.0,
                'max_leverage': 2.0
            }
        }
    )

@pytest.fixture
def test_strategy():
    """创建测试策略实例"""
    return TestStrategy(
        name='test_strategy',
        parameters={
            'symbol': 'BTC/USDT',
            'timeframe': '1h',
            'position_size': 0.1,
            'stop_loss': 0.02,
            'take_profit': 0.05
        }
    )

@pytest.fixture
def sample_market_data():
    """生成样本市场数据"""
    n_samples = 1000
    timestamps = pd.date_range(start='2024-01-01', periods=n_samples, freq='1min')
    
    data = pd.DataFrame({
        'timestamp': timestamps,
        'open': np.random.normal(50000, 1000, n_samples),
        'high': np.random.normal(50100, 1000, n_samples),
        'low': np.random.normal(49900, 1000, n_samples),
        'close': np.random.normal(50000, 1000, n_samples),
        'volume': np.random.normal(100, 20, n_samples),
        'trades': np.random.randint(100, 1000, n_samples)
    })
    
    return data

class TestStrategyInterface:
    """策略接口测试类"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, strategy_interface):
        """测试接口初始化"""
        assert strategy_interface.interface_name == 'test_interface'
        assert strategy_interface.config['max_strategies'] == 10
        assert strategy_interface.config['max_positions_per_strategy'] == 5
        assert 'risk_limits' in strategy_interface.config
        
    @pytest.mark.asyncio
    async def test_register_strategy(self, strategy_interface, test_strategy):
        """测试策略注册"""
        # 注册策略
        success = await strategy_interface.register_strategy(test_strategy)
        
        # 验证注册结果
        assert success is True
        assert test_strategy.name in strategy_interface.get_registered_strategies()
        
    @pytest.mark.asyncio
    async def test_unregister_strategy(self, strategy_interface, test_strategy):
        """测试策略注销"""
        # 注册策略
        await strategy_interface.register_strategy(test_strategy)
        
        # 注销策略
        success = await strategy_interface.unregister_strategy(test_strategy.name)
        
        # 验证注销结果
        assert success is True
        assert test_strategy.name not in strategy_interface.get_registered_strategies()
        
    @pytest.mark.asyncio
    async def test_update_strategy_parameters(self, strategy_interface, test_strategy):
        """测试更新策略参数"""
        # 注册策略
        await strategy_interface.register_strategy(test_strategy)
        
        # 更新参数
        new_parameters = {
            'symbol': 'ETH/USDT',
            'timeframe': '4h',
            'position_size': 0.2,
            'stop_loss': 0.03,
            'take_profit': 0.06
        }
        
        success = await strategy_interface.update_strategy_parameters(
            strategy_name=test_strategy.name,
            parameters=new_parameters
        )
        
        # 验证更新结果
        assert success is True
        assert strategy_interface.get_strategy_parameters(test_strategy.name) == new_parameters
        
    @pytest.mark.asyncio
    async def test_start_strategy(self, strategy_interface, test_strategy):
        """测试启动策略"""
        # 注册策略
        await strategy_interface.register_strategy(test_strategy)
        
        # 启动策略
        success = await strategy_interface.start_strategy(test_strategy.name)
        
        # 验证启动结果
        assert success is True
        assert strategy_interface.is_strategy_running(test_strategy.name) is True
        
    @pytest.mark.asyncio
    async def test_stop_strategy(self, strategy_interface, test_strategy):
        """测试停止策略"""
        # 注册并启动策略
        await strategy_interface.register_strategy(test_strategy)
        await strategy_interface.start_strategy(test_strategy.name)
        
        # 停止策略
        success = await strategy_interface.stop_strategy(test_strategy.name)
        
        # 验证停止结果
        assert success is True
        assert strategy_interface.is_strategy_running(test_strategy.name) is False
        
    @pytest.mark.asyncio
    async def test_process_market_data(self, strategy_interface, test_strategy, sample_market_data):
        """测试处理市场数据"""
        # 注册并启动策略
        await strategy_interface.register_strategy(test_strategy)
        await strategy_interface.start_strategy(test_strategy.name)
        
        # 处理市场数据
        for _, row in sample_market_data.iterrows():
            market_data = row.to_dict()
            await strategy_interface.process_market_data(test_strategy.name, market_data)
            
        # 验证数据处理
        assert strategy_interface.get_strategy_status(test_strategy.name)['last_update'] is not None
        
    @pytest.mark.asyncio
    async def test_get_strategy_status(self, strategy_interface, test_strategy):
        """测试获取策略状态"""
        # 注册并启动策略
        await strategy_interface.register_strategy(test_strategy)
        await strategy_interface.start_strategy(test_strategy.name)
        
        # 获取策略状态
        status = strategy_interface.get_strategy_status(test_strategy.name)
        
        # 验证状态信息
        assert isinstance(status, dict)
        assert 'is_running' in status
        assert 'last_update' in status
        assert 'positions' in status
        assert 'performance' in status
        
    @pytest.mark.asyncio
    async def test_get_strategy_performance(self, strategy_interface, test_strategy):
        """测试获取策略性能"""
        # 注册并启动策略
        await strategy_interface.register_strategy(test_strategy)
        await strategy_interface.start_strategy(test_strategy.name)
        
        # 获取策略性能
        performance = strategy_interface.get_strategy_performance(test_strategy.name)
        
        # 验证性能指标
        assert isinstance(performance, dict)
        assert 'total_return' in performance
        assert 'sharpe_ratio' in performance
        assert 'max_drawdown' in performance
        assert 'win_rate' in performance
        
    @pytest.mark.asyncio
    async def test_risk_management(self, strategy_interface, test_strategy):
        """测试风险管理"""
        # 注册并启动策略
        await strategy_interface.register_strategy(test_strategy)
        await strategy_interface.start_strategy(test_strategy.name)
        
        # 检查风险限制
        risk_limits = strategy_interface.get_risk_limits(test_strategy.name)
        
        # 验证风险限制
        assert isinstance(risk_limits, dict)
        assert 'max_drawdown' in risk_limits
        assert 'max_position_size' in risk_limits
        assert 'max_leverage' in risk_limits
        
    @pytest.mark.asyncio
    async def test_error_handling(self, strategy_interface):
        """测试错误处理"""
        # 测试注册不存在的策略
        with pytest.raises(ValueError):
            await strategy_interface.start_strategy('non_existent_strategy')
            
        # 测试重复注册策略
        test_strategy = TestStrategy('test_strategy', {})
        await strategy_interface.register_strategy(test_strategy)
        with pytest.raises(ValueError):
            await strategy_interface.register_strategy(test_strategy)
            
    @pytest.mark.asyncio
    async def test_concurrent_strategy_execution(self, strategy_interface):
        """测试并发策略执行"""
        # 创建多个策略
        strategies = []
        for i in range(3):
            strategy = TestStrategy(f'test_strategy_{i}', {})
            strategies.append(strategy)
            await strategy_interface.register_strategy(strategy)
            await strategy_interface.start_strategy(strategy.name)
            
        # 验证所有策略都在运行
        for strategy in strategies:
            assert strategy_interface.is_strategy_running(strategy.name) is True 