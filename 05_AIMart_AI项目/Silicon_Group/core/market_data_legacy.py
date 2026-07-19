import json
import os
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

CACHE_DIR = "market_cache"
CACHE_DURATION = 60
REQUEST_TIMEOUT = 8
MAX_RETRIES = 2

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def _ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def _cache_get(key: str) -> Optional[Dict]:
    _ensure_cache_dir()
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    if not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, "r") as f:
            data = json.load(f)
        cached_time = datetime.fromisoformat(data["_cached_at"])
        if datetime.now() - cached_time < timedelta(seconds=CACHE_DURATION):
            return data["_payload"]
        os.remove(cache_file)
    except Exception:
        pass
    return None


def _cache_set(key: str, payload: Dict):
    _ensure_cache_dir()
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    try:
        with open(cache_file, "w") as f:
            json.dump({"_cached_at": datetime.now().isoformat(), "_payload": payload}, f)
    except Exception:
        pass


def _fetch_json(url: str, headers: Optional[Dict] = None) -> Dict:
    headers = headers or {"User-Agent": "Mozilla/5.0"}
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"请求失败: {url} | {e}")
            time.sleep(1 * (attempt + 1))
    return {"error": "已达最大重试次数"}


# ============================================================
# 标的配置表 — 扩展新的品种只需在这里添加
# ============================================================
SYMBOL_LEGACY_CONFIG = {
    # 贵金属
    "XAU/USD": {
        "name": "黄金",
        "type": "forex",
        "yahoo": "GC=F",
        "fallback": "gold_api",
        "gold_api_key": "goldapi",
    },
    "XAG/USD": {
        "name": "白银",
        "type": "forex",
        "yahoo": "SI=F",
        "fallback": "gold_api",
        "gold_api_key": "XAG",
    },
    # 加密货币
    "BTC/USDT": {
        "name": "比特币",
        "type": "crypto",
        "yahoo": "BTC-USD",
        "binance": "BTCUSDT",
    },
    "ETH/USDT": {
        "name": "以太坊",
        "type": "crypto",
        "yahoo": "ETH-USD",
        "binance": "ETHUSDT",
    },
    "SOL/USDT": {
        "name": "Solana",
        "type": "crypto",
        "yahoo": "SOL-USD",
        "binance": "SOLUSDT",
    },
    "DOGE/USDT": {
        "name": "狗狗币",
        "type": "crypto",
        "yahoo": "DOGE-USD",
        "binance": "DOGEUSDT",
    },
    "XRP/USDT": {
        "name": "瑞波币",
        "type": "crypto",
        "yahoo": "XRP-USD",
        "binance": "XRPUSDT",
    },
    "ADA/USDT": {
        "name": "Cardano",
        "type": "crypto",
        "yahoo": "ADA-USD",
        "binance": "ADAUSDT",
    },
    "DOT/USDT": {
        "name": "Polkadot",
        "type": "crypto",
        "yahoo": "DOT-USD",
        "binance": "DOTUSDT",
    },
    "LINK/USDT": {
        "name": "Chainlink",
        "type": "crypto",
        "yahoo": "LINK-USD",
        "binance": "LINKUSDT",
    },
    "AVAX/USDT": {
        "name": "Avalanche",
        "type": "crypto",
        "yahoo": "AVAX-USD",
        "binance": "AVAXUSDT",
    },
    "LTC/USDT": {
        "name": "莱特币",
        "type": "crypto",
        "yahoo": "LTC-USD",
        "binance": "LTCUSDT",
    },
    "BCH/USDT": {
        "name": "比特币现金",
        "type": "crypto",
        "yahoo": "BCH-USD",
        "binance": "BCHUSDT",
    },
    "XLM/USDT": {
        "name": "Stellar",
        "type": "crypto",
        "yahoo": "XLM-USD",
        "binance": "XLMUSDT",
    },
    "TRX/USDT": {
        "name": "波场",
        "type": "crypto",
        "yahoo": "TRX-USD",
        "binance": "TRXUSDT",
    },
    "ETC/USDT": {
        "name": "以太经典",
        "type": "crypto",
        "yahoo": "ETC-USD",
        "binance": "ETCUSDT",
    },
    "NEAR/USDT": {
        "name": "NEAR Protocol",
        "type": "crypto",
        "yahoo": "NEAR-USD",
        "binance": "NEARUSDT",
    },
    # 美股
    "NVDA": {
        "name": "英伟达",
        "type": "stock",
        "yahoo": "NVDA",
    },
    "AAPL": {
        "name": "苹果",
        "type": "stock",
        "yahoo": "AAPL",
    },
    "TSLA": {
        "name": "特斯拉",
        "type": "stock",
        "yahoo": "TSLA",
    },
    "MSFT": {
        "name": "微软",
        "type": "stock",
        "yahoo": "MSFT",
    },
    "AMZN": {
        "name": "亚马逊",
        "type": "stock",
        "yahoo": "AMZN",
    },
    "GOOGL": {
        "name": "谷歌",
        "type": "stock",
        "yahoo": "GOOGL",
    },
    "META": {
        "name": "Meta",
        "type": "stock",
        "yahoo": "META",
    },
    "SPY": {
        "name": "标普500 ETF",
        "type": "etf",
        "yahoo": "SPY",
    },
    "QQQ": {
        "name": "纳斯达克 ETF",
        "type": "etf",
        "yahoo": "QQQ",
    },
    # 指数
    "DJI": {
        "name": "道琼斯",
        "type": "index",
        "yahoo": "^DJI",
    },
    "IXIC": {
        "name": "纳斯达克综合指数",
        "type": "index",
        "yahoo": "^IXIC",
    },
    # 商品 ETF
    "USO": {
        "name": "原油 ETF",
        "type": "etf",
        "yahoo": "USO",
    },
    # 宏观指标
    "VIX": {
        "name": "CBOE 波动率指数",
        "type": "index",
        "yahoo": "^VIX",
    },
    "DXY": {
        "name": "美元指数",
        "type": "index",
        "yahoo": "DX-Y.NYB",
    },
    "US10Y": {
        "name": "美国10年期国债收益率",
        "type": "index",
        "yahoo": "^TNX",
    },
}


