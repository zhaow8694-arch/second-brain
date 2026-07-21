import asyncio
import os
from dotenv import load_dotenv
from models.deepseek_analyzer import DeepSeekAnalyzer

async def main():
    # 加载环境变量
    load_dotenv()
    
    # 获取API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        raise ValueError("未找到DeepSeek API密钥")
        
    # 创建分析器实例
    analyzer = DeepSeekAnalyzer(api_key)
    
    # 测试单个市场分析
    try:
        print("分析BTCUSDT市场...")
        result = await analyzer.analyze_market('BTCUSDT')
        print("\n分析结果:")
        print(f"时间: {result['timestamp']}")
        print(f"交易信号: {result['signal']}")
        print(f"风险评分: {result.get('risk_score', 'N/A')}")
        print("\n详细分析:")
        print(result['raw_analysis'])
    except Exception as e:
        print(f"单市场分析出错: {str(e)}")
        
    # 测试批量市场分析
    try:
        symbols = ['BTCUSDT', 'ETHUSDT', 'XAUUSD']
        print("\n批量分析多个市场...")
        results = await analyzer.get_batch_analysis(symbols)
        
        for symbol, result in results.items():
            print(f"\n{symbol} 分析结果:")
            print(f"交易信号: {result['signal']}")
            print(f"风险评分: {result.get('risk_score', 'N/A')}")
    except Exception as e:
        print(f"批量分析出错: {str(e)}")
        
if __name__ == "__main__":
    asyncio.run(main()) 