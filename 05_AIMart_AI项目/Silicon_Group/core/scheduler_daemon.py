"""
🛡️ 调度器自愈守护进程

职责:
  1. 启动并保持调度器持续运行
  2. 每60秒检测一次调度器状态
  3. 如果调度器线程崩溃/退出，自动重启
  4. 记录所有异常和重启事件
  5. 支持优雅关闭
"""
import os
import sys
import time
import json
import signal
import threading
from datetime import datetime

DAEMON_LOG_DIR = "scheduler_log"
HEARTBEAT_FILE = os.path.join(DAEMON_LOG_DIR, "daemon_heartbeat.json")
CHECK_INTERVAL = 60


def _ensure_dirs():
    if not os.path.exists(DAEMON_LOG_DIR):
        os.makedirs(DAEMON_LOG_DIR)


def _log_event(event_type: str, message: str):
    _ensure_dirs()
    log_file = os.path.join(DAEMON_LOG_DIR, "daemon_events.json")
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "message": message,
    }
    history = []
    if os.path.exists(log_file):
        try:
            with open(log_file, encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            pass
    history.append(entry)
    if len(history) > 1000:
        history = history[-500:]
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def _write_heartbeat(status: str, detail: str = ""):
    _ensure_dirs()
    try:
        with open(HEARTBEAT_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "detail": detail,
            }, f, ensure_ascii=False)
    except Exception:
        pass


def run_daemon():
    """主守护循环"""
    print(f"\n{'='*60}")
    print(f"  🛡️ 调度器自愈守护进程启动")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  检测间隔: 每 {CHECK_INTERVAL} 秒")
    print(f"{'='*60}")

    _ensure_dirs()
    _log_event("DAEMON_START", "守护进程启动")
    _write_heartbeat("running", "守护进程启动")

    scheduler_module = None
    restart_count = 0
    max_restarts = 100

    def _start_scheduler():
        nonlocal scheduler_module
        try:
            if scheduler_module is None:
                import core.scheduler as sm
                scheduler_module = sm
            scheduler_module.start()
            status = scheduler_module.get_status()
            _log_event("SCHEDULER_STARTED", f"调度器启动成功, next_run={status.get('next_run')}")
            _write_heartbeat("scheduler_running", f"next_run={status.get('next_run')}")
            return True
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            _log_event("SCHEDULER_START_FAILED", error_msg)
            _write_heartbeat("error", error_msg)
            print(f"  ❌ 调度器启动失败: {error_msg}")
            return False

    _start_scheduler()

    def _signal_handler(signum, frame):
        print(f"\n  🛑 收到关闭信号 ({signum})，正在停止调度器...")
        _log_event("DAEMON_SHUTDOWN", f"收到信号 {signum}")
        _write_heartbeat("stopped", "守护进程关闭")
        if scheduler_module:
            try:
                scheduler_module.stop()
            except Exception:
                pass
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    while restart_count < max_restarts:
        try:
            time.sleep(CHECK_INTERVAL)

            if scheduler_module is None:
                print("  ⚠️ 调度器模块未加载，重新导入...")
                import core.scheduler as sm
                scheduler_module = sm
                _start_scheduler()
                continue

            status = scheduler_module.get_status()
            is_active = status.get("active", False)

            if not is_active:
                restart_count += 1
                print(f"  ⚠️ 检测到调度器停止 (重启 #{restart_count})")
                _log_event("SCHEDULER_DOWN", f"调度器停止，尝试第 {restart_count} 次重启")
                _write_heartbeat("restarting", f"尝试第 {restart_count} 次重启")

                success = _start_scheduler()
                if not success and restart_count >= 5:
                    print(f"  🔄 连续重启失败，等待 5 分钟后重试...")
                    _log_event("RESTART_BACKOFF", "连续重启失败，进入退避模式")
                    time.sleep(240)
            else:
                _write_heartbeat("healthy", f"cycle={status.get('current_cycle')}, next_run={status.get('next_run')}")

                if restart_count > 0:
                    print(f"  ✅ 调度器已恢复运行 (重启 {restart_count} 次后)")
                    _log_event("SCHEDULER_RECOVERED", f"调度器恢复运行，共重启 {restart_count} 次")
                    restart_count = 0

        except KeyboardInterrupt:
            print(f"\n  🛑 收到中断信号，正在停止调度器...")
            _log_event("DAEMON_SHUTDOWN", "KeyboardInterrupt")
            _write_heartbeat("stopped", "用户中断")
            if scheduler_module:
                try:
                    scheduler_module.stop()
                except Exception:
                    pass
            break
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            import traceback
            traceback.print_exc()
            _log_event("DAEMON_ERROR", error_msg)
            _write_heartbeat("error", error_msg)
            print(f"  ❌ 守护进程异常: {error_msg}")
            time.sleep(30)

    if restart_count >= max_restarts:
        _log_event("MAX_RESTARTS", f"达到最大重启次数 {max_restarts}，守护进程退出")
        _write_heartbeat("stopped", "超过最大重启次数")

    print(f"\n  🛡️ 守护进程退出")
    _log_event("DAEMON_EXIT", "守护进程正常退出")


if __name__ == "__main__":
    run_daemon()
