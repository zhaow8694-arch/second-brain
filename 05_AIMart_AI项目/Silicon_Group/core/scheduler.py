"""
⏰ 定时调度器 — 自动循环执行金融任务

职责:
  1. 按设定间隔自动触发金融重击任务
  2. 只扫描可交易标的（排除宏观指标）
  3. 记录每次执行结果
  4. 支持手动启动/停止/状态查询
"""
import os
import time
import json
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv

SCHEDULER_LOG_DIR = "scheduler_log"
DEFAULT_INTERVAL_HOURS = 4
TRADABLE_SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT",
    "DOGE/USDT", "XRP/USDT", "ADA/USDT",
    "LINK/USDT", "AVAX/USDT", "BCH/USDT",
]

_scheduler_thread = None
_stop_event = threading.Event()
_last_run = None
_next_run = None
_is_running = False
_current_cycle = 0


def _ensure_log_dir():
    if not os.path.exists(SCHEDULER_LOG_DIR):
        os.makedirs(SCHEDULER_LOG_DIR)


def _log_cycle(cycle: int, status: str, summary: str):
    _ensure_log_dir()
    log_file = os.path.join(SCHEDULER_LOG_DIR, "scheduler_history.json")
    entry = {
        "cycle": cycle,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "summary": summary,
    }
    history = []
    if os.path.exists(log_file):
        try:
            with open(log_file) as f:
                history = json.load(f)
        except Exception:
            pass
    history.append(entry)
    with open(log_file, "w") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def get_status() -> dict:
    """获取调度器当前状态"""
    global _last_run, _next_run, _is_running, _current_cycle
    return {
        "active": _scheduler_thread is not None and _scheduler_thread.is_alive(),
        "current_cycle": _current_cycle,
        "last_run": _last_run.isoformat() if _last_run else None,
        "next_run": _next_run.isoformat() if _next_run else None,
        "is_executing": _is_running,
        "interval_hours": DEFAULT_INTERVAL_HOURS,
        "tradable_symbols": len(TRADABLE_SYMBOLS),
    }


def _execute_cycle():
    """执行一轮完整的金融任务"""
    global _last_run, _next_run, _is_running, _current_cycle

    _is_running = True
    _current_cycle += 1
    cycle = _current_cycle
    now = datetime.now()
    print(f"\n{'='*60}")
    print(f"  ⏰ 定时调度器 — 第 {cycle} 轮执行")
    print(f"  时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  扫描标的: {len(TRADABLE_SYMBOLS)} 个可交易品种")
    print(f"{'='*60}")

    try:
        from command.operations import run_financial_mission
        result = run_financial_mission(f"scheduler_{now.strftime('%Y%m%d_%H%M%S')}", symbols=TRADABLE_SYMBOLS)
        summary = str(result)[:200] if result else "无返回"
        _log_cycle(cycle, "success", summary)
        print(f"\n✅ 第 {cycle} 轮执行完成")
        _save_scheduler_run_to_db(cycle, "success", summary)
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        safe_msg = error_msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        _log_cycle(cycle, "failed", safe_msg)
        print(f"\n❌ 第 {cycle} 轮执行失败: {safe_msg}")
        _save_scheduler_run_to_db(cycle, "failed", safe_msg)

    _last_run = now
    _next_run = now + timedelta(hours=DEFAULT_INTERVAL_HOURS)
    _is_running = False


def _save_scheduler_run_to_db(cycle: int, status: str, summary: str):
    """将调度器运行记录写入 SQLite 数据库"""
    try:
        from core.database import get_connection
        conn = get_connection()
        conn.execute(
            """INSERT INTO scheduler_runs
               (cycle, status, finished_at, symbols_count, symbols_analyzed, summary)
               VALUES (?, ?, datetime('now'), ?, ?, ?)""",
            (cycle, status, len(TRADABLE_SYMBOLS),
             json.dumps(TRADABLE_SYMBOLS, ensure_ascii=False), summary)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"   ⚠️ 写入调度器记录到数据库失败: {e}")


def _scheduler_loop():
    """调度器主循环"""
    global _next_run

    _next_run = datetime.now() + timedelta(hours=DEFAULT_INTERVAL_HOURS)
    print(f"\n⏰ 定时调度器已启动")
    print(f"   扫描间隔: 每 {DEFAULT_INTERVAL_HOURS} 小时")
    print(f"   可交易标的: {len(TRADABLE_SYMBOLS)} 个")
    print(f"   首次执行: {_next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   输入 'stop' 停止调度器\n")

    while not _stop_event.is_set():
        now = datetime.now()
        if _next_run and now >= _next_run:
            _execute_cycle()

        remaining = (_next_run - datetime.now()).total_seconds() if _next_run else 0
        if remaining > 0:
            _stop_event.wait(min(30, remaining))


def start():
    """启动定时调度器（后台线程）"""
    global _scheduler_thread, _stop_event

    if _scheduler_thread and _scheduler_thread.is_alive():
        print("⏰ 调度器已在运行中")
        return

    _stop_event.clear()
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
    _scheduler_thread.start()


def stop():
    """停止定时调度器"""
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        _stop_event.set()
        _scheduler_thread.join(timeout=10)
        print("⏰ 调度器已停止")
    else:
        print("⏰ 调度器未在运行")


def run_once():
    """立即执行一轮（不等待定时）"""
    _execute_cycle()
