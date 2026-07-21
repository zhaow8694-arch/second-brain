import pytest
import numpy as np
from datetime import datetime, timedelta
from strategy.statistical_arbitrage import StatisticalArbitrageStrategy
from models.deepseek_interface import Order, MarketState, Position

class TestStatisticalArbitrageStrategy:
    """统计套利策略测试类"""
    
    @pytest.fixture
    def strategy(self):
        """创建策略实例"""
        return StatisticalArbitrageStrategy(
            lookback_period=20,
            entry_threshold=2.0,
            exit_threshold=1.0,
            max_position_size=10.0,
            min_profit_threshold=0.001
        )
    
    @pytest.fixture
    def test_instruments(self):
        """创建测试交易对"""
        return [
            {
                'symbol': 'GOLD',
                'price': 50000.0,
                'volatility': 0.01
            },
            {
                'symbol': 'SILVER',
                'price': 25.0,
                'volatility': 0.015
            }
        ]
    
    async def test_initialization(self, strategy):
        """测试策略初始化"""
        assert strategy.lookback_period == 20
        assert strategy.entry_threshold == 2.0
        assert strategy.exit_threshold == 1.0
        assert strategy.max_position_size == 10.0
        assert strategy.min_profit_threshold == 0.001
        assert strategy.positions == {}
        assert strategy.trade_history == []
    
    async def test_correlation_calculation(self, strategy, test_instruments):
        """测试相关性计算"""
        # 生成历史数据
        prices = []
        for _ in range(30):
            gold_price = test_instruments[0]['price'] * (1 + np.random.normal(0, 0.01))
            silver_price = test_instruments[1]['price'] * (1 + np.random.normal(0, 0.015))
            prices.append({
                'GOLD': gold_price,
                'SILVER': silver_price
            })
        
        # 计算相关性
        correlation = await strategy.calculate_correlation(
            prices,
            'GOLD',
            'SILVER'
        )
        
        # 验证相关性
        assert -1 <= correlation <= 1
        assert not np.isnan(correlation)
    
    async def test_zscore_calculation(self, strategy, test_instruments):
        """测试Z分数计算"""
        # 生成价格序列
        gold_prices = []
        silver_prices = []
        for _ in range(30):
            gold_prices.append(test_instruments[0]['price'] * (1 + np.random.normal(0, 0.01)))
            silver_prices.append(test_instruments[1]['price'] * (1 + np.random.normal(0, 0.015)))
        
        # 计算Z分数
        zscore = await strategy.calculate_zscore(
            gold_prices,
            silver_prices
        )
        
        # 验证Z分数
        assert not np.isnan(zscore)
        assert isinstance(zscore, float)
    
    async def test_signal_generation(self, strategy, test_instruments):
        """测试信号生成"""
        # 生成市场状态
        market_state = MarketState(
            timestamp=datetime.now(),
            prices={
                'GOLD': test_instruments[0]['price'],
                'SILVER': test_instruments[1]['price']
            },
            volumes={
                'GOLD': 1000.0,
                'SILVER': 5000.0
            },
            volatility={
                'GOLD': test_instruments[0]['volatility'],
                'SILVER': test_instruments[1]['volatility']
            }
        )
        
        # 生成信号
        signal = await strategy.generate_signal(market_state)
        
        # 验证信号
        assert signal is not None
        assert 'action' in signal
        assert 'confidence' in signal
        assert 'target_price' in signal
        assert 0 <= signal['confidence'] <= 1
    
    async def test_position_management(self, strategy, test_instruments):
        """测试仓位管理"""
        # 创建初始仓位
        position = Position(
            instrument_id='GOLD',
            quantity=1.0,
            entry_price=test_instruments[0]['price'],
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
            price=test_instruments[0]['price'] * 1.01
        )
        
        # 验证更新
        assert strategy.positions['GOLD'].quantity == 2.0
        assert strategy.positions['GOLD'].entry_price == test_instruments[0]['price'] * 1.01
    
    async def test_risk_management(self, strategy, test_instruments):
        """测试风险管理"""
        # 创建大仓位
        position = Position(
            instrument_id='GOLD',
            quantity=20.0,  # 超过最大仓位限制
            entry_price=test_instruments[0]['price'],
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
                entry_price=test_instruments[0]['price'],
                timestamp=datetime.now()
            )
        )
        
        # 模拟大幅亏损
        await strategy.update_position(
            'GOLD',
            quantity=1.0,
            price=test_instruments[0]['price'] * 0.95  # 5%亏损
        )
        
        # 验证止损触发
        assert await strategy.check_stop_loss('GOLD')
    
    async def test_performance_metrics(self, strategy, test_instruments):
        """测试性能指标"""
        # 添加交易历史
        trade = {
            'timestamp': datetime.now(),
            'instrument_id': 'GOLD',
            'side': 'BUY',
            'quantity': 1.0,
            'price': test_instruments[0]['price'],
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
    
    async def test_strategy_adaptation(self, strategy, test_instruments):
        """测试策略适应性"""
        # 初始市场状态
        initial_state = MarketState(
            timestamp=datetime.now(),
            prices={
                'GOLD': test_instruments[0]['price'],
                'SILVER': test_instruments[1]['price']
            },
            volumes={'GOLD': 1000.0, 'SILVER': 5000.0},
            volatility={
                'GOLD': test_instruments[0]['volatility'],
                'SILVER': test_instruments[1]['volatility']
            }
        )
        
        # 获取初始信号
        initial_signal = await strategy.generate_signal(initial_state)
        
        # 模拟市场变化
        volatile_state = MarketState(
            timestamp=datetime.now() + timedelta(hours=1),
            prices={
                'GOLD': test_instruments[0]['price'] * 1.02,
                'SILVER': test_instruments[1]['price'] * 1.03
            },
            volumes={'GOLD': 2000.0, 'SILVER': 6000.0},
            volatility={
                'GOLD': test_instruments[0]['volatility'] * 2,
                'SILVER': test_instruments[1]['volatility'] * 2
            }
        )
        
        # 获取新信号
        new_signal = await strategy.generate_signal(volatile_state)
        
        # 验证策略适应性
        assert new_signal['confidence'] < initial_signal['confidence']
        assert abs(new_signal['target_price'] - volatile_state.prices['GOLD']) > \
               abs(initial_signal['target_price'] - initial_state.prices['GOLD']) 