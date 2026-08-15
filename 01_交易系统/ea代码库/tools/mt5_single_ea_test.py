import argparse
import csv
import html
import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path


TERMINAL_DIR = Path(r"D:\MT5测试\MetaTrader 5")
EXPERTS_DIR = TERMINAL_DIR / "MQL5" / "Experts"
TESTER_DIR = TERMINAL_DIR / "Tester"
TERMINAL_EXE = TERMINAL_DIR / "terminal64.exe"


METRIC_KEYS = [
    "总净盈利:",
    "毛利:",
    "毛损:",
    "盈利因子:",
    "预期收益:",
    "最大净值亏损:",
    "相对净值亏损:",
    "交易总计:",
    "盈利交易 (% 全部):",
    "亏损交易 (% 全部):",
    "最大 获利交易:",
    "最大 亏损交易:",
    "平均 获利交易:",
    "平均 亏损交易:",
    "平均持仓时间:",
]


def sanitize_name(value: str, limit: int = 90) -> str:
    value = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", value, flags=re.UNICODE)
    value = re.sub(r"_+", "_", value).strip("._ ")
    return (value or "ea")[:limit]


def clean_lines(report_path: Path) -> list[str]:
    text = report_path.read_text(encoding="utf-8", errors="ignore")
    lines = []
    for line in text.splitlines():
        line = re.sub(r"<[^>]+>", " ", line)
        line = html.unescape(line)
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return lines


def metric_value(lines: list[str], key: str) -> str:
    for index, line in enumerate(lines[:-1]):
        if line == key:
            return lines[index + 1]
    return ""


def parse_number(value: str) -> float:
    value = (value or "").replace(" ", "").replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(match.group(0)) if match else 0.0


def parse_report(report_path: Path) -> dict:
    if not report_path.exists():
        return {}
    lines = clean_lines(report_path)
    metrics = {key.rstrip(":"): metric_value(lines, key) for key in METRIC_KEYS}
    metrics["net_profit_num"] = parse_number(metrics.get("总净盈利", ""))
    metrics["profit_factor_num"] = parse_number(metrics.get("盈利因子", ""))
    metrics["trades_num"] = int(parse_number(metrics.get("交易总计", "")))
    metrics["max_equity_dd_num"] = parse_number(metrics.get("最大净值亏损", ""))
    metrics["score"] = round(
        metrics["net_profit_num"]
        + metrics["profit_factor_num"] * 100.0
        - metrics["max_equity_dd_num"] * 0.25
        + min(metrics["trades_num"], 100),
        2,
    )
    return metrics


def write_ini(path: Path, expert_rel: str, report_rel_no_ext: str, args: argparse.Namespace) -> None:
    lines = [
        "[Tester]",
        f"Expert={expert_rel}",
        f"Symbol={args.symbol}",
        f"Period={args.period}",
        "Optimization=0",
        f"Model={args.model}",
        f"FromDate={args.from_date}",
        f"ToDate={args.to_date}",
        "ForwardMode=0",
        f"Deposit={args.deposit}",
        "Currency=USD",
        "ProfitInPips=0",
        f"Leverage={args.leverage}",
        "ExecutionMode=100",
        "OptimizationCriterion=7",
        "Visual=0",
        f"Report={report_rel_no_ext}",
        "ReplaceReport=1",
        "ShutdownTerminal=1",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def append_record(csv_path: Path, row: dict) -> None:
    fields = [
        "run_time", "ea_name", "expert", "symbol", "period", "from_date", "to_date",
        "status", "seconds", "report", "总净盈利", "毛利", "毛损", "盈利因子",
        "预期收益", "最大净值亏损", "相对净值亏损", "交易总计",
        "盈利交易 (% 全部)", "亏损交易 (% 全部)", "最大 获利交易",
        "最大 亏损交易", "平均 获利交易", "平均 亏损交易", "平均持仓时间",
        "score", "notes",
    ]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    exists = csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exactly one MT5 EA test and record its report.")
    parser.add_argument("--expert", required=True, help="Expert path relative to MQL5\\Experts, for example V3.ex5")
    parser.add_argument("--run-id", default=datetime.now().strftime("%Y%m%d_single"))
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--period", default="H1")
    parser.add_argument("--from-date", default="2026.01.01")
    parser.add_argument("--to-date", default="2026.03.31")
    parser.add_argument("--model", type=int, default=1)
    parser.add_argument("--deposit", type=int, default=20000)
    parser.add_argument("--leverage", type=int, default=200)
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()

    expert_rel = args.expert.replace("/", "\\")
    expert_path = EXPERTS_DIR / expert_rel
    if not expert_path.exists():
        raise SystemExit(f"expert not found: {expert_path}")
    if not TERMINAL_EXE.exists():
        raise SystemExit(f"terminal not found: {TERMINAL_EXE}")

    slug = sanitize_name(Path(expert_rel).with_suffix("").as_posix())
    report_dir = TERMINAL_DIR / "SingleEAReports" / args.run_id / slug
    report_dir.mkdir(parents=True, exist_ok=True)
    report_rel = f"SingleEAReports\\{args.run_id}\\{slug}\\report"
    ini_path = TESTER_DIR / f"single_{sanitize_name(args.run_id)}_{slug}.ini"
    write_ini(ini_path, expert_rel, report_rel, args)
    (report_dir / "test_config.ini").write_text(ini_path.read_text(encoding="utf-8"), encoding="utf-8")

    started = time.time()
    status = "unknown"
    notes = ""
    proc = subprocess.Popen(
        [str(TERMINAL_EXE), "/portable", f"/config:{ini_path}"],
        cwd=str(TERMINAL_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        proc.wait(timeout=args.timeout)
        status = "finished" if proc.returncode == 0 else f"exit_{proc.returncode}"
    except subprocess.TimeoutExpired:
        status = "timeout"
        notes = f"timeout after {args.timeout}s"
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()

    seconds = round(time.time() - started, 2)
    report_path = report_dir / "report.htm"
    metrics = parse_report(report_path)
    if not report_path.exists() and status == "finished":
        status = "no_report"
        notes = "terminal finished but report.htm not found"
    if metrics.get("trades_num", 0) == 0 and report_path.exists():
        notes = (notes + "; " if notes else "") + "no trades"

    row = {
        "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ea_name": expert_path.stem,
        "expert": expert_rel,
        "symbol": args.symbol,
        "period": args.period,
        "from_date": args.from_date,
        "to_date": args.to_date,
        "status": status,
        "seconds": seconds,
        "report": str(report_path) if report_path.exists() else "",
        "notes": notes,
    }
    row.update(metrics)
    (report_dir / "status.json").write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    append_record(TERMINAL_DIR / "SingleEAReports" / args.run_id / "EA_Test_Log.csv", row)
    print(json.dumps(row, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
