# price_fetcher.py
# 实时价格获取模块 - V1.0（可模拟真实数据，后续可接入API）

from datetime import datetime
import random

class PriceFetcher:
    def __init__(self):
        print("✅ 实时价格获取模块初始化完成（模拟模式）")
        self.last_price = 4415.5   # 初始价格

    def get_current_price(self):
        """
        获取当前黄金实时价格（模拟真实波动）
        实际运行时可替换为 TradingView / Binance / MT5 API
        """
        # 模拟小幅波动
        self.last_price += random.uniform(-3.5, 3.5)
        
        data = {
            "price": round(self.last_price, 2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "模拟数据（可替换为真实API）",
            "change": round(random.uniform(-0.8, 0.8), 2)
        }
        return data

    def get_mock_structure(self):
        """
        模拟返回当前市场结构（供SignalGenerator使用）
        """
        price = self.get_current_price()["price"]
        return {
            "price": price,
            "ema9_trend": "down" if price < 4425 else "up",
            "ob_type": "bear" if price > 4420 else "bull",
            "ob_price": 4430 if price > 4420 else 4410
        }


# 测试代码
if __name__ == "__main__":
    fetcher = PriceFetcher()
    
    for i in range(5):
        price_data = fetcher.get_current_price()
        structure = fetcher.get_mock_structure()
        print(f"[{price_data['timestamp']}] 价格: {price_data['price']} | 变化: {price_data['change']}")
        print(f"结构: EMA9 {structure['ema9_trend']} | OB: {structure['ob_type']} @ {structure['ob_price']}\n")