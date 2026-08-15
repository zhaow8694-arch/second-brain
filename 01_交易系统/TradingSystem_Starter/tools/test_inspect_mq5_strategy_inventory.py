#!/usr/bin/env python3
"""Self-test for the read-only MQ5 strategy inventory scanner."""

from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT_DIR / "tools" / "inspect_mq5_strategy_inventory.py"


SAMPLE_MQ5 = """
input bool InpEnableTrading = false;
input int InpMaxSpreadPoints = 300;

class RiskManager {};
class SignalEngine {};
CTrade trade;

int OnInit()
{
    return INIT_SUCCEEDED;
}

void OnTick()
{
    OrderSend(request, result);
    trade.PositionOpen(_Symbol, ORDER_TYPE_BUY, 0.01, Ask, 0, 0);
    trade.Buy(0.01);
    trade.Sell(0.01);
}

void OnDeinit(const int reason)
{
}
"""


def fail(message: str) -> int:
    print("MQ5 strategy inventory self-test failed")
    print(message)
    return 1


def load_tool_module():
    spec = importlib.util.spec_from_file_location("inspect_mq5_strategy_inventory", TOOL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec: {TOOL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_main(tool, args: list[str]) -> tuple[int, str]:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = tool.main(args)
    return exit_code, buffer.getvalue()


def test_missing_root_default_passes(tool) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_root = Path(tmpdir) / "missing"
        exit_code, output = run_main(tool, ["--mq5-root", str(missing_root)])
    if exit_code != 0:
        return "missing root default mode should PASS"
    if "PASS" not in output or "total=0" not in output:
        return "missing root default output should contain PASS and empty summary"
    return ""


def test_missing_root_fail_flag_fails(tool) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_root = Path(tmpdir) / "missing"
        exit_code, output = run_main(
            tool,
            ["--mq5-root", str(missing_root), "--fail-on-missing-root"],
        )
    if exit_code == 0:
        return "--fail-on-missing-root should fail for a missing root"
    if "FAIL" not in output:
        return "missing root failure output should contain FAIL"
    return ""


def test_detects_required_markers(tool) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        sample_path = root / "Strategy.mq5"
        sample_path.write_text(SAMPLE_MQ5, encoding="utf-8")
        inventory = tool.build_inventory(root)

    files = inventory["files"]
    if len(files) != 1:
        return f"expected one source file, got {len(files)}"
    file_info = files[0]
    checks = {
        "input parameters": file_info["inputParameterLines"] == 2,
        "InpEnableTrading": file_info["hasInpEnableTrading"],
        "RiskManager": file_info["hasRiskManager"],
        "SignalEngine": file_info["hasSignalEngine"],
        "CTrade": file_info["tradingKeywords"]["CTrade"],
        "OrderSend": file_info["tradingKeywords"]["OrderSend"],
        "PositionOpen": file_info["tradingKeywords"]["PositionOpen"],
        "Buy": file_info["tradingKeywords"]["Buy"],
        "Sell": file_info["tradingKeywords"]["Sell"],
        "OnInit": file_info["lifecycle"]["OnInit"],
        "OnTick": file_info["lifecycle"]["OnTick"],
        "OnDeinit": file_info["lifecycle"]["OnDeinit"],
    }
    missing = [name for name, passed in checks.items() if not passed]
    if missing:
        return f"failed marker checks: {missing}"
    return ""


def test_json_output_is_parseable(tool) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "Strategy.mqh").write_text(SAMPLE_MQ5, encoding="utf-8")
        exit_code, output = run_main(tool, ["--mq5-root", str(root), "--json"])

    if exit_code != 0:
        return "json mode should PASS"
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError as exc:
        return f"json mode did not emit parseable JSON: {exc}"
    if parsed["status"] != "PASS" or parsed["fileCounts"]["total"] != 1:
        return "json output missing expected status or file count"
    return ""


def test_no_output_files_created(tool) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        sample_path = root / "Strategy.mq5"
        sample_path.write_text(SAMPLE_MQ5, encoding="utf-8")
        before = sorted(path.name for path in root.iterdir())
        exit_code, _output = run_main(tool, ["--mq5-root", str(root)])
        after = sorted(path.name for path in root.iterdir())

    if exit_code != 0:
        return "text mode should PASS"
    if before != after:
        return f"tool created or removed files: before={before}, after={after}"
    return ""


def main() -> int:
    if not TOOL_PATH.exists():
        return fail(f"tool script not found: {TOOL_PATH}")

    tool = load_tool_module()
    tests = [
        test_missing_root_default_passes,
        test_missing_root_fail_flag_fails,
        test_detects_required_markers,
        test_json_output_is_parseable,
        test_no_output_files_created,
    ]

    for test in tests:
        error = test(tool)
        if error:
            return fail(error)

    print("MQ5 strategy inventory self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
