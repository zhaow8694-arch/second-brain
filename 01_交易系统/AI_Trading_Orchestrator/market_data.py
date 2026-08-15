# market_data.py
# 市场数据采集与结构判断模块 - V1.0

class MarketData:
    def __init__(self):
        pass
    
    def get_current_structure(self, price: float, ema9_trend: str, ob_type: str, ob_price: float):
        """
        返回当前市场结构状态（供 SignalGenerator 使用）
        """
        structure = {
            "price": price,
            "ema9_trend": ema9_trend,      # "up" 或 "down"
            "ob_type": ob_type,            # "bull" 或 "bear"
            "ob_price": ob_price,
            "bias": "中性" if abs(price - ob_price) < 10 else ("偏多" if price > ob_price else "偏空")
        }
        return structure
    
    def simulate_realtime_price(self):
        """
        模拟实时价格（开发测试用，后续会替换成真实API数据）
        """
        # 这里模拟当前黄金价格，后续可接入真实数据源
        return {
            "price": 4415.5,
            "ema9_trend": "down",      # 示例：当前EMA9向下
            "ob_type": "bear",         # 当前处于Bear OB附近
            "ob_price": 4430.0
        }


# 测试代码
if __name__ == "__main__":
    md = MarketData()
    data = md.simulate_realtime_price()
    structure = md.get_current_structure(
        price=data["price"],
        ema9_trend=data["ema9_trend"],
        ob_type=data["ob_type"],
        ob_price=data["ob_price"]
    )
    print("=== 市场数据模块测试成功 ===")
    print(structure)