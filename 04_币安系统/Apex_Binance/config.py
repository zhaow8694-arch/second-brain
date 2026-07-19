"""
配置文件管理模块
安全地处理API密钥和系统配置
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置管理类"""
    
    # 币安API配置
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET = os.getenv("BINANCE_SECRET", "")
    
    # Telegram配置
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # 交易配置
    RISK_PCT = float(os.getenv("RISK_PCT", "0.008"))
    DAILY_MAX_LOSS = float(os.getenv("DAILY_MAX_LOSS", "0.10"))
    MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", "6"))
    MAX_REGULAR_POSITIONS = int(os.getenv("MAX_REGULAR_POSITIONS", "4"))
    
    # 策略参数
    ATR_SL_LONG = float(os.getenv("ATR_SL_LONG", "3.5"))
    ATR_SL_SHORT = float(os.getenv("ATR_SL_SHORT", "2.5"))
    HWM_ACTIVATE_LONG = float(os.getenv("HWM_ACTIVATE_LONG", "0.025"))
    HWM_ACTIVATE_SHORT = float(os.getenv("HWM_ACTIVATE_SHORT", "0.030"))
    HWM_RETRACT_LONG = float(os.getenv("HWM_RETRACT_LONG", "0.012"))
    HWM_RETRACT_SHORT = float(os.getenv("HWM_RETRACT_SHORT", "0.015"))
    
    # 系统配置
    STATE_FILE = os.getenv("STATE_FILE", "guardian_earth_state_core.json")
    COOLDOWN_TIME = int(os.getenv("COOLDOWN_TIME", "3600"))
    REPORT_INTERVAL = int(os.getenv("REPORT_INTERVAL", "14400"))

    # === Z-Wei 市场状态过滤参数 ===
    ADX_TRENDING_THRESHOLD = float(os.getenv("ADX_TRENDING_THRESHOLD", "20"))
    ADX_STRONG_TREND = float(os.getenv("ADX_STRONG_TREND", "30"))

    # === Z-Wei 突破质量参数 ===
    SIGNAL_EXPANSION_MAX = float(os.getenv("SIGNAL_EXPANSION_MAX", "2.5"))

    # === Z-Wei 危险K线参数 ===
    DANGEROUS_BODY_MULTIPLIER = float(os.getenv("DANGEROUS_BODY_MULTIPLIER", "3.0"))

    # === 动量退出参数 ===
    MOMENTUM_RSI_OVERBOUGHT = float(os.getenv("MOMENTUM_RSI_OVERBOUGHT", "70"))
    MOMENTUM_RSI_OVERSOLD = float(os.getenv("MOMENTUM_RSI_OVERSOLD", "30"))
    MOMENTUM_RSI_DELTA = float(os.getenv("MOMENTUM_RSI_DELTA", "5"))

    # === 时间止损 ===
    MAX_HOLD_HOURS = float(os.getenv("MAX_HOLD_HOURS", "48"))
    
    # 高杠杆币种
    @classmethod
    def get_high_leverage_coins(cls) -> set:
        """获取高杠杆币种列表"""
        default_value = "BTC,ETH,SOL,DOGE"
        coins_str = os.getenv("HIGH_LEV_COINS", default_value)
        return {coin.strip().upper() for coin in coins_str.split(",") if coin.strip()}
    
    # 交易对列表
    SYMBOL_LIST = [
        'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT',
        'DOGE/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT',
        'LINK/USDT', 'BCH/USDT', 'NEAR/USDT', 'UNI/USDT',
        'LTC/USDT', 'APT/USDT', 'STX/USDT', 'ARB/USDT',
        'OP/USDT', 'INJ/USDT', 'TIA/USDT', 'SUI/USDT',
        'SEI/USDT', 'FET/USDT', 'TAO/USDT', 'WLD/USDT'
    ]
    
    # 板块映射（已补全全部 SYMBOL_LIST 中币种）
    SECTOR_MAP = {
        'BTC': 'POW', 'BCH': 'POW', 'LTC': 'POW',
        'ETH': 'L1', 'SOL': 'L1', 'BNB': 'L1', 'SUI': 'L1', 'NEAR': 'L1',
        'AVAX': 'L1', 'APT': 'L1', 'SEI': 'L1', 'TIA': 'L1',
        'DOT': 'L0',
        'LINK': 'INFRA', 'INJ': 'INFRA',
        'OP': 'L2', 'ARB': 'L2', 'STX': 'L2',
        'DOGE': 'MEME', 'WLD': 'MEME',
        'XRP': 'PAYMENT', 'UNI': 'DEFI', 'ADA': 'L1',
        'TAO': 'AI', 'FET': 'AI',
    }
    
    @classmethod
    def validate(cls) -> None:
        """验证配置完整性"""
        errors = []
        
        if not cls.BINANCE_API_KEY:
            errors.append("BINANCE_API_KEY 未设置")
        if not cls.BINANCE_SECRET:
            errors.append("BINANCE_SECRET 未设置")
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN 未设置")
        if not cls.TELEGRAM_CHAT_ID:
            errors.append("TELEGRAM_CHAT_ID 未设置")
        
        if cls.RISK_PCT <= 0 or cls.RISK_PCT > 0.1:
            errors.append(f"RISK_PCT 值无效: {cls.RISK_PCT}")
        if cls.DAILY_MAX_LOSS <= 0 or cls.DAILY_MAX_LOSS > 0.5:
            errors.append(f"DAILY_MAX_LOSS 值无效: {cls.DAILY_MAX_LOSS}")
        if cls.MAX_POSITIONS <= 0:
            errors.append(f"MAX_POSITIONS 值无效: {cls.MAX_POSITIONS}")
        if cls.MAX_REGULAR_POSITIONS <= 0:
            errors.append(f"MAX_REGULAR_POSITIONS 值无效: {cls.MAX_REGULAR_POSITIONS}")
        if cls.MAX_REGULAR_POSITIONS > cls.MAX_POSITIONS:
            errors.append("MAX_REGULAR_POSITIONS 不应大于 MAX_POSITIONS")
        if cls.ATR_SL_LONG <= 0:
            errors.append(f"ATR_SL_LONG 值无效: {cls.ATR_SL_LONG}")
        if cls.ATR_SL_SHORT <= 0:
            errors.append(f"ATR_SL_SHORT 值无效: {cls.ATR_SL_SHORT}")
        if cls.COOLDOWN_TIME <= 0:
            errors.append(f"COOLDOWN_TIME 值无效: {cls.COOLDOWN_TIME}")
        if cls.REPORT_INTERVAL <= 0:
            errors.append(f"REPORT_INTERVAL 值无效: {cls.REPORT_INTERVAL}")
        
        if errors:
            raise RuntimeError(f"配置验证失败:\n" + "\n".join(errors))
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            'binance_api_key_set': bool(cls.BINANCE_API_KEY),
            'binance_secret_set': bool(cls.BINANCE_SECRET),
            'telegram_bot_token_set': bool(cls.TELEGRAM_BOT_TOKEN),
            'telegram_chat_id_set': bool(cls.TELEGRAM_CHAT_ID),
            'risk_pct': cls.RISK_PCT,
            'daily_max_loss': cls.DAILY_MAX_LOSS,
            'max_positions': cls.MAX_POSITIONS,
            'max_regular_positions': cls.MAX_REGULAR_POSITIONS,
            'high_leverage_coins': list(cls.get_high_leverage_coins()),
            'symbol_count': len(cls.SYMBOL_LIST),
            'state_file': cls.STATE_FILE,
        }


# 创建全局配置实例
config = Config