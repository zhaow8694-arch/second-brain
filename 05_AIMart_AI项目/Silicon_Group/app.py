import streamlit as st
import pandas as pd
from datetime import datetime
import json
import sqlite3
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import init_db, get_connection
init_db()

st.set_page_config(
    page_title="硅基远征军统帅部",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "silicon_empire.db")

def query_db(query, params=()):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"数据库查询失败: {e}")
        return pd.DataFrame()

def execute_db(query, params=()):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"数据库执行失败: {e}")
        return False

def get_binance_status():
    """获取 Binance 连接状态和余额"""
    try:
        from core.financial_gateway import check_connection, fetch_balance, get_mode, get_positions
        conn_status = check_connection()
        balance = fetch_balance()
        positions = get_positions()
        mode = get_mode()
        return {
            "mode": mode,
            "connection": conn_status,
            "balance": balance,
            "positions": positions,
        }
    except Exception as e:
        return {"mode": "error", "error": str(e)}

def get_scheduler_status():
    """获取调度器状态"""
    try:
        from core.scheduler import get_status
        return get_status()
    except Exception as e:
        return {"error": str(e)}

def get_latest_report():
    """获取最新分析报告内容"""
    try:
        report_dir = "chief_log"
        if not os.path.exists(report_dir):
            return None
        files = [f for f in os.listdir(report_dir) if f.startswith("FINANCIAL_scheduler") and f.endswith(".md")]
        if not files:
            return None
        latest = sorted(files, reverse=True)[0]
        with open(os.path.join(report_dir, latest), "r", encoding="utf-8") as f:
            content = f.read()
        return {"file": latest, "content": content[:3000]}
    except Exception:
        return None

with st.sidebar:
    st.title("⚔️ 统帅部")
    st.markdown("---")
    st.markdown("**系统控制**")
    if st.button("🔄 刷新数据", width="stretch"):
        st.rerun()
    st.markdown("---")

    binance_info = get_binance_status()
    mode = binance_info.get("mode", "unknown")
    mode_icon = "🔴" if mode == "live" else "🟡" if mode == "virtual" else "⚫"
    st.markdown(f"**网关模式:** {mode_icon} {mode.upper()}")

    conn = binance_info.get("connection", {})
    if conn.get("status") == "ok":
        st.success("✅ Binance 已连接")
        bal = binance_info.get("balance", {})
        if "total" in bal:
            usdt = bal["total"].get("USDT", 0)
            st.metric("USDT 余额", f"${usdt:,.2f}")
    else:
        st.warning(f"⚠️ Binance: {conn.get('message', '未连接')}")

    scheduler_info = get_scheduler_status()
    if isinstance(scheduler_info, dict) and "error" not in scheduler_info:
        if scheduler_info.get("active"):
            st.success(f"✅ 调度器运行中 (第 {scheduler_info.get('current_cycle', 0)} 轮)")
        else:
            st.info("⏸️ 调度器未运行")
    else:
        st.info("⏸️ 调度器状态未知")

    st.markdown("---")
    st.caption(f"最后刷新: {datetime.now().strftime('%H:%M:%S')}")
    st.caption("*数据来自 silicon_empire.db + 实时 API*")

st.title("⚔️ 硅基远征军 (Silicon Expeditionary Force) - 统帅部")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 全军态势", "💼 影子实盘", "💰 实盘交易",
    "⏰ 调度器", "📡 行情快报", "🔧 系统管理"
])

