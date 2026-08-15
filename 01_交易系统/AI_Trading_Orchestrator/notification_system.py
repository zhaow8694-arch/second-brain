# notification_system.py
# 交易信号通知系统 - V1.0

class NotificationSystem:
    def __init__(self):
        print("✅ 通知系统初始化完成")
    
    def send_signal(self, signal: dict):
        """发送交易信号通知"""
        message = f"""
🚨 黄金交易信号
📌 方向：{signal['direction']}
🎯 入场区间：{signal['entry_zone']}
🛑 止损：{signal['stop_loss']}
📏 建议手数：{signal['lots']} 手
🔍 理由：{signal['reason']}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        print(message.strip())
        print("✅ 信号已发送（模拟）\n")
        # 后续可接入 Telegram / 企业微信 / 手机推送
        return message
    
    def send_alert(self, alert_message: str):
        """发送普通警报"""
        print(f"⚠️ 警报：{alert_message}")
        return alert_message


# 测试代码
if __name__ == "__main__":
    from datetime import datetime
    ns = NotificationSystem()
    
    test_signal = {
        'direction': '做空',
        'entry_zone': '4430.0 附近',
        'stop_loss': 4445,
        'lots': 0.03,
        'reason': '4H/Daily Bear OB + EMA9向下'
    }
    
    ns.send_signal(test_signal)