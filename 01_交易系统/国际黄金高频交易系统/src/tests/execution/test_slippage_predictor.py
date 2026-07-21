import pytest
import numpy as np
from datetime import datetime, timedelta
from execution.slippage_predictor import SlippagePredictor, MarketState, SlippageMetrics
from models.deepseek_interface import Order

class TestSlippagePredictor:
    """滑点预测器测试类"""
    
    @pytest.fixture
    def predictor(self):
        """创建预测器实例"""
        return SlippagePredictor(
            lookback_window=20,
            update_interval=5,
            min_samples=10
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
    
    async def test_market_state_update(self, predictor, mock_market_state):
        """测试市场状态更新"""
        # 更新市场状态
        await predictor.update_market_state(mock_market_state)
        
        # 获取当前状态
        current_state = predictor.get_current_state()
        
        # 验证状态
        assert isinstance(current_state, MarketState)
        assert current_state.timestamp == mock_market_state['timestamp']
        assert current_state.volatility == mock_market_state['volatility']
        assert len(predictor.market_states) > 0
    
    async def test_execution_history(self, predictor, test_order, execution_result):
        """测试执行历史"""
        # 添加执行结果
        await predictor.add_execution_result(
            test_order,
            execution_result
        )
        
        # 获取历史数据
        history = predictor.get_execution_history()
        
        # 验证历史记录
        assert len(history) > 0
        assert history[-1]['order_id'] == test_order.order_id
        assert history[-1]['slippage'] == (
            execution_result['execution_price'] / test_order.price - 1
        )
    
    async def test_feature_preparation(self, predictor, mock_market_state):
        """测试特征准备"""
        # 更新多个市场状态
        for i in range(10):
            state = mock_market_state.copy()
            state['timestamp'] += timedelta(minutes=i)
            state['volatility'] *= (1 + np.random.normal(0, 0.1))
            await predictor.update_market_state(state)
        
        # 准备特征
        features = await predictor.prepare_features()
        
        # 验证特征
        assert isinstance(features, np.ndarray)
        assert features.shape[1] == predictor.n_features
        assert not np.any(np.isnan(features))
    
    async def test_model_update(self, predictor, test_order, execution_result):
        """测试模型更新"""
        # 添加多个执行结果
        for i in range(15):
            order = test_order
            order.timestamp += timedelta(minutes=i)
            result = execution_result.copy()
            result['execution_price'] *= (1 + np.random.normal(0, 0.001))
            await predictor.add_execution_result(order, result)
        
        # 更新模型
        await predictor.update_model()
        
        # 验证模型状态
        assert predictor.model is not None
        assert predictor.last_update_time is not None
        assert len(predictor.training_history) > 0
    
    async def test_slippage_prediction(self, predictor, test_order, mock_market_state):
        """测试滑点预测"""
        # 准备数据
        await predictor.update_market_state(mock_market_state)
        
        # 预测滑点
        prediction = await predictor.predict_slippage(test_order)
        
        # 验证预测结果
        assert isinstance(prediction, SlippageMetrics)
        assert prediction.expected_slippage is not None
        assert prediction.confidence_interval is not None
        assert 0 <= prediction.confidence <= 1
    
    async def test_confidence_intervals(self, predictor, test_order):
        """测试置信区间"""
        # 生成多个预测
        predictions = []
        for _ in range(10):
            order = test_order
            order.quantity *= (1 + np.random.normal(0, 0.1))
            prediction = await predictor.predict_slippage(order)
            predictions.append(prediction)
        
        # 验证置信区间
        for pred in predictions:
            assert pred.confidence_interval[0] <= pred.expected_slippage
            assert pred.expected_slippage <= pred.confidence_interval[1]
            assert pred.confidence_interval[1] - pred.confidence_interval[0] > 0
    
    async def test_model_persistence(self, predictor, test_order, execution_result):
        """测试模型持久化"""
        # 训练模型
        for i in range(20):
            order = test_order
            order.timestamp += timedelta(minutes=i)
            result = execution_result.copy()
            result['execution_price'] *= (1 + np.random.normal(0, 0.001))
            await predictor.add_execution_result(order, result)
        
        await predictor.update_model()
        
        # 保存模型
        await predictor.save_model("test_model.pkl")
        
        # 加载模型
        new_predictor = SlippagePredictor()
        await new_predictor.load_model("test_model.pkl")
        
        # 验证加载的模型
        assert new_predictor.model is not None
        assert len(new_predictor.training_history) > 0
        
        # 比较预测结果
        pred1 = await predictor.predict_slippage(test_order)
        pred2 = await new_predictor.predict_slippage(test_order)
        
        assert np.isclose(pred1.expected_slippage, pred2.expected_slippage, rtol=1e-5)
    
    async def test_adaptive_update(self, predictor, test_order, mock_market_state):
        """测试自适应更新"""
        # 初始化
        await predictor.update_market_state(mock_market_state)
        initial_pred = await predictor.predict_slippage(test_order)
        
        # 模拟市场变化
        volatile_state = mock_market_state.copy()
        volatile_state['volatility'] *= 2
        await predictor.update_market_state(volatile_state)
        
        # 添加新的执行结果
        execution_result = {
            'execution_price': test_order.price * 1.002,
            'executed_quantity': test_order.quantity,
            'execution_time': datetime.now(),
            'market_impact': test_order.price * 0.002,
            'transaction_cost': test_order.price * 0.002 * test_order.quantity,
            'execution_delay': timedelta(milliseconds=50)
        }
        await predictor.add_execution_result(test_order, execution_result)
        
        # 更新模型
        await predictor.update_model()
        
        # 获取新预测
        updated_pred = await predictor.predict_slippage(test_order)
        
        # 验证模型适应性
        assert updated_pred.confidence_interval[1] - updated_pred.confidence_interval[0] > \
               initial_pred.confidence_interval[1] - initial_pred.confidence_interval[0] 