import time
import json
import os
from datetime import datetime, timedelta

LOG_FILE = "cost_log.json"

DAILY_BUDGET = float(os.getenv("DAILY_API_BUDGET", "5.0"))

usage_log = []


def load_log():
    global usage_log
    try:
        with open(LOG_FILE, "r") as f:
            usage_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        usage_log = []


def save_log():
    with open(LOG_FILE, "w") as f:
        json.dump(usage_log, f, indent=2)


def record_call(model: str, tokens: int, cost: float):
    load_log()
    usage_log.append({
        "time": datetime.now().isoformat(),
        "model": model,
        "tokens": tokens,
        "cost": round(cost, 6),
    })
    save_log()


def today_cost() -> float:
    load_log()
    today = datetime.now().date()
    total = 0.0
    for entry in usage_log:
        entry_date = datetime.fromisoformat(entry["time"]).date()
        if entry_date == today:
            total += entry["cost"]
    return total


def is_meltdown() -> bool:
    total = today_cost()
    if total >= DAILY_BUDGET:
        return True
    return False


def get_status() -> dict:
    return {
        "today_cost": round(today_cost(), 4),
        "daily_budget": DAILY_BUDGET,
        "meltdown": is_meltdown(),
        "remaining": round(DAILY_BUDGET - today_cost(), 4),
    }
