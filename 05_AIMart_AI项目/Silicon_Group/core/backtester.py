"""
📊 策略回测器 (Backtester) — 历史数据验证策略

职责:
  1. 用历史 K 线数据验证交易策略
  2. 计算胜率、盈亏比、最大回撤、夏普比率
  3. 支持多种策略模板（均线交叉、突破、网格）
  4. 生成回测报告，回测通过才允许"实盘"

设计原则:
  - 完全独立模块，不修改任何现有代码
  - 只读方式访问历史数据
  - 所有输出写入 backtest_log/ 目录
  - 不涉及任何实盘交易
"""
import os
import json
from datetime import datetime
from core.battle_log import write_log

BACKTEST_DIR = "backtest_log"


def ensure_backtest_dir():
    if not os.path.exists(BACKTEST_DIR):
        os.makedirs(BACKTEST_DIR)


def run_backtest(symbol: str, strategy: str, historical_data: list, params: dict = None, session_id: str = "BACKTEST") -> dict:
    """运行策略回测

    用历史 K 线数据验证策略表现。
    计算关键指标：胜率、盈亏比、最大回撤、总收益率。

    Args:
        symbol: 标的代码
        strategy: 策略名称 (ma_cross/breakout/grid)
        historical_data: 历史 K 线数据列表
        params: 策略参数

    Returns:
        回测结果字典
    """
    ensure_backtest_dir()

    if not historical_data or len(historical_data) < 20:
        return {
            "symbol": symbol,
            "strategy": strategy,
            "error": "历史数据不足，至少需要 20 条 K 线",
            "passed": False,
        }

    strategy_map = {
        "ma_cross": _backtest_ma_cross,
        "breakout": _backtest_breakout,
        "grid": _backtest_grid,
    }

    backtest_func = strategy_map.get(strategy, _backtest_ma_cross)
    result = backtest_func(symbol, historical_data, params or {})

    result["symbol"] = symbol
    result["strategy"] = strategy
    result["data_points"] = len(historical_data)
    result["timestamp"] = datetime.now().isoformat()

    win_rate = result.get("win_rate", 0)
    result["passed"] = win_rate >= 50 and result.get("max_drawdown", 100) < 20

    safe_symbol = symbol.replace("/", "_")
    backtest_file = os.path.join(BACKTEST_DIR, f"{safe_symbol}_{strategy}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(backtest_file, "w") as f:
        json.dump(result, f, indent=2)

    write_log(
        session_id,   # 修复: 原先硬编码为字符串 "BACKTEST"，导致数据库内日志无法关联到实际会话
        "BACKTEST",
        symbol,
        json.dumps({
            "strategy": strategy,
            "win_rate": round(win_rate, 1),
            "passed": result["passed"],
            "total_return": round(result.get("total_return", 0), 2),
        }, ensure_ascii=False),
    )

    return result


def _backtest_ma_cross(symbol: str, data: list, params: dict) -> dict:
    """均线交叉策略回测

    规则:
      - 短期均线上穿长期均线 → 买入
      - 短期均线下穿长期均线 → 卖出
      - 默认: MA5 上穿 MA20 买入, 下穿卖出
    """
    short_period = params.get("short_period", 5)
    long_period = params.get("long_period", 20)

    if len(data) < long_period + 1:
        return {"error": f"数据不足，需要至少 {long_period + 1} 条", "passed": False}

    closes = [c["close"] for c in data]
    trades = []
    position = None
    entry_price = 0

    for i in range(long_period, len(closes)):
        short_ma = sum(closes[i - short_period:i]) / short_period
        long_ma = sum(closes[i - long_period:i]) / long_period
        prev_short = sum(closes[i - short_period - 1:i - 1]) / short_period
        prev_long = sum(closes[i - long_period - 1:i - 1]) / long_period

        if prev_short <= prev_long and short_ma > long_ma:
            if position != "long":
                if position == "short":
                    profit_pct = (entry_price - closes[i]) / entry_price * 100
                    trades.append({"type": "cover", "price": closes[i], "profit_pct": round(profit_pct, 2)})
                position = "long"
                entry_price = closes[i]
                trades.append({"type": "buy", "price": closes[i]})

        elif prev_short >= prev_long and short_ma < long_ma:
            if position != "short":
                if position == "long":
                    profit_pct = (closes[i] - entry_price) / entry_price * 100
                    trades.append({"type": "sell", "price": closes[i], "profit_pct": round(profit_pct, 2)})
                position = "short"
                entry_price = closes[i]
                trades.append({"type": "short", "price": closes[i]})

    if position == "long":
        profit_pct = (closes[-1] - entry_price) / entry_price * 100
        trades.append({"type": "close_long", "price": closes[-1], "profit_pct": round(profit_pct, 2)})
    elif position == "short":
        profit_pct = (entry_price - closes[-1]) / entry_price * 100
        trades.append({"type": "close_short", "price": closes[-1], "profit_pct": round(profit_pct, 2)})

    closed_trades = [t for t in trades if "profit_pct" in t]
    wins = [t for t in closed_trades if t["profit_pct"] > 0]
    losses = [t for t in closed_trades if t["profit_pct"] <= 0]

    win_rate = (len(wins) / len(closed_trades) * 100) if closed_trades else 0
    total_return = sum(t["profit_pct"] for t in closed_trades) if closed_trades else 0
    avg_win = sum(t["profit_pct"] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t["profit_pct"] for t in losses) / len(losses) if losses else 0

    equity_curve = [100]
    for t in closed_trades:
        equity_curve.append(equity_curve[-1] * (1 + t["profit_pct"] / 100))
    max_drawdown = _calculate_max_drawdown(equity_curve)

    return {
        "total_return": round(total_return, 2),
        "win_rate": round(win_rate, 1),
        "total_trades": len(closed_trades),
        "wins": len(wins),
        "losses": len(losses),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "max_drawdown": round(max_drawdown, 2),
        "profit_factor": round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else float("inf"),
        "trades": trades,
        "params": {"short_period": short_period, "long_period": long_period},
    }


def _backtest_breakout(symbol: str, data: list, params: dict) -> dict:
    """突破策略回测

    规则:
      - 价格突破前 N 日高点 → 买入
      - 价格跌破前 N 日低点 → 卖出
      - 默认: 突破 20 日高点买入, 跌破 20 日低点卖出
    """
    lookback = params.get("lookback", 20)

    if len(data) < lookback + 1:
        return {"error": f"数据不足，需要至少 {lookback + 1} 条", "passed": False}

    closes = [c["close"] for c in data]
    highs = [c["high"] for c in data]
    lows = [c["low"] for c in data]

    trades = []
    position = None
    entry_price = 0

    for i in range(lookback, len(closes)):
        high_n = max(highs[i - lookback:i])
        low_n = min(lows[i - lookback:i])

        if closes[i] > high_n and position != "long":
            if position == "short":
                profit_pct = (entry_price - closes[i]) / entry_price * 100
                trades.append({"type": "cover", "price": closes[i], "profit_pct": round(profit_pct, 2)})
            position = "long"
            entry_price = closes[i]
            trades.append({"type": "buy", "price": closes[i], "breakout": "high"})

        elif closes[i] < low_n and position != "short":
            if position == "long":
                profit_pct = (closes[i] - entry_price) / entry_price * 100
                trades.append({"type": "sell", "price": closes[i], "profit_pct": round(profit_pct, 2)})
            position = "short"
            entry_price = closes[i]
            trades.append({"type": "short", "price": closes[i], "breakout": "low"})

    if position == "long":
        profit_pct = (closes[-1] - entry_price) / entry_price * 100
        trades.append({"type": "close_long", "price": closes[-1], "profit_pct": round(profit_pct, 2)})
    elif position == "short":
        profit_pct = (entry_price - closes[-1]) / entry_price * 100
        trades.append({"type": "close_short", "price": closes[-1], "profit_pct": round(profit_pct, 2)})

    closed_trades = [t for t in trades if "profit_pct" in t]
    wins = [t for t in closed_trades if t["profit_pct"] > 0]
    losses = [t for t in closed_trades if t["profit_pct"] <= 0]

    win_rate = (len(wins) / len(closed_trades) * 100) if closed_trades else 0
    total_return = sum(t["profit_pct"] for t in closed_trades) if closed_trades else 0
    avg_win = sum(t["profit_pct"] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t["profit_pct"] for t in losses) / len(losses) if losses else 0

    equity_curve = [100]
    for t in closed_trades:
        equity_curve.append(equity_curve[-1] * (1 + t["profit_pct"] / 100))
    max_drawdown = _calculate_max_drawdown(equity_curve)

    return {
        "total_return": round(total_return, 2),
        "win_rate": round(win_rate, 1),
        "total_trades": len(closed_trades),
        "wins": len(wins),
        "losses": len(losses),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "max_drawdown": round(max_drawdown, 2),
        "profit_factor": round(abs(avg_win / avg_loss), 2) if avg_loss != 0 else float("inf"),
        "trades": trades,
        "params": {"lookback": lookback},
    }


def _backtest_grid(symbol: str, data: list, params: dict) -> dict:
    """网格策略回测

    规则:
      - 在价格区间内设置多层网格
      - 每跌一格买入，每涨一格卖出
      - 默认: 10 层网格, 每层 1% 间距
    """
    grid_levels = params.get("grid_levels", 10)
    grid_spacing = params.get("grid_spacing", 1.0)

    if len(data) < 10:
        return {"error": "数据不足", "passed": False}

    closes = [c["close"] for c in data]
    price_range = max(closes) - min(closes)
    grid_step = price_range / grid_levels

    grid_prices = [min(closes) + i * grid_step for i in range(grid_levels + 1)]
    holdings = [0] * len(grid_prices)
    cash = 10000
    trades = []

    for price in closes:
        for i, grid_price in enumerate(grid_prices):
            if price <= grid_price and holdings[i] == 0:
                shares = cash * 0.1 / price
                holdings[i] = shares
                cash -= shares * price
                trades.append({"type": "buy", "price": price, "grid": i, "shares": round(shares, 4)})
                break

        for i in range(len(grid_prices) - 1, -1, -1):
            if price >= grid_prices[i] and holdings[i] > 0:
                cash += holdings[i] * price
                trades.append({"type": "sell", "price": price, "grid": i, "shares": round(holdings[i], 4)})
                holdings[i] = 0
                break

    total_value = cash + sum(h * closes[-1] for h in holdings)
    total_return = (total_value - 10000) / 10000 * 100

    # 计算实际胜率和回扈（不再硬编码 100%）
    buy_trades = [t for t in trades if t["type"] == "buy"]
    sell_trades = [t for t in trades if t["type"] == "sell"]
    pairs = min(len(buy_trades), len(sell_trades))
    wins = 0
    pair_returns = []
    for i in range(pairs):
        profit = (sell_trades[i]["price"] - buy_trades[i]["price"]) / buy_trades[i]["price"] * 100
        pair_returns.append(profit)
        if profit > 0:
            wins += 1

    win_rate = (wins / pairs * 100) if pairs else 0.0
    equity_curve = [100]
    for r in pair_returns:
        equity_curve.append(equity_curve[-1] * (1 + r / 100))
    max_drawdown = _calculate_max_drawdown(equity_curve)
    closed_trades = sell_trades

    return {
        "total_return": round(total_return, 2),
        "win_rate": round(win_rate, 1),
        "total_trades": len(closed_trades),
        "wins": wins,
        "losses": pairs - wins,
        "avg_win": round(sum(r for r in pair_returns if r > 0) / wins, 2) if wins else 0,
        "avg_loss": round(sum(r for r in pair_returns if r <= 0) / max(pairs - wins, 1), 2),
        "max_drawdown": round(max_drawdown, 2),
        "profit_factor": float("inf") if pairs == wins else round(
            abs(sum(r for r in pair_returns if r > 0)) / max(abs(sum(r for r in pair_returns if r <= 0)), 0.001), 2
        ),
        "trades": trades[:50],
        "params": {"grid_levels": grid_levels, "grid_spacing": grid_spacing},
    }


def _calculate_max_drawdown(equity_curve: list) -> float:
    """计算最大回撤百分比"""
    peak = equity_curve[0]
    max_dd = 0
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak * 100
        if dd > max_dd:
            max_dd = dd
    return max_dd


def get_available_strategies() -> dict:
    """获取可用策略列表"""
    return {
        "ma_cross": {
            "name": "均线交叉策略",
            "description": "短期均线上穿长期均线买入，下穿卖出",
            "default_params": {"short_period": 5, "long_period": 20},
        },
        "breakout": {
            "name": "突破策略",
            "description": "价格突破前 N 日高点买入，跌破前 N 日低点卖出",
            "default_params": {"lookback": 20},
        },
        "grid": {
            "name": "网格策略",
            "description": "在价格区间内设置多层网格，低买高卖",
            "default_params": {"grid_levels": 10, "grid_spacing": 1.0},
        },
    }


def get_backtest_status() -> dict:
    """获取回测系统状态"""
    ensure_backtest_dir()
    reports = [f for f in os.listdir(BACKTEST_DIR) if f.endswith(".json")] if os.path.exists(BACKTEST_DIR) else []
    return {
        "total_backtests": len(reports),
        "latest_backtest": sorted(reports, reverse=True)[0] if reports else None,
        "available_strategies": list(get_available_strategies().keys()),
    }