def get_price_fallback(symbol: str) -> Dict:
    """由总司令设计的降级抓取逻辑 — 支持 15+ 个品种"""
    sym = symbol.upper()
    config = SYMBOL_LEGACY_CONFIG.get(sym)
    if not config:
        return {"error": f"不支持的标的: {sym}"}

    cache_key = f"price_{sym}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    result = None

    if config.get("type") == "crypto" and config.get("binance"):
        data = _fetch_json(f"https://api.binance.com/api/v3/ticker/24hr?symbol={config['binance']}")
        if "error" not in data:
            price = data.get("lastPrice")
            change = data.get("priceChangePercent")
            result = {"price": price, "change_24h": change, "source": "legacy_binance"}

    if not result and config.get("yahoo"):
        data = _fetch_json(f"https://query1.finance.yahoo.com/v8/finance/chart/{config['yahoo']}?interval=1d")
        if "error" not in data:
            meta = data.get("chart", {}).get("result", [{}])[0].get("meta", {})
            price = meta.get("regularMarketPrice")
            prev_close = meta.get("chartPreviousClose")
            if price:
                change_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else 0
                result = {"price": price, "change_24h": change_pct, "source": "legacy_yahoo"}

    if not result and config.get("type") == "forex" and config.get("gold_api_key"):
        api_key = config["gold_api_key"]
        data = _fetch_json(f"https://api.gold-api.com/price/{api_key}")
        if "error" not in data and data.get("price"):
            try:
                price = float(data.get("price", 0))
                if price > 0:
                    change = data.get("change", 0)
                    result = {"price": price, "change_24h": change, "source": "legacy_gold_api"}
            except (TypeError, ValueError):
                pass

    if not result:
        return {"error": f"所有数据源均无法获取 {sym}"}

    _cache_set(cache_key, result)
    return result
