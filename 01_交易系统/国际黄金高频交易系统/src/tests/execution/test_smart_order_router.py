import pytest
from datetime import datetime
from execution.smart_order_router import SmartOrderRouter
from models.deepseek_interface import Order, ExecutionVenue

class TestSmartOrderRouter:
    """智能订单路由器测试类"""
    
    @pytest.fixture
    def router(self):
        """创建路由器实例"""
        return SmartOrderRouter()
    
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
    
    async def test_venue_selection(self, router, test_order, order_book):
        """测试交易所选择"""
        # 初始化路由器
        await router.initialize()
        
        # 更新市场数据
        await router.update_market_data(order_book)
        
        # 选择最优交易所
        selected_venue = await router.select_best_venue(test_order)
        
        # 验证结果
        assert isinstance(selected_venue, ExecutionVenue)
        assert selected_venue.liquidity_score > 0
        assert selected_venue.cost_score >= 0
    
    async def test_order_splitting(self, router, test_order):
        """测试订单拆分"""
        # 设置大订单
        large_order = test_order
        large_order.quantity = 10.0
        
        # 执行订单拆分
        child_orders = await router.split_order(large_order)
        
        # 验证拆分结果
        assert len(child_orders) > 1
        assert sum(order.quantity for order in child_orders) == large_order.quantity
        assert all(order.instrument_id == large_order.instrument_id for order in child_orders)
    
    async def test_routing_strategy(self, router, test_order, mock_market_state):
        """测试路由策略"""
        # 更新市场状态
        await router.update_market_state(mock_market_state)
        
        # 获取路由策略
        strategy = await router.get_routing_strategy(test_order)
        
        # 验证策略
        assert strategy.venue_weights is not None
        assert len(strategy.venue_weights) > 0
        assert sum(strategy.venue_weights.values()) == pytest.approx(1.0)
    
    async def test_cost_estimation(self, router, test_order, order_book):
        """测试成本估算"""
        # 估算执行成本
        cost_estimate = await router.estimate_execution_cost(
            test_order,
            order_book
        )
        
        # 验证成本估算
        assert cost_estimate.total_cost >= 0
        assert cost_estimate.slippage is not None
        assert cost_estimate.fee is not None
    
    async def test_market_impact(self, router, test_order, order_book):
        """测试市场冲击评估"""
        # 评估市场冲击
        impact = await router.estimate_market_impact(
            test_order,
            order_book
        )
        
        # 验证评估结果
        assert impact.price_impact >= 0
        assert impact.volume_impact >= 0
        assert impact.confidence > 0
    
    async def test_venue_scoring(self, router):
        """测试交易所评分"""
        # 获取所有交易所评分
        venue_scores = await router.get_venue_scores()
        
        # 验证评分
        assert len(venue_scores) > 0
        for venue in venue_scores:
            assert venue.liquidity_score >= 0
            assert venue.reliability_score >= 0
            assert venue.cost_score >= 0
    
    async def test_adaptive_routing(self, router, test_order, mock_market_state):
        """测试自适应路由"""
        # 初始化历史性能数据
        await router.initialize_performance_history()
        
        # 更新市场状态
        await router.update_market_state(mock_market_state)
        
        # 执行自适应路由
        routing_decision = await router.get_adaptive_routing(test_order)
        
        # 验证路由决策
        assert routing_decision.primary_venue is not None
        assert routing_decision.backup_venues is not None
        assert len(routing_decision.backup_venues) > 0
        assert routing_decision.confidence > 0 