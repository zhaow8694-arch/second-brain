import pytest
import asyncio
from datetime import datetime, timedelta
import numpy as np
from src.prediction.price_predictor import PricePredictor
from src.prediction.volatility_predictor import VolatilityPredictor
from src.prediction.deepseek_interface import DeepSeekInterface

@pytest.fixture
async def price_predictor():
    """创建价格预测器实例"""
    predictor = PricePredictor(
        lookback_window=100,
        prediction_window=10,
        feature_columns=['price', 'volume', 'rsi', 'macd']
    )
    await predictor.initialize()
    return predictor

@pytest.fixture
async def volatility_predictor():
    """创建波动率预测器实例"""
    predictor = VolatilityPredictor(
        lookback_window=100,
        prediction_window=10,
        volatility_window=20
    )
    await predictor.initialize()
    return predictor

@pytest.fixture
async def deepseek_interface():
    """创建DeepSeek接口实例"""
    interface = DeepSeekInterface(
        model_name='deepseek-coder',
        max_tokens=1000,
        temperature=0.7
    )
    await interface.initialize()
    return interface

def generate_market_data(base_price: float, periods: int = 100):
    """生成模拟市场数据"""
    data = []
    current_time = datetime.now()
    
    # 生成价格序列
    prices = base_price * np.exp(np.random.normal(0, 0.001, periods).cumsum())
    
    # 生成技术指标
    for i in range(periods):
        data.append({
            'timestamp': current_time + timedelta(minutes=i),
            'price': prices[i],
            'volume': np.random.uniform(1, 10),
            'rsi': np.random.uniform(0, 100),
            'macd': np.random.uniform(-1, 1),
            'macd_signal': np.random.uniform(-1, 1),
            'macd_hist': np.random.uniform(-1, 1)
        })
    
    return data

async def test_price_prediction(predictor):
    """测试价格预测"""
    # 生成市场数据
    market_data = generate_market_data(50000.0)
    
    # 更新预测器数据
    for data in market_data:
        await predictor.update_market_data(data)
    
    # 生成预测
    prediction = await predictor.predict()
    assert prediction is not None
    assert 'price' in prediction
    assert 'confidence' in prediction
    assert 0 <= prediction['confidence'] <= 1

async def test_volatility_prediction(predictor):
    """测试波动率预测"""
    # 生成市场数据
    market_data = generate_market_data(50000.0)
    
    # 更新预测器数据
    for data in market_data:
        await predictor.update_market_data(data)
    
    # 生成预测
    prediction = await predictor.predict()
    assert prediction is not None
    assert 'volatility' in prediction
    assert 'confidence' in prediction
    assert prediction['volatility'] > 0
    assert 0 <= prediction['confidence'] <= 1

async def test_deepseek_interface(interface):
    """测试DeepSeek接口"""
    # 测试代码生成
    prompt = "实现一个简单的移动平均线计算函数"
    response = await interface.generate_code(prompt)
    assert response is not None
    assert len(response) > 0
    
    # 测试代码分析
    code = """
def calculate_ma(prices, window):
    return sum(prices[-window:]) / window
    """
    analysis = await interface.analyze_code(code)
    assert analysis is not None
    assert 'complexity' in analysis
    assert 'suggestions' in analysis

async def main():
    """运行所有测试"""
    print("开始运行预测模型测试...")
    
    try:
        # 创建测试实例
        price_predictor = await price_predictor()
        volatility_predictor = await volatility_predictor()
        deepseek_interface = await deepseek_interface()
        
        # 运行测试
        print("\n测试价格预测...")
        await test_price_prediction(price_predictor)
        print("✓ 价格预测测试通过")
        
        print("\n测试波动率预测...")
        await test_volatility_prediction(volatility_predictor)
        print("✓ 波动率预测测试通过")
        
        print("\n测试DeepSeek接口...")
        await test_deepseek_interface(deepseek_interface)
        print("✓ DeepSeek接口测试通过")
        
        print("\n所有预测模型测试通过！")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 