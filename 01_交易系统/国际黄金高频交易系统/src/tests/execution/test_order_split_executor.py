import pytest
from datetime import datetime
from execution.order_split_executor import OrderSplitExecutor
from models.deepseek_interface import Order, ExecutionResult

class TestOrderSplitExecutor:
    """订单拆分执行器测试类"""
    
    @pytest.fixture
    def executor(self):
        """创建执行器实例"""
        return OrderSplitExecutor()
    
    @pytest.fixture
    def test_order(self):
        """创建测试订单"""
        return Order(
            instrument_id="GOLD",
            order_type="LIMIT",
            side="BUY",
            quantity=10.0,
            price=50000.0,
            timestamp=datetime.now()
        )
    
    async def test_initialization(self, executor):
        """测试初始化"""
        await executor.initialize()
        assert executor.is_initialized
        assert executor.execution_config is not None
    
    async def test_split_calculation(self, executor, test_order, mock_market_state):
        """测试拆分计算"""
        # 更新市场状态
        await executor.update_market_state(mock_market_state)
        
        # 计算拆分方案
        split_plan = await executor.calculate_split_plan(test_order)
        
        # 验证拆分方案
        assert len(split_plan.child_orders) > 0
        assert sum(order.quantity for order in split_plan.child_orders) == test_order.quantity
        assert split_plan.time_points is not None
        assert split_plan.venue_allocation is not None
    
    async def test_execution_sequence(self, executor, test_order):
        """测试执行序列"""
        # 获取执行序列
        sequence = await executor.get_execution_sequence(test_order)
        
        # 验证序列
        assert len(sequence) > 0
        assert all(step.order.quantity > 0 for step in sequence)
        assert all(step.scheduled_time >= test_order.timestamp for step in sequence)
    
    async def test_adaptive_execution(self, executor, test_order, mock_market_state):
        """测试自适应执行"""
        # 设置初始状态
        await executor.update_market_state(mock_market_state)
        
        # 开始执行
        execution_stream = executor.execute_adaptively(test_order)
        
        results = []
        async for result in execution_stream:
            results.append(result)
        
        # 验证执行结果
        assert len(results) > 0
        assert all(isinstance(r, ExecutionResult) for r in results)
        assert sum(r.executed_quantity for r in results) == pytest.approx(test_order.quantity)
    
    async def test_execution_monitoring(self, executor, test_order):
        """测试执行监控"""
        # 启动监控
        monitor = await executor.start_execution_monitoring(test_order)
        
        # 验证监控状态
        assert monitor.is_active
        assert monitor.order_id == test_order.order_id
        assert monitor.start_time is not None
        
        # 获取监控指标
        metrics = await monitor.get_metrics()
        assert metrics.progress >= 0
        assert metrics.performance_metrics is not None
    
    async def test_risk_control(self, executor, test_order, risk_data):
        """测试风险控制"""
        # 设置风险限制
        await executor.set_risk_limits(risk_data)
        
        # 验证风险检查
        risk_check = await executor.check_execution_risk(test_order)
        assert risk_check.is_within_limits
        assert risk_check.risk_metrics is not None
        
        # 测试风险事件处理
        risk_event = await executor.simulate_risk_event(test_order)
        assert risk_event.mitigation_action is not None
    
    async def test_performance_analysis(self, executor, test_order, execution_result):
        """测试性能分析"""
        # 添加执行结果
        await executor.add_execution_result(execution_result)
        
        # 获取性能分析
        analysis = await executor.analyze_performance(test_order)
        
        # 验证分析结果
        assert analysis.execution_quality is not None
        assert analysis.cost_analysis is not None
        assert analysis.efficiency_metrics is not None
    
    async def test_venue_coordination(self, executor, test_order):
        """测试交易所协调"""
        # 获取交易所分配
        allocation = await executor.get_venue_allocation(test_order)
        
        # 验证分配结果
        assert len(allocation.venues) > 0
        assert sum(allocation.weights.values()) == pytest.approx(1.0)
        assert allocation.backup_plan is not None 