# ========================================================================
# Tab 1: 全军态势
# ========================================================================
with tab1:
    st.header("全军行动日志")

    col1, col2, col3, col4 = st.columns(4)
    log_df = query_db("SELECT * FROM battle_logs")
    if not log_df.empty:
        total_actions = len(log_df)
        session_count = log_df['session_id'].nunique()
        reject_count = len(log_df[log_df['stage'] == 'QUALITY_GATE_REJECT'])
        scheduler_count = len(log_df[log_df['session_id'].str.contains('scheduler', case=False)])

        col1.metric("累计行动次数", total_actions)
        col2.metric("战役发单数", session_count)
        col3.metric("宪兵队拦截次数", reject_count, delta="-风险规避", delta_color="inverse")
        col4.metric("调度器执行次数", scheduler_count)

        st.subheader("最近作战日志")
        recent_logs = log_df.sort_values(by='timestamp', ascending=False).head(50)
        st.dataframe(recent_logs[['timestamp', 'session_id', 'stage', 'target', 'content']], width="stretch")
    else:
        col1.metric("累计行动次数", 0)
        col2.metric("战役发单数", 0)
        col3.metric("宪兵队拦截次数", 0)
        col4.metric("调度器执行次数", 0)
        st.info("🛡️ 尚无作战日志数据。请先运行一次金融任务。")

    st.markdown("---")
    st.subheader("最新分析报告")
    report = get_latest_report()
    if report:
        st.caption(f"报告文件: {report['file']}")
        st.text_area("报告摘要", report["content"], height=300)
    else:
        st.info("暂无分析报告")

# ========================================================================
# Tab 2: 影子实盘 (Paper Trading)
# ========================================================================
with tab2:
    st.header("财务主权 - 模拟战果")

    account_df = query_db("SELECT * FROM paper_account WHERE id = 1")
    cash = account_df['balance'].iloc[0] if not account_df.empty else 100000.0

    trades_df = query_db("SELECT * FROM paper_trades")

    if not trades_df.empty:
        closed_trades = trades_df[trades_df['status'] == 'closed']
        realized_pnl = closed_trades['pnl'].sum() if not closed_trades.empty else 0.0
        open_trades = trades_df[trades_df['status'] == 'open']

        col1, col2, col3 = st.columns(3)
        col1.metric("可用资金 (USDT)", f"${cash:,.2f}")
        col2.metric("累计已实现盈亏", f"${realized_pnl:,.2f}", delta=f"{realized_pnl:,.2f}")
        col3.metric("当前敞口数", len(open_trades))

        st.subheader("当前持仓")
        if not open_trades.empty:
            st.dataframe(open_trades[['symbol', 'direction', 'quantity', 'entry_price', 'open_time']], width="stretch")
        else:
            st.info("当前无持仓")

        st.subheader("历史战绩")
        if not closed_trades.empty:
            st.dataframe(closed_trades[['symbol', 'direction', 'quantity', 'entry_price', 'exit_price', 'pnl', 'close_time']], width="stretch")

            st.subheader("资金曲线")
            curve_data = closed_trades[['close_time', 'pnl']].copy()
            curve_data['close_time'] = pd.to_datetime(curve_data['close_time'])
            curve_data = curve_data.sort_values('close_time')
            curve_data['cumulative_pnl'] = curve_data['pnl'].cumsum()
            st.line_chart(curve_data.set_index('close_time')['cumulative_pnl'])
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("初始资金 (USDT)", f"${cash:,.2f}")
        col2.metric("累计已实现盈亏", "$0.00")
        col3.metric("当前敞口数", 0)
        st.info("📭 尚无交易记录。等待金融军团首次出击。")

# ========================================================================
# Tab 3: 实盘交易 (Live Trading)
# ========================================================================
with tab3:
    st.header("💰 实盘交易记录 (Binance U本位合约)")

    binance_info = get_binance_status()
    mode = binance_info.get("mode", "unknown")

    col1, col2, col3 = st.columns(3)
    col1.metric("网关模式", mode.upper())

    conn = binance_info.get("connection", {})
    if conn.get("status") == "ok":
        col2.success("✅ 已连接")
        bal = binance_info.get("balance", {})
        if "total" in bal:
            usdt = bal["total"].get("USDT", 0)
            col3.metric("USDT 余额", f"${usdt:,.2f}")
    else:
        col2.warning("⚠️ 未连接")
        col3.metric("USDT 余额", "-")

    st.markdown("---")
    st.subheader("当前持仓 (交易所实时)")

    positions = binance_info.get("positions", [])
    if positions and len(positions) > 0 and "error" not in positions[0]:
        pos_df = pd.DataFrame(positions)
        st.dataframe(pos_df, width="stretch")

        total_upnl = sum(p.get("unrealized_pnl", 0) for p in positions)
        st.metric("浮动盈亏", f"${total_upnl:+.2f}", delta=f"{total_upnl:+.2f}")
    else:
        st.info("当前无持仓或无法获取持仓数据")

    st.markdown("---")
    st.subheader("历史实盘订单 (数据库)")

    live_trades = query_db("SELECT * FROM live_trades ORDER BY created_at DESC LIMIT 50")
    if not live_trades.empty:
        st.dataframe(live_trades, width="stretch")

        total_trades = len(live_trades)
        buy_trades = len(live_trades[live_trades['side'] == 'buy'])
        sell_trades = len(live_trades[live_trades['side'] == 'sell'])
        col1, col2, col3 = st.columns(3)
        col1.metric("总订单数", total_trades)
        col2.metric("开多", buy_trades)
        col3.metric("开空", sell_trades)
    else:
        st.info("📭 尚无实盘交易记录")

