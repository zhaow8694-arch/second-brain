# telegram_notifier.py
# 真实 Telegram 推送模块 - V1.0（已填入你的真实信息）

import requests
from datetime import datetime

class TelegramNotifier:
    def __init__(self):
        # 已为你填入真实信息
        self.bot_token = "8677589842:AAHbkony7koMbzsexBUaz1c6uxubtMYk4q4"
        self.chat_id = "7912228032"
        self.enabled = True
        
        print("✅ Telegram 真实推送模块初始化成功（已使用你的 Bot Token 和 Chat ID）")

    def send_signal(self, signal: dict):
        """发送真实 Telegram 交易信号"""
        message = f"""
🚨 【黄金交易信号】

📌 方向：{signal['direction']}
🎯 入场区间：{signal['entry_zone']}
🛑 止损：{signal['stop_loss']}
📏 建议手数：{signal['lots']} 手
🔍 理由：{signal['reason']}
⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print("✅ Telegram 信号已成功推送至你的账号")
                return True
            else:
                print(f"❌ Telegram 发送失败: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Telegram 发送异常: {e}")
            return False


# 测试代码
if __name__ == "__main__":
    notifier = TelegramNotifier()
    
    test_signal = {
        'direction': '做空',
        'entry_zone': '4430.0 附近',
        'stop_loss': 4445,
        'lots': 0.03,
        'reason': '4H/Daily Bear OB + EMA9向下'
    }
    
    notifier.send_signal(test_signal)