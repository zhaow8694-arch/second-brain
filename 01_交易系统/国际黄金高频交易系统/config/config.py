from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 基础配置
BASE_DIR = Path(__file__).parent.parent

# 数据库配置
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'trading_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
}

# Redis配置
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
}

# 币安API配置
BINANCE_CONFIG = {
    'api_key': os.getenv('BINANCE_API_KEY', ''),
    'api_secret': os.getenv('BINANCE_API_SECRET', ''),
    'testnet': os.getenv('BINANCE_TESTNET', 'True').lower() == 'true',
}

# MT4配置
MT4_CONFIG = {
    'login': int(os.getenv('MT4_LOGIN', 0)),
    'password': os.getenv('MT4_PASSWORD', ''),
    'server': os.getenv('MT4_SERVER', ''),
    'timeout': int(os.getenv('MT4_TIMEOUT', 60000)),
}

# DeepSeek AI配置
DEEPSEEK_CONFIG = {
    'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
    'api_base': os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1'),
}

# 交易配置
TRADING_CONFIG = {
    'symbols': {
        'binance': ['BTCUSDT', 'ETHUSDT'],
        'mt4': ['XAUUSD'],
    },
    'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
    'risk_per_trade': float(os.getenv('RISK_PER_TRADE', 0.02)),
    'max_position_size': {
        'BTCUSDT': float(os.getenv('MAX_POSITION_BTC', 1.0)),
        'ETHUSDT': float(os.getenv('MAX_POSITION_ETH', 10.0)),
        'XAUUSD': float(os.getenv('MAX_POSITION_GOLD', 1.0)),
    },
}

# 风控配置
RISK_CONFIG = {
    'max_daily_loss': float(os.getenv('MAX_DAILY_LOSS', -1000)),
    'max_drawdown': float(os.getenv('MAX_DRAWDOWN', 0.1)),
    'max_trades_per_day': int(os.getenv('MAX_TRADES_PER_DAY', 100)),
}

# 日志配置
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'directory': BASE_DIR / 'logs',
} 