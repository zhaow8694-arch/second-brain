import pytest
import numpy as np
from datetime import datetime
from execution.price_calculator import DynamicPriceCalculator
from models.deepseek_interface import Order, PriceRange, MarketDepthInfo

class TestDynamicPriceCalculator:
    """动态价格计算器测试类"""
    
    @pytest.fixture
    def calculator(self):
        """创建计算器实例"""
        return DynamicPriceCalculator(
            max_price_deviation=0.01,
            confidence_threshold=0.7,
            depth_impact_factor=0.5,
            urgency_multiplier=1.0
        )
    
    @pytest.fixture
    def test_order(self):
        """创建测试订单"""
        return Order(
            instrument_id="GOLD",
            order_type="LIMIT",
            side="BUY",
            quantity=1.0,
            price=50000.0,
            timestamp=datetime.now()
        )
    
    async def test_basic_price_calculation(self, calculator, test_order, mock_market_state):
        """测试基本价格计算"""
        # 计算买入订单的价格
        buy_price = await calculator.calculate_limit_price(
            test_order,
            mock_market_state
        )
        
        # 验证买入价格
        assert isinstance(buy_price, PriceRange)
        assert buy_price.optimal_price <= mock_market_state['ask_price']
        assert buy_price.min_price <= buy_price.optimal_price <= buy_price.max_price
        
        # 测试卖出订单
        test_order.side = "SELL"
        sell_price = await calculator.calculate_limit_price(
            test_order,
            mock_market_state
        )
        
        # 验证卖出价格
        assert sell_price.optimal_price >= mock_market_state['bid_price']
        assert sell_price.min_price <= sell_price.optimal_price <= sell_price.max_price
    
    async def test_depth_impact(self, calculator, test_order, order_book):
        """测试深度影响"""
        # 创建市场深度信息
        depth_info = MarketDepthInfo(
            total_bid_volume=sum(order_book['bid_volumes']),
            total_ask_volume=sum(order_book['ask_volumes']),
            bid_depth=order_book['bid_volumes'],
            ask_depth=order_book['ask_volumes'],
            weighted_bid_price=np.average(
                order_book['bid_prices'],
                weights=order_book['bid_volumes']
            ),
            weighted_ask_price=np.average(
                order_book['ask_prices'],
                weights=order_book['ask_volumes']
            )
        )
        
        # 计算小订单价格
        small_order = test_order
        small_price = await calculator.calculate_with_depth(
            small_order,
            depth_info
        )
        
        # 计算大订单价格
        large_order = test_order
        large_order.quantity = 10.0
        large_price = await calculator.calculate_with_depth(
            large_order,
            depth_info
        )
        
        # 验证深度影响
        assert large_price.price_impact > small_price.price_impact
        assert large_price.confidence < small_price.confidence
    
    async def test_urgency_impact(self, calculator, test_order, mock_market_state):
        """测试紧急程度影响"""
        # 正常紧急程度
        normal_price = await calculator.calculate_limit_price(
            test_order,
            mock_market_state,
            urgency=1.0
        )
        
        # 高紧急程度
        urgent_price = await calculator.calculate_limit_price(
            test_order,
            mock_market_state,
            urgency=2.0
        )
        
        # 验证紧急程度影响
        if test_order.side == "BUY":
            assert urgent_price.optimal_price > normal_price.optimal_price
        else:
            assert urgent_price.optimal_price < normal_price.optimal_price
    
    async def test_adjustment_factors(self, calculator, test_order):
        """测试调整因子"""
        # 获取当前因子
        original_factors = calculator.get_adjustment_factors()
        
        # 更新因子
        new_factors = {
            'volatility': 1.2,
            'momentum': 0.8,
            'depth': 1.5
        }
        await calculator.update_adjustment_factors(new_factors)
        
        # 验证更新
        updated_factors = calculator.get_adjustment_factors()
        assert updated_factors['volatility'] == new_factors['volatility']
        assert updated_factors['momentum'] == new_factors['momentum']
        assert updated_factors['depth'] == new_factors['depth']
    
    async def test_confidence_calculation(self, calculator, test_order, mock_market_state):
        """测试置信度计算"""
        # 计算价格和置信度
        price_range = await calculator.calculate_limit_price(
            test_order,
            mock_market_state
        )
        
        # 验证置信度
        assert 0 <= price_range.confidence <= 1
        assert price_range.confidence_factors is not None
        
        # 测试不同市场条件下的置信度
        volatile_state = mock_market_state.copy()
        volatile_state['volatility'] *= 2
        
        volatile_price = await calculator.calculate_limit_price(
            test_order,
            volatile_state
        )
        
        assert volatile_price.confidence < price_range.confidence
    
    async def test_price_range_validation(self, calculator, test_order, mock_market_state):
        """测试价格范围验证"""
        # 计算价格范围
        price_range = await calculator.calculate_limit_price(
            test_order,
            mock_market_state
        )
        
        # 验证价格范围的合理性
        assert price_range.min_price > 0
        assert price_range.max_price > price_range.min_price
        assert price_range.optimal_price >= price_range.min_price
        assert price_range.optimal_price <= price_range.max_price
        
        # 验证价格偏差
        max_deviation = calculator.max_price_deviation
        mid_price = (mock_market_state['bid_price'] + mock_market_state['ask_price']) / 2
        assert abs(price_range.optimal_price / mid_price - 1) <= max_deviation
    
    async def test_market_condition_adaptation(self, calculator, test_order, mock_market_state):
        """测试市场条件适应"""
        # 正常市场条件
        normal_price = await calculator.calculate_limit_price(
            test_order,
            mock_market_state
        )
        
        # 高波动性市场条件
        volatile_state = mock_market_state.copy()
        volatile_state['volatility'] *= 2
        volatile_price = await calculator.calculate_limit_price(
            test_order,
            volatile_state
        )
        
        # 验证适应性
        assert volatile_price.price_range > normal_price.price_range
        assert volatile_price.confidence < normal_price.confidence 