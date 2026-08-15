# api_config.py
# API配置管理模块 - V1.0（真实API接入准备）

class APIConfig:
    def __init__(self):
        # 请在这里填写你的真实API密钥（目前留空，使用模拟模式）
        self.gemini_api_key = ""          # Google Gemini API Key
        self.grok_api_key = ""            # xAI Grok API Key（如果有）
        self.deepseek_api_key = ""        # DeepSeek API Key（如果有）
        self.binance_api_key = ""         # Binance API Key（可选）
        self.binance_secret = ""          # Binance Secret（可选）
        
        self.use_real_api = False         # 切换开关：True=真实API，False=模拟模式
        
        if self.use_real_api:
            print("✅ 真实API模式已启用")
        else:
            print("⚠️ 当前使用模拟模式（可随时切换为真实API）")

    def get_gemini_key(self):
        return self.gemini_api_key if self.gemini_api_key else None

    def get_grok_key(self):
        return self.grok_api_key if self.grok_api_key else None

    def get_deepseek_key(self):
        return self.deepseek_api_key if self.deepseek_api_key else None

    def switch_to_real_api(self):
        """切换到真实API模式"""
        self.use_real_api = True
        print("🔄 已切换到真实API模式（需填写有效API Key）")

    def switch_to_simulate(self):
        """切换回模拟模式"""
        self.use_real_api = False
        print("🔄 已切换回模拟模式")


# 测试代码
if __name__ == "__main__":
    config = APIConfig()
    print(f"当前模式: {'真实API' if config.use_real_api else '模拟模式'}")
    config.switch_to_real_api()
    config.switch_to_simulate()