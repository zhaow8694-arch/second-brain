"""
💼 投资组合管理 (Portfolio) — 虚拟仓位与风险监控 (SQLite Version)

职责:
  1. 记录虚拟仓位（多标的持仓、成本、数量）
  2. 实时计算盈亏（浮动盈亏、已实现盈亏）
  3. 风险敞口监控（总敞口、单一标的敞口上限）
  4. 交易流水记录

设计原则:
  - 所有数据存储在 SQLite 数据库中，实现 ACID 强一致性
  - 纯虚拟仓位，不涉及任何实盘交易
  - 与 market_data 联动获取实时估值
"""
import os
import json
from datetime import datetime
from core.battle_log import write_log
from core.database import get_connection

def _get_cash() -> float:
    conn = get_connection()
    row = conn.execute("SELECT balance FROM paper_account WHERE id = 1").fetchone()
    conn.close()
    return row['balance'] if row else 100000.0

def _update_cash(amount: float):
    conn = get_connection()
    conn.execute("UPDATE paper_account SET balance = balance + ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (amount,))
    conn.commit()
    conn.close()

def open_position(session_id: str, symbol: str, direction: str, quantity: float, entry_price: float) -> dict:
    """开仓"""
    cost = quantity * entry_price
    current_cash = _get_cash()
    
    if current_cash < cost and direction == "long":
        return {"error": f"现金不足: 需要 ${cost:.2f}, 可用 ${current_cash:.2f}"}

    position_id = f"{symbol}_{direction}_{datetime.now().strftime('%H%M%S')}"

    conn = get_connection()
    
    # 检查是否已有同向持仓
    existing = conn.execute(
        "SELECT id, quantity, entry_price FROM paper_trades WHERE symbol = ? AND direction = ? AND status = 'open'",
        (symbol, direction)
    ).fetchone()

    if existing:
        new_qty = existing['quantity'] + quantity
        new_entry = (existing['entry_price'] * existing['quantity'] + entry_price * quantity) / new_qty
        conn.execute(
            "UPDATE paper_trades SET quantity = ?, entry_price = ? WHERE id = ?",
            (new_qty, new_entry, existing['id'])
        )
        position_id = existing['id']
    else:
        conn.execute(
            "INSERT INTO paper_trades (id, session_id, symbol, direction, quantity, entry_price, status) VALUES (?, ?, ?, ?, ?, ?, 'open')",
            (position_id, session_id, symbol, direction, quantity, entry_price)
        )

    conn.commit()
    conn.close()

    if direction == "long":
        _update_cash(-cost)

    write_log(session_id, "PORTFOLIO_OPEN", symbol, json.dumps({
        "direction": direction, "quantity": quantity, "price": entry_price, "cost": round(cost, 2),
    }, ensure_ascii=False))

    return {
        "position_id": position_id,
        "symbol": symbol,
        "direction": direction,
        "quantity": quantity,
        "entry_price": entry_price,
        "cost": round(cost, 2),
        "cash_remaining": round(_get_cash(), 2),
    }

def close_position(session_id: str, symbol: str, direction: str, exit_price: float, quantity: float = None) -> dict:
    """平仓"""
    conn = get_connection()
    position = conn.execute(
        "SELECT id, quantity, entry_price FROM paper_trades WHERE symbol = ? AND direction = ? AND status = 'open'",
        (symbol, direction)
    ).fetchone()

    if not position:
        conn.close()
        return {"error": f"无 {symbol} {direction} 仓位"}

    close_qty = quantity or position['quantity']
    if close_qty > position['quantity']:
        close_qty = position['quantity']

    if direction == "long":
        pnl = (exit_price - position['entry_price']) * close_qty
        _update_cash(close_qty * exit_price)
    else:
        pnl = (position['entry_price'] - exit_price) * close_qty
        _update_cash(close_qty * (position['entry_price'] + (position['entry_price'] - exit_price)))

    pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100
    if direction == "short":
        pnl_pct = -pnl_pct

    # 更新数据库
    if close_qty == position['quantity']:
        conn.execute(
            "UPDATE paper_trades SET status = 'closed', exit_price = ?, pnl = ?, close_time = CURRENT_TIMESTAMP WHERE id = ?",
            (exit_price, pnl, position['id'])
        )
    else:
        # 部分平仓：更新原仓位数量，并插入一条已平仓记录
        conn.execute("UPDATE paper_trades SET quantity = quantity - ? WHERE id = ?", (close_qty, position['id']))
        conn.execute(
            "INSERT INTO paper_trades (id, session_id, symbol, direction, quantity, entry_price, exit_price, pnl, status, close_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'closed', CURRENT_TIMESTAMP)",
            (f"{position['id']}_partial_{datetime.now().strftime('%H%M%S')}", session_id, symbol, direction, close_qty, position['entry_price'], exit_price, pnl)
        )

    conn.commit()
    conn.close()

    write_log(session_id, "PORTFOLIO_CLOSE", symbol, json.dumps({
        "direction": direction, "quantity": close_qty, "exit_price": exit_price,
        "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2),
    }, ensure_ascii=False))

    return {
        "symbol": symbol,
        "direction": direction,
        "quantity": close_qty,
        "exit_price": exit_price,
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
        "cash_remaining": round(_get_cash(), 2),
    }

def update_prices(prices: dict):
    """仅在内存中计算，不持久化浮动盈亏"""
    pass

def get_portfolio_summary() -> dict:
    """获取投资组合摘要 (SQLite版)"""
    conn = get_connection()
    
    # 获取敞口仓位
    open_positions = conn.execute("SELECT * FROM paper_trades WHERE status = 'open'").fetchall()
    
    # 获取已实现盈亏和交易次数
    stats = conn.execute("SELECT SUM(pnl) as total_pnl, COUNT(*) as trades FROM paper_trades WHERE status = 'closed'").fetchone()
    realized_pnl = stats['total_pnl'] or 0.0
    total_trades = stats['trades'] or 0

    # 获取最近订单
    recent = conn.execute("SELECT * FROM paper_trades ORDER BY open_time DESC LIMIT 10").fetchall()
    conn.close()

    from core.market_data import get_price
    
    total_position_value = 0
    total_unrealized = 0
    positions_detail = []

    for pos in open_positions:
        symbol = pos['symbol']
        try:
            price_data = get_price(symbol)
            current_price = price_data['price'] if 'error' not in price_data else pos['entry_price']
        except:
            current_price = pos['entry_price']
            
        value = pos['quantity'] * current_price
        total_position_value += value
        
        if pos['direction'] == 'long':
            unrealized_pnl = (current_price - pos['entry_price']) * pos['quantity']
            pnl_pct = (current_price - pos['entry_price']) / pos['entry_price'] * 100
        else:
            unrealized_pnl = (pos['entry_price'] - current_price) * pos['quantity']
            pnl_pct = (pos['entry_price'] - current_price) / pos['entry_price'] * 100
            
        total_unrealized += unrealized_pnl
            
        positions_detail.append({
            "symbol": symbol,
            "direction": pos['direction'],
            "quantity": pos['quantity'],
            "entry_price": pos['entry_price'],
            "current_price": current_price,
            "value": round(value, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "unrealized_pnl_pct": round(pnl_pct, 2),
        })

    cash = _get_cash()
    total_equity = cash + total_position_value

    recent_orders = []
    for r in recent:
        recent_orders.append({
            "time": r['open_time'] if r['status'] == 'open' else r['close_time'],
            "type": r['status'],
            "symbol": r['symbol'],
            "direction": r['direction'],
            "quantity": r['quantity'],
            "price": r['entry_price'] if r['status'] == 'open' else r['exit_price'],
            "pnl": r['pnl'] if r['pnl'] else 0.0,
        })

    return {
        "cash": round(cash, 2),
        "position_value": round(total_position_value, 2),
        "total_equity": round(total_equity, 2),
        "unrealized_pnl": round(total_unrealized, 2),
        "realized_pnl": round(realized_pnl, 2),
        "total_pnl": round(total_unrealized + realized_pnl, 2),
        "total_trades": total_trades,
        "positions": positions_detail,
        "position_count": len(positions_detail),
        "recent_orders": recent_orders,
    }

def get_portfolio_status() -> dict:
    """获取投资组合状态（供 dashboard 使用）"""
    summary = get_portfolio_summary()
    return {
        "total_equity": summary["total_equity"],
        "cash": summary["cash"],
        "position_count": summary["position_count"],
        "total_trades": summary["total_trades"],
        "total_pnl": summary["total_pnl"],
        "realized_pnl": summary["realized_pnl"],
    }

def connect_futures_u_margin():
    from core.financial_gateway import _get_exchange, get_mode
    if get_mode() == "virtual":
        print("⚠️ 当前为虚拟模式，不会连接交易所")
        return None
    try:
        client = _get_exchange()
        balance = client.fetch_balance()
        usdt_total = balance.get("total", {}).get("USDT", 0)
        print(f"✅ 合约战场就绪！可用 USDT: {usdt_total}")
        return client
    except Exception as e:
        print(f"❌ 合约连接失败: {e}")
        return None
