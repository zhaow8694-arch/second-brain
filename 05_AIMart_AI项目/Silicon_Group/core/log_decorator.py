"""
🧱 基石一：统一日志与元数据系统 (The Unified Log)

职责:
  1. 提供装饰器，自动记录函数的输入/输出/耗时/成本
  2. 统一日志格式，确保所有模块的日志结构一致
  3. 记录 Agent 决策的"内心 OS"（role, goal, task, result）
  4. 与 battle_log.py 无缝集成

用法:
  @log_mission(module="金融重击", target="XAU/USD")
  def my_function(session_id, ...):
      ...

  或手动调用:
  logger = MissionLogger(session_id, "金融重击", "XAU/USD")
  logger.start()
  # ... 执行任务 ...
  logger.end(result, cost=0.01)
"""
import time
import json
import functools
from datetime import datetime
from core.battle_log import write_log
from core.cost_watchdog import record_call

LOG_DIR = "battle_logs"


def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)


import os


class MissionLogger:
    """任务级日志记录器 — 记录一次完整作战的元数据"""

    def __init__(self, session_id: str, module: str, target: str, agent_role: str = ""):
        self.session_id = session_id
        self.module = module
        self.target = target
        self.agent_role = agent_role
        self.start_time = None
        self.end_time = None
        self.status = "pending"

    def start(self):
        self.start_time = time.time()
        self.status = "running"
        meta = {
            "session": self.session_id,
            "module": self.module,
            "target": self.target,
            "agent_role": self.agent_role,
            "action": "start",
            "timestamp": datetime.now().isoformat(),
        }
        write_log(self.session_id, f"{self.module}_START", self.target, json.dumps(meta, ensure_ascii=False))
        return self

    def end(self, result: str, cost: float = 0.0, status: str = "success"):
        self.end_time = time.time()
        elapsed = round(self.end_time - self.start_time, 2) if self.start_time else 0
        self.status = status

        meta = {
            "session": self.session_id,
            "module": self.module,
            "target": self.target,
            "agent_role": self.agent_role,
            "action": "end",
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": elapsed,
            "cost": cost,
            "status": status,
            "result_preview": str(result)[:200],
        }
        write_log(self.session_id, f"{self.module}_END", self.target, json.dumps(meta, ensure_ascii=False))
        record_call(self.module, 0, cost)
        return self

    def fail(self, error: str, cost: float = 0.0):
        return self.end(f"ERROR: {error}", cost, status="failed")


def log_mission(module: str = "", target: str = "", agent_role: str = ""):
    """装饰器：自动包装函数为一次标准化日志任务

    用法:
        @log_mission(module="金融重击", target="XAU/USD")
        def my_func(session_id, ...):
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            session_id = kwargs.get("session_id") or (args[0] if args else "unknown")
            logger = MissionLogger(
                session_id=session_id,
                module=module or func.__name__,
                target=target or "unknown",
                agent_role=agent_role,
            )
            logger.start()
            try:
                result = func(*args, **kwargs)
                logger.end(result)
                return result
            except Exception as e:
                logger.fail(str(e))
                raise
        return wrapper
    return decorator


def get_recent_logs(session_id: str = None, limit: int = 20) -> list:
    """获取最近的日志条目（供教导团使用）"""
    log_dir = "battle_logs"
    if not os.path.exists(log_dir):
        return []

    log_files = []
    if session_id:
        target = f"{log_dir}/{session_id}.md"
        if os.path.exists(target):
            log_files.append(target)
    else:
        log_files = sorted(
            [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith(".md")],
            reverse=True
        )[:5]

    entries = []
    for filepath in log_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        sections = content.split("---")
        for section in sections:
            section = section.strip()
            if not section:
                continue
            try:
                json_start = section.find("{")
                if json_start >= 0:
                    json_str = section[json_start:]
                    data = json.loads(json_str)
                    entries.append(data)
            except (json.JSONDecodeError, ValueError):
                pass

    return entries[:limit]
