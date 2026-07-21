import pytest
import numpy as np
from datetime import datetime, timedelta
from strategy.trend_following import TrendFollowingStrategy
from models.deepseek_interface import Order, MarketState, Position

class TestTrendFollowingStrategy:
    """趋势跟踪策略测试类"""
    
    @pytest.fixture
    def strategy(self):
        """创建策略实例"""
        return TrendFollowingStrategy(
            short_window=10,
            long_window=30,
            entry_threshold=0.02,
            exit_threshold=0.01,
            max_position_size=10.0,
            stop_loss=0.05
        )
    
    @pytest.fixture
    def test_instrument(self):
        """创建测试交易品种"""
        return {
            'symbol': 'GOLD',
            'price': 50000.0,
            'volatility': 0.01
        }
    
    async def test_initialization(self, strategy):
        """测试策略初始化"""
        assert strategy.short_window == 10
        assert strategy.long_window == 30
        assert strategy.entry_threshold == 0.02
        assert strategy.exit_threshold == 0.01
        assert strategy.max_position_size == 10.0
        assert strategy.stop_loss == 0.05
        assert strategy.positions == {}
        assert strategy.trade_history == []
    
    async def test_moving_average_calculation(self, strategy, test_instrument):
        """测试移动平均计算"""
        # 生成价格序列
        prices = []
        for _ in range(40):
            prices.append(test_instrument['price'] * (1 + np.random.normal(0, 0.01)))
        
        # 计算移动平均
        short_ma = await strategy.calculate_moving_average(prices, strategy.short_window)
        long_ma = await strategy.calculate_moving_average(prices, strategy.long_window)
        
        # 验证移动平均
        assert len(short_ma) == len(prices) - strategy.short_window + 1
        assert len(long_ma) == len(prices) - strategy.long_window + 1
        assert not np.any(np.isnan(short_ma))
        assert not np.any(np.isnan(long_ma))
    
    async def test_trend_detection(self, strategy, test_instrument):
        """测试趋势检测"""
        # 生成趋势数据
        prices = []
        trend = 0.001  # 上升趋势
        for _ in range(40):
            prices.append(test_instrument['price'] * (1 + trend + np.random.normal(0, 0.01)))
            test_instrument['price'] = prices[-1]
        
        # 检测趋势
        trend_direction = await strategy.detect_trend(prices)
        
        # 验证趋势
        assert trend_direction in [-1, 0, 1]
        assert trend_direction == 1  # 应该检测到上升趋势
    
    async def test_signal_generation(self, strategy, test_instrument):
        """测试信号生成"""
        # 生成市场状态
        market_state = MarketState(
            timestamp=datetime.now(),
            prices={'GOLD': test_instrument['price']},
            volumes={'GOLD': 1000.0},
            volatility={'GOLD': test_instrument['volatility']}
        )
        
        # 生成信号
        signal = await strategy.generate_signal(market_state)
        
        # 验证信号
        assert signal is not None
        assert 'action' in signal
        assert 'confidence' in signal
        assert 'target_price' in signal
        assert 0 <= signal['confidence'] <= 1
    
    async def test_position_management(self, strategy, test_instrument):
        """测试仓位管理"""
        # 创建初始仓位
        position = Position(
            instrument_id='GOLD',
            quantity=1.0,
            entry_price=test_instrument['price'],
            timestamp=datetime.now()
        )
        
        # 添加仓位
        await strategy.add_position(position)
        
        # 验证仓位
        assert 'GOLD' in strategy.positions
        assert strategy.positions['GOLD'].quantity == 1.0
        
        # 更新仓位
        await strategy.update_position(
            'GOLD',
            quantity=2.0,
            price=test_instrument['price'] * 1.01
        )
        
        # 验证更新
        assert strategy.positions['GOLD'].quantity == 2.0
        assert strategy.positions['GOLD'].entry_price == test_instrument['price'] * 1.01
    
    async def test_risk_management(self, strategy, test_instrument):
        """测试风险管理"""
        # 创建大仓位
        position = Position(
            instrument_id='GOLD',
            quantity=20.0,  # 超过最大仓位限制
            entry_price=test_instrument['price'],
            timestamp=datetime.now()
        )
        
        # 验证仓位限制
        with pytest.raises(ValueError):
            await strategy.add_position(position)
        
        # 验证止损
        await strategy.add_position(
            Position(
                instrument_id='GOLD',
                quantity=1.0,
                entry_price=test_instrument['price'],
                timestamp=datetime.now()
            )
        )
        
        # 模拟大幅亏损
        await strategy.update_position(
            'GOLD',
            quantity=1.0,
            price=test_instrument['price'] * 0.94  # 6%亏损
        )
        
        # 验证止损触发
        assert await strategy.check_stop_loss('GOLD')
    
    async def test_performance_metrics(self, strategy, test_instrument):
        """测试性能指标"""
        # 添加交易历史
        trade = {
            'timestamp': datetime.now(),
            'instrument_id': 'GOLD',
            'side': 'BUY',
            'quantity': 1.0,
            'price': test_instrument['price'],
            'profit': 100.0
        }
        strategy.trade_history.append(trade)
        
        # 计算性能指标
        metrics = await strategy.calculate_performance_metrics()
        
        # 验证指标
        assert 'total_trades' in metrics
        assert 'win_rate' in metrics
        assert 'profit_factor' in metrics
        assert 'sharpe_ratio' in metrics
        assert metrics['total_trades'] == 1
        assert 0 <= metrics['win_rate'] <= 1
    
    async def test_strategy_adaptation(self, strategy, test_instrument):
        """测试策略适应性"""
        # 初始市场状态
        initial_state = MarketState(
            timestamp=datetime.now(),
            prices={'GOLD': test_instrument['price']},
            volumes={'GOLD': 1000.0},
            volatility={'GOLD': test_instrument['volatility']}
        )
        
        # 获取初始信号
        initial_signal = await strategy.generate_signal(initial_state)
        
        # 模拟市场变化
        volatile_state = MarketState(
            timestamp=datetime.now() + timedelta(hours=1),
            prices={'GOLD': test_instrument['price'] * 1.02},
            volumes={'GOLD': 2000.0},
            volatility={'GOLD': test_instrument['volatility'] * 2}
        )
        
        # 获取新信号
        new_signal = await strategy.generate_signal(volatile_state)
        
        # 验证策略适应性
        assert new_signal['confidence'] < initial_signal['confidence']
        assert abs(new_signal['target_price'] - volatile_state.prices['GOLD']) > \
               abs(initial_signal['target_price'] - initial_state.prices['GOLD'])
    
    async def test_trend_reversal_detection(self, strategy, test_instrument):
        """测试趋势反转检测"""
        # 生成趋势反转数据
        prices = []
        trend = 0.001  # 初始上升趋势
        for i in range(40):
            if i > 20:  # 20点后趋势反转
                trend = -0.001
            prices.append(test_instrument['price'] * (1 + trend + np.random.normal(0, 0.01)))
            test_instrument['price'] = prices[-1]
        
        # 检测趋势反转
        reversal = await strategy.detect_trend_reversal(prices)
        
        # 验证趋势反转
        assert reversal is not None
        assert 'timestamp' in reversal
        assert 'direction' in reversal
        assert reversal['direction'] == -1  # 应该检测到下降趋势 