# ========================================================================
# Tab 4: 调度器
# ========================================================================
with tab4:
    st.header("⏰ 调度器运行状态")

    scheduler_info = get_scheduler_status()
    if isinstance(scheduler_info, dict) and "error" not in scheduler_info:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("运行状态", "🟢 运行中" if scheduler_info.get("active") else "🔴 已停止")
        col2.metric("当前轮次", scheduler_info.get("current_cycle", 0))
        col3.metric("扫描标的数", scheduler_info.get("tradable_symbols", 0))
        col4.metric("扫描间隔", f"{scheduler_info.get('interval_hours', 4)} 小时")

        if scheduler_info.get("last_run"):
            st.info(f"⏳ 上次执行: {scheduler_info['last_run']}")
        if scheduler_info.get("next_run"):
            st.info(f"⏰ 下次执行: {scheduler_info['next_run']}")
    else:
        st.warning("⚠️ 调度器状态不可用")

    st.markdown("---")
    st.subheader("调度器运行历史")

    runs_df = query_db("SELECT * FROM scheduler_runs ORDER BY started_at DESC LIMIT 20")
    if not runs_df.empty:
        display_df = runs_df[['cycle', 'status', 'started_at', 'finished_at', 'symbols_count', 'summary']].copy()
        display_df['status'] = display_df['status'].apply(lambda x: "✅" if x == "success" else "❌")
        st.dataframe(display_df, width="stretch")

        success_count = len(runs_df[runs_df['status'] == 'success'])
        fail_count = len(runs_df[runs_df['status'] == 'failed'])
        col1, col2 = st.columns(2)
        col1.metric("成功次数", success_count)
        col2.metric("失败次数", fail_count)
    else:
        st.info("暂无调度器运行记录")

    st.markdown("---")
    st.subheader("调度器日志文件")
    log_dir = "scheduler_log"
    if os.path.exists(log_dir):
        files = [f for f in os.listdir(log_dir) if f.endswith(".json")]
        if files:
            latest_log = sorted(files, reverse=True)[0]
            try:
                with open(os.path.join(log_dir, latest_log), "r", encoding="utf-8") as f:
                    history = json.load(f)
                st.json(history[-5:] if len(history) > 5 else history)
            except Exception:
                st.info("无法读取调度器日志")
        else:
            st.info("暂无调度器日志文件")

