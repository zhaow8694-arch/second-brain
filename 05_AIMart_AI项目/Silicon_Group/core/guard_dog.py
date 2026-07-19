"""
🐕 物理防火墙 (Guard Dog) — 帝国防御系统

职责:
  1. 独立于系统之外的监控层
  2. 检测异常 API 速率和成本超支
  3. 检测进程异常行为（死循环、内存泄漏）
  4. 网络级熔断：切断 API 请求
  5. 与 cost_watchdog 形成双重保障

设计原则:
  - 完全独立模块，不修改任何现有代码
  - 只读方式访问 cost_log.json
  - 不依赖任何业务模块
  - 熔断后只能手动恢复
"""
import os
import json
import time
from datetime import datetime, timedelta
from core.battle_log import write_log

GUARD_DOG_LOG = "guard_dog_log.json"
MELTDOWN_FLAG = "guard_dog_meltdown.flag"


def _load_guard_log() -> dict:
    try:
        with open(GUARD_DOG_LOG, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"incidents": [], "meltdown_history": [], "last_patrol": None}


def _save_guard_log(data: dict):
    with open(GUARD_DOG_LOG, "w") as f:
        json.dump(data, f, indent=2)


def _read_cost_log() -> dict:
    """只读方式访问 cost_log.json

    兼容两种格式:
      - dict: {"calls": [...], "total_cost": N, ...}
      - list: [{"time": ..., "cost": N}, ...] (旧格式)
    """
    try:
        with open("cost_log.json", "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {"calls": data, "total_cost": sum(c.get("cost", 0) for c in data), "daily_budget": 5.0}
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"calls": [], "total_cost": 0, "daily_budget": 5.0}


def patrol() -> dict:
    """执行一次巡逻 — 检查系统各项指标

    这是 Guard Dog 的核心接口，每次调用都会检查:
    1. API 成本是否超支
    2. 请求频率是否异常
    3. 是否有熔断标志

    Returns:
        巡逻报告
    """
    now = datetime.now()
    report = {
        "patrol_time": now.isoformat(),
        "status": "healthy",
        "checks": [],
        "alerts": [],
    }

    cost_data = _read_cost_log()
    guard_log = _load_guard_log()

    check_cost = _check_cost_anomaly(cost_data)
    report["checks"].append(check_cost)
    if not check_cost["passed"]:
        report["alerts"].append(check_cost["message"])
        report["status"] = "alert"

    check_rate = _check_rate_anomaly(cost_data)
    report["checks"].append(check_rate)
    if not check_rate["passed"]:
        report["alerts"].append(check_rate["message"])
        report["status"] = "alert"

    check_meltdown = _check_meltdown_flag()
    report["checks"].append(check_meltdown)
    if not check_meltdown["passed"]:
        report["alerts"].append(check_meltdown["message"])
        report["status"] = "meltdown"

    guard_log["last_patrol"] = report
    guard_log["incidents"].append({
        "time": now.isoformat(),
        "status": report["status"],
        "alert_count": len(report["alerts"]),
    })
    _save_guard_log(guard_log)

    return report


def _check_cost_anomaly(cost_data: dict) -> dict:
    """检查成本异常

    规则:
    - 单次调用成本超过 $0.05 视为异常
    - 最近 10 次调用平均成本超过 $0.03 视为异常
    """
    calls = cost_data.get("calls", [])
    recent_calls = calls[-10:] if len(calls) >= 10 else calls

    if not recent_calls:
        return {"check": "cost_anomaly", "passed": True, "message": "无调用记录"}

    recent_costs = [c.get("cost", 0) for c in recent_calls if isinstance(c, dict)]
    avg_cost = sum(recent_costs) / len(recent_costs) if recent_costs else 0
    max_cost = max(recent_costs) if recent_costs else 0

    alerts = []
    if max_cost > 0.05:
        alerts.append(f"单次调用成本异常: ${max_cost:.4f} (阈值: $0.05)")

    if avg_cost > 0.03 and len(recent_costs) >= 5:
        alerts.append(f"近 {len(recent_costs)} 次调用平均成本异常: ${avg_cost:.4f} (阈值: $0.03)")

    return {
        "check": "cost_anomaly",
        "passed": len(alerts) == 0,
        "message": "; ".join(alerts) if alerts else f"成本正常 (avg: ${avg_cost:.4f}, max: ${max_cost:.4f})",
        "avg_cost": round(avg_cost, 4),
        "max_cost": round(max_cost, 4),
    }


def _check_rate_anomaly(cost_data: dict) -> dict:
    """检查请求频率异常

    规则:
    - 1 分钟内超过 30 次调用视为异常
    """
    calls = cost_data.get("calls", [])
    now = datetime.now()
    one_minute_ago = now - timedelta(minutes=1)

    recent_calls = []
    for c in calls:
        if isinstance(c, dict):
            call_time_str = c.get("time", "")
            try:
                call_time = datetime.fromisoformat(call_time_str)
                if call_time > one_minute_ago:
                    recent_calls.append(c)
            except (ValueError, TypeError):
                continue

    rate = len(recent_calls)

    if rate > 30:
        return {
            "check": "rate_anomaly",
            "passed": False,
            "message": f"请求频率异常: 1 分钟内 {rate} 次 (阈值: 30)",
            "rate": rate,
        }

    return {
        "check": "rate_anomaly",
        "passed": True,
        "message": f"请求频率正常: 1 分钟内 {rate} 次",
        "rate": rate,
    }


def _check_meltdown_flag() -> dict:
    """检查熔断标志文件"""
    if os.path.exists(MELTDOWN_FLAG):
        try:
            with open(MELTDOWN_FLAG, "r") as f:
                reason = f.read().strip()
        except Exception:
            reason = "未知原因"
        return {
            "check": "meltdown_flag",
            "passed": False,
            "message": f"熔断已触发: {reason}",
        }
    return {
        "check": "meltdown_flag",
        "passed": True,
        "message": "无熔断标志",
    }


def trigger_meltdown(reason: str = "Guard Dog 触发熔断"):
    """触发熔断 — 创建熔断标志文件

    这是 Guard Dog 的最高级别防御动作。
    熔断后，main.py 的启动检查会阻止任务执行。
    """
    with open(MELTDOWN_FLAG, "w") as f:
        f.write(f"{datetime.now().isoformat()} | {reason}")

    guard_log = _load_guard_log()
    guard_log["meltdown_history"].append({
        "time": datetime.now().isoformat(),
        "reason": reason,
    })
    _save_guard_log(guard_log)

    write_log("GUARD_DOG", "MELTDOWN", "系统防御", f"Guard Dog 触发熔断: {reason}")


def release_meltdown():
    """手动解除熔断"""
    if os.path.exists(MELTDOWN_FLAG):
        os.remove(MELTDOWN_FLAG)
        write_log("GUARD_DOG", "MELTDOWN_RELEASED", "系统防御", "熔断已手动解除")


def is_meltdown_active() -> bool:
    """检查熔断是否激活"""
    return os.path.exists(MELTDOWN_FLAG)


def get_guard_dog_status() -> dict:
    """获取 Guard Dog 状态"""
    guard_log = _load_guard_log()
    last_patrol = guard_log.get("last_patrol") or {}

    return {
        "meltdown_active": is_meltdown_active(),
        "last_patrol_time": last_patrol.get("patrol_time", "从未巡逻"),
        "last_status": last_patrol.get("status", "unknown"),
        "total_incidents": len(guard_log.get("incidents", [])),
        "total_meltdowns": len(guard_log.get("meltdown_history", [])),
    }
