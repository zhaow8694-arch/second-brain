# signal_generator.py
# 黄金交易信号生成器 - V1.0

from risk_manager import RiskManager

class SignalGenerator:
    def __init__(self):
        self.rm = RiskManager(total_capital=20000)
    
    def generate_signal(self, price: float, ema9_trend: str, ob_type: str, ob_price: float):
        """
        生成黄金交易信号
        参数：
        price: 当前价格
        ema9_trend: "up" 或 "down"
        ob_type: "bull" 或 "bear"
        ob_price: Order Block价格
        """
        signal = {
            "direction": None,
            "entry_zone": None,
            "stop_loss": None,
            "lots": 0.0,
            "reason": ""
        }
        
        # 做多信号
        if ema9_trend == "up" and ob_type == "bull" and price <= ob_price + 5:
            signal["direction"] = "做多"
            signal["entry_zone"] = f"{ob_price:.1f} 附近"
            signal["stop_loss"] = ob_price - 15
            signal["lots"] = self.rm.calculate_position_size(price, signal["stop_loss"])
            signal["reason"] = "4H/Daily Bull OB + EMA9向上"
        
        # 做空信号
        elif ema9_trend == "down" and ob_type == "bear" and price >= ob_price - 5:
            signal["direction"] = "做空"
            signal["entry_zone"] = f"{ob_price:.1f} 附近"
            signal["stop_loss"] = ob_price + 15
            signal["lots"] = self.rm.calculate_position_size(price, signal["stop_loss"])
            signal["reason"] = "4H/Daily Bear OB + EMA9向下"
        
        return signal


# 测试代码
if __name__ == "__main__":
    sg = SignalGenerator()
    
    # 示例1：做多信号
    signal1 = sg.generate_signal(price=4415, ema9_trend="up", ob_type="bull", ob_price=4410)
    print("=== 测试做多信号 ===")
    print(signal1)
    
    # 示例2：做空信号
    signal2 = sg.generate_signal(price=4425, ema9_trend="down", ob_type="bear", ob_price=4430)
    print("\n=== 测试做空信号 ===")
    print(signal2)