# ========================================================================
# Tab 5: 行情快报
# ========================================================================
with tab5:
    st.header("📡 全球行情快报")
    st.caption("数据通过 Binance API + yfinance 实时获取，每次刷新更新。")

    WATCHLIST = {
        "BTC/USDT": "比特币",
        "ETH/USDT": "以太坊",
        "SOL/USDT": "Solana",
        "DOGE/USDT": "狗狗币",
        "XRP/USDT": "瑞波币",
        "ADA/USDT": "Cardano",
        "LINK/USDT": "Chainlink",
        "AVAX/USDT": "Avalanche",
        "BCH/USDT": "比特币现金",
    }

    with st.spinner("正在拉取行情数据..."):
        try:
            from core.market_data import get_price
            rows = []
            for sym, name in WATCHLIST.items():
                try:
                    data = get_price(sym)
                    price = data.get("price", "N/A")
                    chg = data.get("change_24h", 0)
                    src = data.get("source", "unknown")
                    rows.append({
                        "标的": f"{name} ({sym})",
                        "最新价": f"${price:,.2f}" if isinstance(price, (int, float)) else str(price),
                        "24h涨跌%": chg,
                        "数据源": src,
                    })
                except Exception as e:
                    rows.append({"标的": f"{name} ({sym})", "最新价": "获取失败", "24h涨跌%": 0, "数据源": str(e)})

            if rows:
                mkt_df = pd.DataFrame(rows)
                cols = st.columns(len(rows))
                for i, row in enumerate(rows):
                    chg = row["24h涨跌%"]
                    chg_str = f"{chg:+.2f}%" if isinstance(chg, (int, float)) else "-"
                    delta_color = "normal" if (isinstance(chg, (int, float)) and chg >= 0) else "inverse"
                    cols[i].metric(
                        label=row["标的"],
                        value=row["最新价"],
                        delta=chg_str,
                        delta_color=delta_color,
                    )

                st.markdown("---")
                st.subheader("详细数据")
                st.dataframe(mkt_df, width="stretch")
        except ImportError:
            st.warning("⚠️ 行情模块加载失败，请确认 `core/market_data.py` 存在。")
        except Exception as e:
            st.error(f"行情获取异常: {e}")

    st.markdown("---")
    st.subheader("宏观市场环境")
    try:
        from core.market_data import get_macro_data
        macro = get_macro_data()
        if macro:
            macro_rows = []
            for sym, data in macro.items():
                if "error" not in data:
                    macro_rows.append({
                        "指标": data.get("name", sym),
                        "最新值": data.get("price", "N/A"),
                        "24h变化": f"{data.get('change_24h', 0):+.2f}%",
                    })
                else:
                    macro_rows.append({"指标": data.get("name", sym), "最新值": "获取失败", "24h变化": "-"})
            if macro_rows:
                st.dataframe(pd.DataFrame(macro_rows), width="stretch")
    except Exception as e:
        st.info(f"宏观数据不可用: {e}")

# ========================================================================
# Tab 6: 系统管理
# ========================================================================
with tab6:
    st.header("🔧 系统状态管理")

    st.subheader("系统状态快照")
    status_df = query_db("SELECT * FROM system_status ORDER BY timestamp DESC LIMIT 10")
    if not status_df.empty:
        st.dataframe(status_df, width="stretch")
    else:
        st.info("暂无系统状态记录")

    st.markdown("---")
    st.subheader("数据库表统计")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    tables = ["battle_logs", "snapshots", "paper_trades", "live_trades", "scheduler_runs", "system_status"]
    cols = [col1, col2, col3, col4, col5, col6]
    for col, tbl in zip(cols, tables):
        cnt_df = query_db(f"SELECT COUNT(*) as cnt FROM {tbl}")
        cnt = int(cnt_df['cnt'].iloc[0]) if not cnt_df.empty else 0
        col.metric(tbl, cnt)

    st.markdown("---")
    st.subheader("快照管理")
    snapshots_df = query_db("SELECT * FROM snapshots")
    if not snapshots_df.empty:
        st.dataframe(snapshots_df[['session_id', 'stage', 'timestamp']], width="stretch")
        if st.button("🔴 清除所有快照"):
            if execute_db("DELETE FROM snapshots"):
                st.success("快照已清空！")
                st.rerun()
    else:
        st.success("✅ 系统运行健康，无挂起快照")

    st.markdown("---")
    st.subheader("环境变量检查")
    env_keys = ["GATEWAY_MODE", "IS_TESTNET", "FUTURES_LEVERAGE",
                "OPENAI_API_KEY", "OPENAI_MODEL_NAME",
                "BINANCE_API_KEY", "BINANCE_SECRET"]
    env_status = []
    for key in env_keys:
        val = os.getenv(key, "")
        masked = val[:6] + "****" + val[-4:] if len(val) > 12 else (val[:4] + "****" if val else "未设置")
        env_status.append({"变量名": key, "状态": "✅ 已设置" if val else "❌ 未设置", "值": masked if val else "-"})
    st.dataframe(pd.DataFrame(env_status), width="stretch")
