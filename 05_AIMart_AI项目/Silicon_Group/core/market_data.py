import logging
from core.market_data_legacy import get_price_fallback, SYMBOL_LEGACY_CONFIG

logger = logging.getLogger(__name__)

OPENBB_AVAILABLE = False
try:
    from openbb import obb
    OPENBB_AVAILABLE = True
except ImportError:
    pass

SYMBOL_CONFIG = {}
for k, v in SYMBOL_LEGACY_CONFIG.items():
    SYMBOL_CONFIG[k] = {"name": v["name"], "yahoo": v.get("yahoo"), "binance": v.get("binance")}


def get_market_data(symbol: str, days: int = 7) -> dict:
    """帝国双模引擎：优先 OpenBB，失败则自动切换 Legacy"""
    sym = symbol.upper()

    if OPENBB_AVAILABLE:
        try:
            config = SYMBOL_LEGACY_CONFIG.get(sym, {})
            if config.get("type") == "crypto":
                target = config.get("yahoo", sym)
                res = obb.equity.price.historical(symbol=target, provider="yfinance", limit=days)
            elif config.get("type") == "forex":
                target = config.get("yahoo", sym)
                res = obb.equity.price.historical(symbol=target, provider="yfinance", limit=days)
            else:
                target = config.get("yahoo", sym)
                res = obb.equity.price.historical(symbol=target, provider="yfinance", limit=days)
            df = res.to_dataframe()
            last_price = df['close'].iloc[-1]
            prev_close = df['close'].iloc[-2] if len(df) > 1 else last_price
            change_pct = round((last_price - prev_close) / prev_close * 100, 2)
            return {
                "symbol": sym,
                "price": round(float(last_price), 2),
                "change_24h": change_pct,
                "source": f"OpenBB/yfinance",
                "status": "Success",
            }
        except Exception:
            pass

    return get_price_fallback(sym)


def get_price(symbol: str) -> dict:
    """获取单个标的实时价格（向后兼容）"""
    raw = get_market_data(symbol)
    if "error" in raw:
        return raw
    price = raw.get("price", 0)
    try:
        price = float(price)
    except (TypeError, ValueError):
        return {"error": f"无效价格: {price}"}

    change_24h = raw.get("change_24h", 0)
    try:
        change_24h = float(change_24h)
    except (TypeError, ValueError):
        change_24h = 0.0

    return {
        "symbol": symbol,
        "price": price,
        "change_24h": change_24h,
        "source": raw.get("source", "legacy"),
    }


def get_all_prices() -> dict:
    """获取所有配置标的的实时价格"""
    result = {}
    for symbol in SYMBOL_CONFIG:
        result[symbol] = get_price(symbol)
    return result


def get_historical_data(symbol: str, days: int = 30) -> list:
    """获取历史 K 线数据（向后兼容）"""
    import yfinance as yf
    sym = symbol.upper()
    config = SYMBOL_LEGACY_CONFIG.get(sym, {})
    try:
        ticker = config.get("yahoo", sym)
        actual_days = max(days, 60)
        df = yf.download(ticker, period=f"{actual_days}d", progress=False)
        if df.empty:
            return []

        records = []
        for idx, row in df.iterrows():
            records.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"].iloc[0]), 2),
                "high": round(float(row["High"].iloc[0]), 2),
                "low": round(float(row["Low"].iloc[0]), 2),
                "close": round(float(row["Close"].iloc[0]), 2),
                "volume": int(row["Volume"].iloc[0]),
            })
        return records[-days:]
    except Exception:
        return []


def get_market_status() -> dict:
    """获取行情引擎状态"""
    return {
        "symbols": list(SYMBOL_CONFIG.keys()),
        "openbb_available": OPENBB_AVAILABLE,
        "cache_duration_seconds": 60,
    }


MACRO_SYMBOLS = {
    "VIX": "CBOE 波动率指数",
    "DXY": "美元指数",
    "US10Y": "美国10年期国债收益率",
}


def get_macro_data() -> dict:
    """获取宏观市场环境数据（VIX、DXY、US10Y）"""
    result = {}
    for sym, name in MACRO_SYMBOLS.items():
        try:
            data = get_market_data(sym)
            if "error" not in data:
                result[sym] = {
                    "name": name,
                    "price": data.get("price"),
                    "change_24h": data.get("change_24h", 0),
                    "source": data.get("source", "legacy"),
                }
            else:
                result[sym] = {"name": name, "error": data["error"]}
        except Exception as e:
            result[sym] = {"name": name, "error": str(e)}
    return result
