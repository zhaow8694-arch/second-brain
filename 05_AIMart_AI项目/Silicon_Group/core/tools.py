import pandas as pd
from datetime import datetime
from core.market_data import get_market_data, get_historical_data, SYMBOL_CONFIG, get_macro_data


def _make_tool(name, description, func):
    """延迟创建 CrewAI 兼容的 Tool"""
    try:
        from crewai.tools import tool
    except ImportError:
        from langchain.tools import tool
        
    func.__name__ = name
    func.__doc__ = description
    return tool(name)(func)


def openbb_market_tool_func(symbol: str) -> str:
    """获取任何交易标的的实时市场价格和24小时涨跌幅。支持：黄金(XAU/USD)、白银(XAG/USD)、比特币(BTC/USDT)、以太坊(ETH/USDT)、Solana(SOL/USDT)、狗狗币(DOGE/USDT)、英伟达(NVDA)、苹果(AAPL)、特斯拉(TSLA)、微软(MSFT)、亚马逊(AMZN)、谷歌(GOOGL)、Meta(META)、标普500ETF(SPY)、纳斯达克ETF(QQQ)、道琼斯(DJI)、纳斯达克综合指数(IXIC)、原油ETF(USO)。输入只需标的代码。"""
    data = get_market_data(symbol)
    if "error" in data:
        return f"错误: {data['error']}"

    return f"""
### {data['symbol']} 实时军情报告
- **当前价格:** ${data['price']}
- **24小时涨跌:** {data.get('change_24h', 0):+.2f}%
- **数据来源:** {data['source']}
- **采集时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""


def get_market_summary_for_agent(symbol: str, days: int = 7) -> str:
    """获取指定标的最近 N 天的市场摘要数据（Markdown 表格格式），输入只需标的代码即可获取最近 5 天的开盘/最高/最低/收盘/成交量数据。"""
    hist = get_historical_data(symbol, days=days)
    if not hist:
        return f"错误: 无法获取 {symbol} 的历史数据"

    recent = hist[-5:]
    df = pd.DataFrame(recent)
    df = df.rename(columns={"date": "日期", "open": "开盘", "high": "最高", "low": "最低", "close": "收盘", "volume": "成交量"})
    table = df.to_markdown(index=False)

    current = get_market_data(symbol)
    price = current.get("price", "N/A")
    source = current.get("source", "N/A")

    return f"""
### {symbol} 市场摘要 (最近 {min(len(recent), days)} 天)
- **最新价格:** ${price}
- **数据来源:** {source}

#### K 线数据
{table}
"""


def macro_environment_tool(dummy=None) -> dict:
    """获取当前宏观市场环境数据，包括VIX波动率指数、美元指数DXY、美国10年期国债收益率US10Y。无需输入参数。"""
    macro_data = get_macro_data()
    lines = []
    for sym, data in macro_data.items():
        if "error" not in data:
            lines.append(f"- **{data['name']} ({sym}):** {data['price']} ({data.get('change_24h', 0):+.2f}%)")
        else:
            lines.append(f"- **{data['name']} ({sym}):** ⚠️ {data['error']}")
    # 返回必须的 output 字段；添加 reasoning_content 让 thinking 模式满足要求
    return {
        "reasoning_content": "Fetched macro indicators via get_macro_data().",
        "output": f"""### 宏观市场环境\n{chr(10).join(lines)}\n**采集时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    }


def available_symbols_tool(dummy=None) -> str:
    """获取所有可查询的交易标的列表，包含代码和中文名称。无需输入参数。"""
    lines = []
    for sym, config in SYMBOL_CONFIG.items():
        lines.append(f"- **{sym}** — {config['name']}")
    return f"""
### 可用交易标的 ({len(SYMBOL_CONFIG)} 个)
{chr(10).join(lines)}
"""


_openbb_tool_instance = None
_market_history_instance = None
_macro_env_instance = None
_available_symbols_instance = None


def get_openbb_tool():
    global _openbb_tool_instance
    if _openbb_tool_instance is None:
        _openbb_tool_instance = _make_tool("OpenBB_Financial_Intelligence", openbb_market_tool_func.__doc__, openbb_market_tool_func)
    return _openbb_tool_instance


def get_market_history_tool():
    global _market_history_instance
    if _market_history_instance is None:
        _market_history_instance = _make_tool("Market_History_Summary", get_market_summary_for_agent.__doc__, get_market_summary_for_agent)
    return _market_history_instance


def get_macro_tool():
    global _macro_env_instance
    if _macro_env_instance is None:
        _macro_env_instance = _make_tool("Macro_Environment", macro_environment_tool.__doc__, macro_environment_tool)
    return _macro_env_instance


def get_available_symbols_tool():
    global _available_symbols_instance
    if _available_symbols_instance is None:
        _available_symbols_instance = _make_tool("Available_Symbols", available_symbols_tool.__doc__, available_symbols_tool)
    return _available_symbols_instance


def call_openbb_tool(symbol: str) -> str:
    """直接调用 Tool 的包装函数（非 Agent 环境用）"""
    return get_market_data(symbol)
