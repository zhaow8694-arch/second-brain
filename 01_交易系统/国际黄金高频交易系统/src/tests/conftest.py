import pytest
import os
import sys
from datetime import datetime
from typing import Dict, Any
from models.deepseek_interface import ModelConfig
from src.tests.data_generators import (
    generate_market_data,
    generate_order_book_data,
    generate_execution_data,
    generate_strategy_signals,
    generate_risk_metrics
)

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """测试配置"""
    return {
        'cache_dir': os.path.join(project_root, 'test_cache'),
        'max_workers': 4,
        'chunk_size': 100,
        'cache_size': 1000
    }

@pytest.fixture(autouse=True)
def setup_test_env():
    """设置测试环境"""
    # 创建测试缓存目录
    cache_dir = os.path.join(project_root, 'test_cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    yield
    
    # 清理测试缓存目录
    if os.path.exists(cache_dir):
        for file in os.listdir(cache_dir):
            os.remove(os.path.join(cache_dir, file))
        os.rmdir(cache_dir)

@pytest.fixture
def model_config():
    """创建测试用的模型配置"""
    return ModelConfig(
        model_type="volatility_prediction",
        input_features=[
            'price', 'volume', 'volatility', 'trend_strength',
            'momentum', 'order_imbalance', 'spread'
        ],
        output_features=['volatility'],
        time_horizon=5,
        update_interval=1,
        confidence_threshold=0.7,
        batch_size=32,
        use_gpu=False
    )

@pytest.fixture
def market_data():
    """生成市场数据fixture"""
    features, labels = generate_market_data(n_points=50)
    return features, labels

@pytest.fixture
def order_book():
    """生成订单簿数据fixture"""
    return generate_order_book_data()

@pytest.fixture
def execution_result():
    """生成执行结果数据fixture"""
    return generate_execution_data(
        order_size=1.0,
        base_price=50000.0,
        slippage_bps=1.0
    )

@pytest.fixture
def strategy_data():
    """生成策略数据fixture"""
    mean_reversion_signals = generate_strategy_signals(
        n_points=50,
        signal_type='mean_reversion'
    )
    momentum_signals = generate_strategy_signals(
        n_points=50,
        signal_type='momentum'
    )
    return {
        'mean_reversion': mean_reversion_signals,
        'momentum': momentum_signals
    }

@pytest.fixture
def risk_data():
    """生成风险数据fixture"""
    return generate_risk_metrics()

@pytest.fixture
def test_timestamps():
    """生成测试用的时间戳序列"""
    base_time = datetime.now()
    return [base_time + pytest.approx(i, abs=1e-6) for i in range(10)]

@pytest.fixture
def mock_market_state() -> Dict[str, Any]:
    """生成模拟的市场状态"""
    return {
        'current_price': 50000.0,
        'bid_price': 49999.0,
        'ask_price': 50001.0,
        'last_trade_price': 50000.0,
        'last_trade_volume': 1.0,
        'total_volume': 100.0,
        'vwap': 50000.0,
        'volatility': 0.02,
        'timestamp': datetime.now()
    }

@pytest.fixture
def mock_portfolio_state() -> Dict[str, Any]:
    """生成模拟的投资组合状态"""
    return {
        'total_value': 1000000.0,
        'cash': 500000.0,
        'positions': {
            'GOLD': {
                'size': 10.0,
                'avg_price': 50000.0,
                'current_price': 50100.0,
                'unrealized_pnl': 1000.0
            }
        },
        'realized_pnl': 5000.0,
        'timestamp': datetime.now()
    } 