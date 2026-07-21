import asyncio
import os
from dotenv import load_dotenv
from signals.signal_generator import SignalGenerator
import json

async def main():
    # 加载环境变量
    load_dotenv()
    
    # 获取API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        raise ValueError("未找到DeepSeek API密钥")
        
    # 创建信号生成器实例
    signal_generator = SignalGenerator(api_key)
    
    # 测试单个交易对的信号生成
    try:
        print("为BTCUSDT生成交易信号...")
        signal = await signal_generator.generate_signal('BTCUSDT')
        
        print("\n交易信号详情:")
        print(f"时间: {signal['timestamp']}")
        print(f"交易对: {signal['symbol']}")
        print(f"信号类型: {signal['signal_type']}")
        print(f"交易方向: {signal['direction']}")
        print(f"进场价格: {signal['entry_price']}")
        print(f"止损价格: {signal['stop_loss']}")
        print(f"目标价格: {signal['target_price']}")
        print(f"信号强度: {signal['confidence']:.2f}")
        print(f"风险评分: {signal['metadata']['risk_score']}")
        
        # 验证信号
        is_valid = signal_generator.validate_signal(signal)
        print(f"\n信号验证结果: {'有效' if is_valid else '无效'}")
        
        # 打印完整的AI分析
        print("\nAI分析详情:")
        print(signal['metadata']['ai_analysis'])
        
    except Exception as e:
        print(f"生成单个交易信号时出错: {str(e)}")
        
    # 测试批量交易对的信号生成
    try:
        symbols = ['BTCUSDT', 'ETHUSDT', 'XAUUSD']
        print("\n批量生成交易信号...")
        signals = await signal_generator.generate_batch_signals(symbols)
        
        for symbol, signal in signals.items():
            print(f"\n{symbol} 交易信号:")
            print(f"方向: {signal['direction']}")
            print(f"信号强度: {signal['confidence']:.2f}")
            print(f"风险评分: {signal['metadata']['risk_score']}")
            
    except Exception as e:
        print(f"批量生成交易信号时出错: {str(e)}")
        
if __name__ == "__main__":
    asyncio.run(main()) 