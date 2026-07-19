# -*- coding: utf-8 -*-
"""
Silicon Group Auto-Start — 7x24 Automated Trading Scheduler
"""
import sys
import os
import io
import signal
import time

# 强制 UTF-8 输出，解决 Windows GBK 终端乱码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from core.database import init_db
from core.cost_watchdog import get_status, is_meltdown
from core.guard_dog import is_meltdown_active
from core.scheduler import start, stop, get_status as sched_status, run_once

init_db()

print("=" * 60)
print("  [SG] Silicon Group Auto-Trading System")
print("=" * 60)

budget = get_status()
print(f"\n[Budget] Today: ${budget['today_cost']:.4f} / ${budget['daily_budget']} | Remaining: ${budget['remaining']:.4f}")

if is_meltdown():
    print("[ERROR] Daily API budget exhausted. Try again tomorrow.")
    sys.exit(1)

if is_meltdown_active():
    print("[ERROR] Guard Dog meltdown active. System locked.")
    sys.exit(1)

print("[OK] Safety checks passed. Starting scheduler...\n")

def handle_exit(sig, frame):
    print("\n[STOP] Signal received, shutting down safely...")
    stop()
    print("[OK] Scheduler stopped. Goodbye!")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# 立即执行第一轮
print("[RUN] Executing first cycle immediately...")
run_once()

# 启动定时调度器
start()
print("\n[SCHEDULER] Active — auto-triggers every 4 hours.")
print("            Press Ctrl+C to stop safely.\n")

# 保持主进程存活，每分钟打印一次状态
while True:
    try:
        s = sched_status()
        next_r = s['next_run'] or 'calculating...'
        print(f"[{time.strftime('%H:%M:%S')}] Cycle #{s['current_cycle']} done | Next run: {next_r}", flush=True)
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Status check error: {e}", flush=True)
    time.sleep(60)
