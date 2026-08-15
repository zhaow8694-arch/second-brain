#!/usr/bin/env python3
"""Self-test for the fast no-trade preflight runner."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
PREFLIGHT_PATH = ROOT_DIR / "tools" / "run_fast_no_trade_preflight.py"


def fail(message: str) -> int:
    print("Fast no-trade preflight self-test failed")
    print(message)
    return 1


def load_preflight_module():
    spec = importlib.util.spec_from_file_location("run_fast_no_trade_preflight", PREFLIGHT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec: {PREFLIGHT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def command_text(command: tuple[str, ...]) -> str:
    return " ".join(command).replace("\\", "/")


def run_main(module, args, responses):
    calls = []

    def fake_runner(command):
        calls.append(tuple(command))
        text = command_text(tuple(command))
        for pattern, response in responses:
            if pattern in text:
                if isinstance(response, BaseException):
                    raise response
                return response
        return subprocess.CompletedProcess(list(command), 0, stdout="", stderr="")

    output = io.StringIO()
    with redirect_stdout(output):
        result = module.main(args, runner=fake_runner)
    return result, calls, output.getvalue()


def completed(command_name, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(
        [command_name],
        returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_default_runs_fast_profile(module) -> str:
    result, calls, output = run_main(
        module,
        [],
        [("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1))],
    )
    if result != 0:
        return f"default preflight failed\n{output}"
    lines = "\n".join(command_text(command) for command in calls)
    if "run_release_validation_bundle.py --profile fast-no-trade-dev" not in lines:
        return f"default mode did not call fast-no-trade-dev profile\n{lines}"
    if "Fast no-trade preflight" not in output:
        return "summary did not include Fast no-trade preflight"
    if "Inventory only; no MT5 run; no trading authorization." not in output:
        return "summary did not include no-trade notice"
    return ""


def test_rg_no_match_exit_one_passes(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile"],
        [("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1))],
    )
    if result != 0:
        return f"rg no-match exit 1 was not treated as PASS\n{output}"
    if "no trading keyword matches" not in output:
        return f"rg no-match detail missing\n{output}"
    return ""


def test_skip_profile_omits_release_bundle(module) -> str:
    result, calls, output = run_main(
        module,
        ["--skip-profile"],
        [("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1))],
    )
    if result != 0:
        return f"skip-profile preflight failed\n{output}"
    lines = "\n".join(command_text(command) for command in calls)
    if "run_release_validation_bundle.py" in lines:
        return f"skip-profile still called release validation bundle\n{lines}"
    return ""


def test_allowed_change_guard_allows_explicit_files(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow",
            "docs/CURRENT_TASK.md",
            "--allow",
            "tools/run_fast_no_trade_preflight.py",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git diff --name-only", completed("git", 0, stdout="docs/CURRENT_TASK.md\n")),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=(
                        " M docs/CURRENT_TASK.md\n"
                        "?? .vscode/\n"
                        "?? tools/run_fast_no_trade_preflight.py\n"
                    ),
                ),
            ),
        ],
    )
    if result != 0:
        return f"allowed explicit files did not pass\n{output}"
    if "allowed_change_guard=true" not in output:
        return f"allowed-change summary missing guard flag\n{output}"
    if "allowed_change_check=PASS" not in output:
        return f"allowed-change summary missing PASS\n{output}"
    if "unexpected_changes_count=0" not in output:
        return f"allowed-change summary missing zero count\n{output}"
    return ""


def test_allowed_change_guard_allows_prefix(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow-prefix",
            "docs/",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git diff --name-only", completed("git", 0, stdout="docs/PROJECT_STATE.md\n")),
            ("git status --short", completed("git", 0, stdout=" M docs/PROJECT_STATE.md\n")),
        ],
    )
    if result != 0:
        return f"allowed prefix did not pass\n{output}"
    if "allowed_change_check=PASS" not in output:
        return f"allowed prefix summary missing PASS\n{output}"
    return ""


def test_allow_preset_doc_state_expands_allowed_files(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow-preset",
            "doc-state",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            (
                "git diff --name-only",
                completed(
                    "git",
                    0,
                    stdout=(
                        "docs/CURRENT_TASK.md\n"
                        "docs/HANDOFF_PROMPT.md\n"
                        "docs/PROJECT_STATE.md\n"
                        "tools/validate_project_state_docs.py\n"
                        "tools/test_validate_project_state_docs.py\n"
                    ),
                ),
            ),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=(
                        " M docs/CURRENT_TASK.md\n"
                        " M docs/HANDOFF_PROMPT.md\n"
                        " M docs/PROJECT_STATE.md\n"
                        " M tools/validate_project_state_docs.py\n"
                        " M tools/test_validate_project_state_docs.py\n"
                    ),
                ),
            ),
        ],
    )
    if result != 0:
        return f"doc-state preset did not pass\n{output}"
    if "allowed_presets=doc-state" not in output:
        return f"doc-state preset summary missing\n{output}"
    return ""


def test_allow_preset_tooling_preflight_expands_allowed_files(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow-preset",
            "tooling-preflight",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            (
                "git diff --name-only",
                completed(
                    "git",
                    0,
                    stdout=(
                        "docs/CURRENT_TASK.md\n"
                        "tools/run_fast_no_trade_preflight.py\n"
                        "tools/test_run_fast_no_trade_preflight.py\n"
                    ),
                ),
            ),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=(
                        " M docs/CURRENT_TASK.md\n"
                        " M tools/run_fast_no_trade_preflight.py\n"
                        " M tools/test_run_fast_no_trade_preflight.py\n"
                    ),
                ),
            ),
        ],
    )
    if result != 0:
        return f"tooling-preflight preset did not pass\n{output}"
    if "allowed_presets=tooling-preflight" not in output:
        return f"tooling-preflight preset summary missing\n{output}"
    return ""


def test_allow_preset_mq5_observability_expands_allowed_files(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow-preset",
            "mq5-observability",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            (
                "git diff --name-only",
                completed(
                    "git",
                    0,
                    stdout=(
                        "mq5/core/EaController.mqh\n"
                        "mq5/logger/Logger.mqh\n"
                        "tools/validate_mq5_no_trade_observability.py\n"
                        "tools/test_validate_mq5_no_trade_observability.py\n"
                    ),
                ),
            ),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=(
                        " M mq5/core/EaController.mqh\n"
                        " M mq5/logger/Logger.mqh\n"
                        " M tools/validate_mq5_no_trade_observability.py\n"
                        " M tools/test_validate_mq5_no_trade_observability.py\n"
                    ),
                ),
            ),
        ],
    )
    if result != 0:
        return f"mq5-observability preset did not pass\n{output}"
    if "allowed_presets=mq5-observability" not in output:
        return f"mq5-observability preset summary missing\n{output}"
    return ""


def test_allow_preset_stacks_with_allow(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow-preset",
            "doc-state",
            "--allow",
            "tools/run_fast_no_trade_preflight.py",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            (
                "git diff --name-only",
                completed(
                    "git",
                    0,
                    stdout="docs/CURRENT_TASK.md\ntools/run_fast_no_trade_preflight.py\n",
                ),
            ),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=" M docs/CURRENT_TASK.md\n M tools/run_fast_no_trade_preflight.py\n",
                ),
            ),
        ],
    )
    if result != 0:
        return f"preset plus --allow did not pass\n{output}"
    if "allowed_change_check=PASS" not in output:
        return f"preset plus --allow missing PASS summary\n{output}"
    return ""


def test_allow_preset_stacks_with_allow_prefix(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow-preset",
            "doc-state",
            "--allow-prefix",
            "scratch/",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git diff --name-only", completed("git", 0, stdout="scratch/note.txt\n")),
            ("git status --short", completed("git", 0, stdout="?? scratch/note.txt\n")),
        ],
    )
    if result != 0:
        return f"preset plus --allow-prefix did not pass\n{output}"
    if "allowed_change_check=PASS" not in output:
        return f"preset plus --allow-prefix missing PASS summary\n{output}"
    return ""


def test_unknown_allow_preset_fails(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow-preset",
            "unknown",
        ],
        [],
    )
    if result == 0:
        return "unknown allow preset did not fail"
    if "unknown allow preset: unknown" not in output:
        return f"unknown preset failure was not clear\n{output}"
    return ""


def test_allow_preset_requires_check_allowed_changes(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile", "--allow-preset", "doc-state"],
        [],
    )
    if result == 0:
        return "allow preset without allowed-change guard did not fail"
    if "--allow-preset requires --check-allowed-changes" not in output:
        return f"missing fail-fast message for preset without guard\n{output}"
    return ""


def test_allowed_change_guard_rejects_unallowed_tracked_diff(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow",
            "docs/CURRENT_TASK.md",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git diff --name-only", completed("git", 0, stdout="mq5/TradingSystem.mq5\n")),
            ("git status --short", completed("git", 0, stdout=" M mq5/TradingSystem.mq5\n")),
        ],
    )
    if result == 0:
        return "unallowed tracked diff did not fail"
    if "allowed_change_check=FAIL" not in output:
        return f"unallowed tracked diff missing FAIL summary\n{output}"
    if "unexpected_changes_count=1" not in output:
        return f"unallowed tracked diff missing count\n{output}"
    return ""


def test_allowed_change_guard_rejects_unallowed_untracked_file(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile", "--check-allowed-changes"],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git diff --name-only", completed("git", 0, stdout="")),
            ("git status --short", completed("git", 0, stdout="?? scratch.txt\n")),
        ],
    )
    if result == 0:
        return "unallowed untracked file did not fail"
    if "scratch.txt" not in output:
        return f"unallowed untracked path missing from output\n{output}"
    return ""


def test_allowed_change_guard_ignores_known_untracked_items(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile", "--check-allowed-changes"],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git diff --name-only", completed("git", 0, stdout="")),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=(
                        "?? .vscode/\n"
                        "?? logs/localhost-3000.out.log\n"
                        "?? package-lock.json\n"
                        "?? tools/__pycache__/\n"
                        "?? 新建 文本文档.txt\n"
                    ),
                ),
            ),
        ],
    )
    if result != 0:
        return f"known untracked items caused failure\n{output}"
    if "unexpected_changes_count=0" not in output:
        return f"known untracked summary missing zero count\n{output}"
    return ""


def test_doc_only_with_allowed_change_guard_passes(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--doc-only",
            "--skip-profile",
            "--check-allowed-changes",
            "--allow-prefix",
            "docs/",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git diff --name-only", completed("git", 0, stdout="docs/HANDOFF_PROMPT.md\n")),
            ("git status --short", completed("git", 0, stdout=" M docs/HANDOFF_PROMPT.md\n")),
        ],
    )
    if result != 0:
        return f"doc-only allowed-change guard failed\n{output}"
    if "doc-only MQ5 diff guard" not in output:
        return f"doc-only guard did not run\n{output}"
    return ""


def test_strict_mq5_with_allowed_change_guard_passes(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--strict-mq5",
            "--skip-profile",
            "--check-allowed-changes",
            "--allow",
            "tools/validate_project_state_docs.py",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            (
                "git diff --name-only",
                completed("git", 0, stdout="tools/validate_project_state_docs.py\n"),
            ),
            (
                "git status --short",
                completed("git", 0, stdout=" M tools/validate_project_state_docs.py\n"),
            ),
        ],
    )
    if result != 0:
        return f"strict-mq5 allowed-change guard failed\n{output}"
    if "strict MQ5 forbidden file diff guard" not in output:
        return f"strict-mq5 guard did not run\n{output}"
    return ""


def test_rg_match_exit_zero_fails(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile"],
        [
            (
                "rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5",
                completed("rg", 0, stdout="mq5/file.mqh:Buy"),
            )
        ],
    )
    if result == 0:
        return "rg match exit 0 did not fail"
    if "trading keyword matches detected" not in output:
        return f"rg match failure detail missing\n{output}"
    return ""


def test_doc_only_checks_mq5_diff(module) -> str:
    result, calls, output = run_main(
        module,
        ["--doc-only"],
        [("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1))],
    )
    if result != 0:
        return f"doc-only preflight failed\n{output}"
    lines = "\n".join(command_text(command) for command in calls)
    if "git diff -- mq5" not in lines:
        return f"doc-only mode did not check git diff -- mq5\n{lines}"
    return ""


def test_strict_mq5_checks_forbidden_files(module) -> str:
    result, calls, output = run_main(
        module,
        ["--strict-mq5"],
        [("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1))],
    )
    if result != 0:
        return f"strict-mq5 preflight failed\n{output}"
    lines = "\n".join(command_text(command) for command in calls)
    required = (
        "mq5/TradingSystem.mq5",
        "mq5/config/InputConfig.mqh",
        "mq5/signals/SignalEngine.mqh",
        "mq5/risk/RiskManager.mqh",
        "mq5/execution/ExecutionManager.mqh",
    )
    for path in required:
        if path not in lines:
            return f"strict-mq5 mode missing forbidden file: {path}\n{lines}"
    return ""


def test_backtest_manifest_diff_output_fails(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile"],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            (
                "git diff -- backtest/sets backtest/reports/manifests",
                completed("git", 0, stdout="diff --git a/backtest/sets/example.set"),
            ),
        ],
    )
    if result == 0:
        return "backtest/manifest diff output did not fail"
    if "unexpected diff output detected" not in output:
        return f"backtest/manifest diff failure detail missing\n{output}"
    return ""


def test_unexpected_command_failure_fails(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile"],
        [
            ("git diff --check", completed("git", 2, stderr="fatal")),
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
        ],
    )
    if result == 0:
        return "unexpected command failure did not fail overall"
    if "command failed with exit code 2" not in output:
        return f"unexpected command failure detail missing\n{output}"
    return ""


def test_missing_rg_fails_clearly(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile"],
        [
            (
                "rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5",
                FileNotFoundError("rg"),
            )
        ],
    )
    if result == 0:
        return "missing rg did not fail"
    if "missing executable" not in output:
        return f"missing rg failure was not clear\n{output}"
    return ""


def test_review_summary_not_printed_by_default(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile"],
        [("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1))],
    )
    if result != 0:
        return f"default preflight failed\n{output}"
    if "fast_no_trade_review_summary=true" in output:
        return f"review summary printed without --review-summary\n{output}"
    return ""


def test_review_summary_pass_doc_only_outputs_required_fields(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--doc-only", "--skip-profile", "--review-summary"],
        [("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1))],
    )
    if result != 0:
        return f"doc-only review summary preflight failed\n{output}"
    required = (
        "fast_no_trade_review_summary=true",
        "preflight_result=PASS",
        "mode=doc-only",
        "allowed_change_check=SKIPPED",
        "unexpected_changes_count=0",
        "mq5_inventory_expected=7 files",
        "trading_keywords=false",
        "mt5_run=false",
        "trading_executed=false",
        "manifest_created=false",
        "fixture_created=false",
        "report_created=false",
        "external_evidence_copied=false",
        "suggested_git_add=SKIPPED",
    )
    for text in required:
        if text not in output:
            return f"review summary missing required field {text}\n{output}"
    return ""


def test_review_summary_pass_strict_mq5_outputs_mode(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--strict-mq5", "--skip-profile", "--review-summary"],
        [("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1))],
    )
    if result != 0:
        return f"strict-mq5 review summary preflight failed\n{output}"
    if "mode=strict-mq5" not in output:
        return f"strict-mq5 review summary mode missing\n{output}"
    return ""


def test_review_summary_allowed_change_pass_suggests_git_add(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow",
            "docs/CURRENT_TASK.md",
            "--allow",
            "tools/run_fast_no_trade_preflight.py",
            "--allow",
            "tools/test_run_fast_no_trade_preflight.py",
            "--review-summary",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            (
                "git diff --name-only",
                completed(
                    "git",
                    0,
                    stdout=(
                        "docs/CURRENT_TASK.md\n"
                        "tools/run_fast_no_trade_preflight.py\n"
                        "tools/test_run_fast_no_trade_preflight.py\n"
                    ),
                ),
            ),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=(
                        " M docs/CURRENT_TASK.md\n"
                        " M tools/run_fast_no_trade_preflight.py\n"
                        " M tools/test_run_fast_no_trade_preflight.py\n"
                        "?? .vscode/\n"
                        "?? logs/localhost-3000.out.log\n"
                        "?? package-lock.json\n"
                        "?? tools/__pycache__/\n"
                        "?? 鏂板缓 鏂囨湰鏂囨。.txt\n"
                    ),
                ),
            ),
        ],
    )
    if result != 0:
        return f"allowed-change review summary preflight failed\n{output}"
    expected = (
        "suggested_git_add=docs/CURRENT_TASK.md "
        "tools/run_fast_no_trade_preflight.py "
        "tools/test_run_fast_no_trade_preflight.py"
    )
    if expected not in output:
        return f"review summary did not suggest allowed git add list\n{output}"
    blocked = (".vscode", "logs/localhost-3000", "package-lock.json", "tools/__pycache__")
    summary = output.split("fast_no_trade_review_summary=true", 1)[-1]
    for path in blocked:
        if path in summary:
            return f"review summary included known untracked item {path}\n{output}"
    return ""


def test_review_summary_allowed_change_fail_blocks_git_add(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow",
            "docs/CURRENT_TASK.md",
            "--review-summary",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git diff --name-only", completed("git", 0, stdout="docs/PROJECT_STATE.md\n")),
            ("git status --short", completed("git", 0, stdout=" M docs/PROJECT_STATE.md\n")),
        ],
    )
    if result == 0:
        return "allowed-change failure did not fail"
    required = (
        "fast_no_trade_review_summary=true",
        "preflight_result=FAIL",
        "allowed_change_check=FAIL",
        "unexpected_changes_count=1",
        "suggested_git_add=BLOCKED",
    )
    for text in required:
        if text not in output:
            return f"review summary failure missing {text}\n{output}"
    return ""


def test_review_summary_command_failure_reports_fail(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile", "--review-summary"],
        [
            ("git diff --check", completed("git", 2, stderr="fatal")),
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
        ],
    )
    if result == 0:
        return "command failure did not fail"
    if "preflight_result=FAIL" not in output:
        return f"review summary did not report failed preflight\n{output}"
    return ""


def test_emit_trae_command_requires_review_summary(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--emit-trae-command",
            "--task-id",
            "TASK-274",
            "--commit-message",
            "TASK-274 implement fast preflight Trae command preview output",
            "--tag-name",
            "v0.5.75-task-274-fast-preflight-trae-command-preview",
        ],
        [],
    )
    if result == 0:
        return "--emit-trae-command without --review-summary did not fail"
    if "--emit-trae-command requires --review-summary" not in output:
        return f"missing review-summary requirement\n{output}"
    return ""


def test_emit_trae_command_requires_task_id(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--review-summary",
            "--emit-trae-command",
            "--commit-message",
            "TASK-274 implement fast preflight Trae command preview output",
            "--tag-name",
            "v0.5.75-task-274-fast-preflight-trae-command-preview",
        ],
        [],
    )
    if result == 0:
        return "--emit-trae-command without --task-id did not fail"
    if "--emit-trae-command requires --task-id" not in output:
        return f"missing task-id requirement\n{output}"
    return ""


def test_emit_trae_command_requires_commit_message(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--review-summary",
            "--emit-trae-command",
            "--task-id",
            "TASK-274",
            "--tag-name",
            "v0.5.75-task-274-fast-preflight-trae-command-preview",
        ],
        [],
    )
    if result == 0:
        return "--emit-trae-command without --commit-message did not fail"
    if "--emit-trae-command requires --commit-message" not in output:
        return f"missing commit-message requirement\n{output}"
    return ""


def test_emit_trae_command_requires_tag_name(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--review-summary",
            "--emit-trae-command",
            "--task-id",
            "TASK-274",
            "--commit-message",
            "TASK-274 implement fast preflight Trae command preview output",
        ],
        [],
    )
    if result == 0:
        return "--emit-trae-command without --tag-name did not fail"
    if "--emit-trae-command requires --tag-name" not in output:
        return f"missing tag-name requirement\n{output}"
    return ""


def test_emit_trae_command_requires_check_allowed_changes(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--review-summary",
            "--emit-trae-command",
            "--task-id",
            "TASK-274",
            "--commit-message",
            "TASK-274 implement fast preflight Trae command preview output",
            "--tag-name",
            "v0.5.75-task-274-fast-preflight-trae-command-preview",
        ],
        [],
    )
    if result == 0:
        return "--emit-trae-command without --check-allowed-changes did not fail"
    if "--emit-trae-command requires --check-allowed-changes" not in output:
        return f"missing check-allowed-changes requirement\n{output}"
    return ""


def test_emit_trae_command_rejects_invalid_tag_name(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--review-summary",
            "--emit-trae-command",
            "--task-id",
            "TASK-274",
            "--commit-message",
            "TASK-274 implement fast preflight Trae command preview output",
            "--tag-name",
            "release tag",
        ],
        [],
    )
    if result == 0:
        return "invalid tag name did not fail"
    if "--tag-name must start with v and must not contain spaces or newlines" not in output:
        return f"missing invalid tag-name message\n{output}"
    return ""


def test_emit_trae_command_rejects_commit_message_newline(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--review-summary",
            "--emit-trae-command",
            "--task-id",
            "TASK-274",
            "--commit-message",
            "TASK-274 line one\nline two",
            "--tag-name",
            "v0.5.75-task-274-fast-preflight-trae-command-preview",
        ],
        [],
    )
    if result == 0:
        return "commit message with newline did not fail"
    if "--commit-message must not contain newlines" not in output:
        return f"missing commit-message newline message\n{output}"
    return ""


def test_emit_trae_command_outputs_command_block_from_suggested_git_add(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow",
            "docs/CURRENT_TASK.md",
            "--allow",
            "tools/run_fast_no_trade_preflight.py",
            "--review-summary",
            "--emit-trae-command",
            "--task-id",
            "TASK-274",
            "--commit-message",
            "TASK-274 implement fast preflight Trae command preview output",
            "--tag-name",
            "v0.5.75-task-274-fast-preflight-trae-command-preview",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            (
                "git diff --name-only",
                completed(
                    "git",
                    0,
                    stdout="docs/CURRENT_TASK.md\ntools/run_fast_no_trade_preflight.py\n",
                ),
            ),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=" M docs/CURRENT_TASK.md\n M tools/run_fast_no_trade_preflight.py\n",
                ),
            ),
        ],
    )
    if result != 0:
        return f"emit Trae command preview failed\n{output}"
    required = (
        "trae_command_preview=true",
        "task_id=TASK-274",
        "commit_message=TASK-274 implement fast preflight Trae command preview output",
        "tag_name=v0.5.75-task-274-fast-preflight-trae-command-preview",
        "suggested_git_add=docs/CURRENT_TASK.md tools/run_fast_no_trade_preflight.py",
        "command_block_start",
        "git add docs/CURRENT_TASK.md tools/run_fast_no_trade_preflight.py",
        'git commit -m "TASK-274 implement fast preflight Trae command preview output"',
        "git tag v0.5.75-task-274-fast-preflight-trae-command-preview",
        "git log --oneline -1",
        "git tag --points-at HEAD",
        "git rev-parse HEAD",
        "git rev-parse v0.5.75-task-274-fast-preflight-trae-command-preview",
        "git status --short",
        "command_block_end",
    )
    for text in required:
        if text not in output:
            return f"Trae command preview missing {text}\n{output}"
    commands_after_preview = output.split("command_block_start", 1)[-1]
    if "&&" in commands_after_preview:
        return f"Trae command preview used &&\n{output}"
    return ""


def test_emit_trae_command_blocks_on_allowed_change_fail(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow",
            "docs/CURRENT_TASK.md",
            "--review-summary",
            "--emit-trae-command",
            "--task-id",
            "TASK-274",
            "--commit-message",
            "TASK-274 implement fast preflight Trae command preview output",
            "--tag-name",
            "v0.5.75-task-274-fast-preflight-trae-command-preview",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git diff --name-only", completed("git", 0, stdout="docs/PROJECT_STATE.md\n")),
            ("git status --short", completed("git", 0, stdout=" M docs/PROJECT_STATE.md\n")),
        ],
    )
    if result == 0:
        return "allowed-change failure did not block Trae command preview"
    if "trae_command_preview=true" in output or "command_block_start" in output:
        return f"Trae command preview printed despite allowed-change failure\n{output}"
    if "suggested_git_add=BLOCKED" not in output:
        return f"blocked suggested_git_add summary missing\n{output}"
    return ""


def test_emit_trae_command_blocks_when_suggested_git_add_skipped(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--review-summary",
            "--emit-trae-command",
            "--task-id",
            "TASK-274",
            "--commit-message",
            "TASK-274 implement fast preflight Trae command preview output",
            "--tag-name",
            "v0.5.75-task-274-fast-preflight-trae-command-preview",
        ],
        [],
    )
    if result == 0:
        return "SKIPPED suggested_git_add path did not fail"
    if "trae_command_preview=true" in output or "command_block_start" in output:
        return f"Trae command preview printed despite skipped allowed-change guard\n{output}"
    return ""


def test_workflow_preset_doc_state_enables_expected_flags(module) -> str:
    result, calls, output = run_main(
        module,
        ["--workflow-preset", "doc-state"],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git diff --name-only", completed("git", 0, stdout="docs/CURRENT_TASK.md\n")),
            ("git status --short", completed("git", 0, stdout=" M docs/CURRENT_TASK.md\n")),
        ],
    )
    if result != 0:
        return f"doc-state workflow preset failed\n{output}"
    lines = "\n".join(command_text(command) for command in calls)
    if "git diff -- mq5" not in lines:
        return f"doc-state workflow preset did not enable doc-only guard\n{lines}"
    required = (
        "workflow_preset=doc-state",
        "allowed_presets=doc-state",
        "allowed_change_guard=true",
        "allowed_change_check=PASS",
        "fast_no_trade_review_summary=true",
        "mode=doc-only",
    )
    for text in required:
        if text not in output:
            return f"doc-state workflow preset missing {text}\n{output}"
    return ""


def test_workflow_preset_tooling_preflight_enables_expected_flags(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--workflow-preset", "tooling-preflight"],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            (
                "git diff --name-only",
                completed(
                    "git",
                    0,
                    stdout="tools/run_fast_no_trade_preflight.py\ntools/test_run_fast_no_trade_preflight.py\n",
                ),
            ),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=" M tools/run_fast_no_trade_preflight.py\n M tools/test_run_fast_no_trade_preflight.py\n",
                ),
            ),
        ],
    )
    if result != 0:
        return f"tooling-preflight workflow preset failed\n{output}"
    required = (
        "workflow_preset=tooling-preflight",
        "allowed_presets=tooling-preflight",
        "allowed_change_check=PASS",
        "fast_no_trade_review_summary=true",
        "mode=doc-only",
    )
    for text in required:
        if text not in output:
            return f"tooling-preflight workflow preset missing {text}\n{output}"
    return ""


def test_workflow_preset_mq5_observability_enables_expected_flags(module) -> str:
    result, calls, output = run_main(
        module,
        ["--workflow-preset", "mq5-observability"],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git diff --name-only", completed("git", 0, stdout="mq5/core/EaController.mqh\n")),
            ("git status --short", completed("git", 0, stdout=" M mq5/core/EaController.mqh\n")),
        ],
    )
    if result != 0:
        return f"mq5-observability workflow preset failed\n{output}"
    lines = "\n".join(command_text(command) for command in calls)
    if "strict MQ5 forbidden file diff guard" not in output:
        return f"mq5-observability workflow preset did not run strict guard\n{output}"
    if "mq5/TradingSystem.mq5" not in lines:
        return f"mq5-observability workflow preset did not check forbidden MQ5 files\n{lines}"
    required = (
        "workflow_preset=mq5-observability",
        "allowed_presets=mq5-observability",
        "allowed_change_check=PASS",
        "fast_no_trade_review_summary=true",
        "mode=strict-mq5",
    )
    for text in required:
        if text not in output:
            return f"mq5-observability workflow preset missing {text}\n{output}"
    return ""


def test_workflow_preset_emit_trae_command_outputs_command_block(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--workflow-preset",
            "tooling-preflight",
            "--emit-trae-command",
            "--task-id",
            "TASK-275",
            "--commit-message",
            "TASK-275 implement fast preflight workflow presets",
            "--tag-name",
            "v0.5.76-task-275-fast-preflight-workflow-presets",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            (
                "git diff --name-only",
                completed(
                    "git",
                    0,
                    stdout="tools/run_fast_no_trade_preflight.py\ntools/test_run_fast_no_trade_preflight.py\n",
                ),
            ),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=" M tools/run_fast_no_trade_preflight.py\n M tools/test_run_fast_no_trade_preflight.py\n",
                ),
            ),
        ],
    )
    if result != 0:
        return f"workflow preset with Trae command preview failed\n{output}"
    required = (
        "workflow_preset=tooling-preflight",
        "trae_command_preview=true",
        "task_id=TASK-275",
        "command_block_start",
        "git add tools/run_fast_no_trade_preflight.py tools/test_run_fast_no_trade_preflight.py",
        'git commit -m "TASK-275 implement fast preflight workflow presets"',
        "git tag v0.5.76-task-275-fast-preflight-workflow-presets",
        "command_block_end",
    )
    for text in required:
        if text not in output:
            return f"workflow preset Trae command preview missing {text}\n{output}"
    return ""


def test_workflow_preset_stacks_with_extra_allow(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--workflow-preset",
            "doc-state",
            "--allow",
            "tools/run_fast_no_trade_preflight.py",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            (
                "git diff --name-only",
                completed("git", 0, stdout="docs/CURRENT_TASK.md\ntools/run_fast_no_trade_preflight.py\n"),
            ),
            (
                "git status --short",
                completed("git", 0, stdout=" M docs/CURRENT_TASK.md\n M tools/run_fast_no_trade_preflight.py\n"),
            ),
        ],
    )
    if result != 0:
        return f"workflow preset plus --allow did not pass\n{output}"
    if "allowed_change_check=PASS" not in output:
        return f"workflow preset plus --allow missing PASS\n{output}"
    return ""


def test_workflow_preset_stacks_with_extra_allow_prefix(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--workflow-preset",
            "doc-state",
            "--allow-prefix",
            "scratch/",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git diff --name-only", completed("git", 0, stdout="scratch/note.txt\n")),
            ("git status --short", completed("git", 0, stdout="?? scratch/note.txt\n")),
        ],
    )
    if result != 0:
        return f"workflow preset plus --allow-prefix did not pass\n{output}"
    if "allowed_change_check=PASS" not in output:
        return f"workflow preset plus --allow-prefix missing PASS\n{output}"
    return ""


def test_unknown_workflow_preset_fails(module) -> str:
    result, _calls, output = run_main(module, ["--workflow-preset", "unknown"], [])
    if result == 0:
        return "unknown workflow preset did not fail"
    if "unknown workflow preset: unknown" not in output:
        return f"unknown workflow preset failure was not clear\n{output}"
    return ""


def test_workflow_preset_conflicts_with_manual_doc_only(module) -> str:
    result, _calls, output = run_main(module, ["--workflow-preset", "doc-state", "--doc-only"], [])
    if result == 0:
        return "workflow preset with manual --doc-only did not fail"
    if "--workflow-preset conflicts with manual --doc-only" not in output:
        return f"missing workflow/doc-only conflict message\n{output}"
    return ""


def test_workflow_preset_conflicts_with_manual_strict_mq5(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--workflow-preset", "mq5-observability", "--strict-mq5"],
        [],
    )
    if result == 0:
        return "workflow preset with manual --strict-mq5 did not fail"
    if "--workflow-preset conflicts with manual --strict-mq5" not in output:
        return f"missing workflow/strict-mq5 conflict message\n{output}"
    return ""


def test_workflow_preset_conflicts_with_manual_allow_preset(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--workflow-preset", "doc-state", "--allow-preset", "doc-state"],
        [],
    )
    if result == 0:
        return "workflow preset with manual --allow-preset did not fail"
    if "--workflow-preset conflicts with manual --allow-preset" not in output:
        return f"missing workflow/allow-preset conflict message\n{output}"
    return ""


def test_workflow_preset_accepts_manual_review_summary(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--workflow-preset", "doc-state", "--review-summary"],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git diff --name-only", completed("git", 0, stdout="docs/CURRENT_TASK.md\n")),
            ("git status --short", completed("git", 0, stdout=" M docs/CURRENT_TASK.md\n")),
        ],
    )
    if result != 0:
        return f"workflow preset with manual --review-summary did not pass\n{output}"
    if "fast_no_trade_review_summary=true" not in output:
        return f"workflow preset did not retain review summary\n{output}"
    return ""


def test_state_report_not_printed_by_default(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile"],
        [("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1))],
    )
    if result != 0:
        return f"default preflight failed\n{output}"
    if "fast_no_trade_state_report=true" in output:
        return f"state report printed without --state-report\n{output}"
    return ""


def test_state_report_outputs_required_fields(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile", "--state-report"],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git log --oneline -1", completed("git", 0, stdout="abc1234 latest commit\n")),
            ("git tag --points-at HEAD", completed("git", 0, stdout="v0.1.0\n")),
            ("git diff --name-only", completed("git", 0, stdout="docs/CURRENT_TASK.md\n")),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=(
                        " M docs/CURRENT_TASK.md\n"
                        "?? scratch.txt\n"
                        "?? .vscode/\n"
                        "?? logs/localhost-3000.out.log\n"
                        "?? package-lock.json\n"
                        "?? tools/__pycache__/\n"
                        "?? 鏂板缓 鏂囨湰鏂囨。.txt\n"
                    ),
                ),
            ),
        ],
    )
    if result != 0:
        return f"state report preflight failed\n{output}"
    required = (
        "fast_no_trade_state_report=true",
        "current_head=abc1234 latest commit",
        "current_tags_at_head=v0.1.0",
        "workflow_preset=NONE",
        "profile=SKIPPED",
        "mode=default",
        "allowed_change_guard=false",
        "allowed_change_check=SKIPPED",
        "unexpected_changes_count=0",
        "modified_files=docs/CURRENT_TASK.md",
        "untracked_files=scratch.txt",
        "mq5_inventory_expected=7 files",
        "trading_keywords=false",
        "mt5_run=false",
        "trading_executed=false",
        "manifest_created=false",
        "fixture_created=false",
        "report_created=false",
        "external_evidence_copied=false",
        "official_manifest_modified=false",
        "backtest_sets_modified=false",
        "backtest_manifests_modified=false",
    )
    for text in required:
        if text not in output:
            return f"state report missing {text}\n{output}"
    state_report = output.split("fast_no_trade_state_report=true", 1)[-1]
    for ignored in (".vscode", "logs/localhost-3000", "package-lock.json", "tools/__pycache__"):
        if ignored in state_report:
            return f"state report included known untracked item {ignored}\n{output}"
    return ""


def test_state_report_outputs_none_for_empty_head_tags_and_files(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile", "--state-report"],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git log --oneline -1", completed("git", 0, stdout="")),
            ("git tag --points-at HEAD", completed("git", 0, stdout="")),
            ("git diff --name-only", completed("git", 0, stdout="")),
            ("git status --short", completed("git", 0, stdout="?? .vscode/\n?? package-lock.json\n")),
        ],
    )
    if result != 0:
        return f"empty state report preflight failed\n{output}"
    required = (
        "current_head=UNKNOWN",
        "current_tags_at_head=NONE",
        "modified_files=NONE",
        "untracked_files=NONE",
    )
    for text in required:
        if text not in output:
            return f"empty state report missing {text}\n{output}"
    return ""


def test_state_report_with_workflow_preset_review_and_trae_command(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--workflow-preset",
            "tooling-preflight",
            "--state-report",
            "--emit-trae-command",
            "--task-id",
            "TASK-276",
            "--commit-message",
            "TASK-276 implement fast preflight state report stdout",
            "--tag-name",
            "v0.5.77-task-276-fast-preflight-state-report",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git log --oneline -1", completed("git", 0, stdout="abc1234 latest commit\n")),
            ("git tag --points-at HEAD", completed("git", 0, stdout="v0.1.0\n")),
            (
                "git diff --name-only",
                completed(
                    "git",
                    0,
                    stdout="tools/run_fast_no_trade_preflight.py\ntools/test_run_fast_no_trade_preflight.py\n",
                ),
            ),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=" M tools/run_fast_no_trade_preflight.py\n M tools/test_run_fast_no_trade_preflight.py\n",
                ),
            ),
        ],
    )
    if result != 0:
        return f"state report with workflow/Trae preview failed\n{output}"
    required = (
        "fast_no_trade_state_report=true",
        "workflow_preset=tooling-preflight",
        "allowed_change_guard=true",
        "allowed_change_check=PASS",
        "fast_no_trade_review_summary=true",
        "trae_command_preview=true",
        "command_block_start",
    )
    for text in required:
        if text not in output:
            return f"state report workflow integration missing {text}\n{output}"
    return ""


def test_state_report_reports_failure_state(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow",
            "docs/CURRENT_TASK.md",
            "--review-summary",
            "--state-report",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git log --oneline -1", completed("git", 0, stdout="abc1234 latest commit\n")),
            ("git tag --points-at HEAD", completed("git", 0, stdout="v0.1.0\n")),
            ("git diff --name-only", completed("git", 0, stdout="docs/PROJECT_STATE.md\n")),
            ("git status --short", completed("git", 0, stdout=" M docs/PROJECT_STATE.md\n")),
        ],
    )
    if result == 0:
        return "state report failure scenario did not fail"
    required = (
        "preflight_result=FAIL",
        "fast_no_trade_state_report=true",
        "allowed_change_guard=true",
        "allowed_change_check=FAIL",
        "unexpected_changes_count=1",
        "modified_files=docs/PROJECT_STATE.md",
    )
    for text in required:
        if text not in output:
            return f"state report failure output missing {text}\n{output}"
    return ""


def handoff_success_responses():
    return [
        ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
        ("git log --oneline -1", completed("git", 0, stdout="8217709 TASK-276 implement fast preflight state report stdout\n")),
        ("git tag --points-at HEAD", completed("git", 0, stdout="v0.5.77-task-276-fast-preflight-state-report\n")),
        (
            "git diff --name-only",
            completed(
                "git",
                0,
                stdout="tools/run_fast_no_trade_preflight.py\ntools/test_run_fast_no_trade_preflight.py\n",
            ),
        ),
        (
            "git status --short",
            completed(
                "git",
                0,
                stdout=" M tools/run_fast_no_trade_preflight.py\n M tools/test_run_fast_no_trade_preflight.py\n",
            ),
        ),
    ]


def handoff_success_args():
    return [
        "--workflow-preset",
        "tooling-preflight",
        "--state-report",
        "--emit-trae-command",
        "--emit-trae-handoff",
        "--task-id",
        "TASK-277",
        "--commit-message",
        "TASK-277 implement compact Trae handoff instruction output",
        "--tag-name",
        "v0.5.78-task-277-fast-preflight-trae-handoff",
    ]


def test_emit_trae_handoff_requires_state_report(module) -> str:
    args = [arg for arg in handoff_success_args() if arg != "--state-report"]
    result, _calls, output = run_main(module, args, [])
    if result == 0:
        return "--emit-trae-handoff without --state-report did not fail"
    if "--emit-trae-handoff requires --state-report" not in output:
        return f"missing state-report requirement\n{output}"
    return ""


def test_emit_trae_handoff_requires_review_summary(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--state-report",
            "--check-allowed-changes",
            "--emit-trae-command",
            "--emit-trae-handoff",
            "--task-id",
            "TASK-277",
            "--commit-message",
            "TASK-277 implement compact Trae handoff instruction output",
            "--tag-name",
            "v0.5.78-task-277-fast-preflight-trae-handoff",
        ],
        [],
    )
    if result == 0:
        return "--emit-trae-handoff without --review-summary did not fail"
    if "--emit-trae-handoff requires --review-summary" not in output:
        return f"missing review-summary requirement\n{output}"
    return ""


def test_emit_trae_handoff_requires_emit_trae_command(module) -> str:
    args = [arg for arg in handoff_success_args() if arg != "--emit-trae-command"]
    result, _calls, output = run_main(module, args, [])
    if result == 0:
        return "--emit-trae-handoff without --emit-trae-command did not fail"
    if "--emit-trae-handoff requires --emit-trae-command" not in output:
        return f"missing emit-trae-command requirement\n{output}"
    return ""


def test_emit_trae_handoff_requires_check_allowed_changes(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--state-report",
            "--review-summary",
            "--emit-trae-command",
            "--emit-trae-handoff",
            "--task-id",
            "TASK-277",
            "--commit-message",
            "TASK-277 implement compact Trae handoff instruction output",
            "--tag-name",
            "v0.5.78-task-277-fast-preflight-trae-handoff",
        ],
        [],
    )
    if result == 0:
        return "--emit-trae-handoff without --check-allowed-changes did not fail"
    if "--emit-trae-handoff requires --check-allowed-changes" not in output:
        return f"missing check-allowed-changes requirement\n{output}"
    return ""


def test_emit_trae_handoff_requires_task_id_message_and_tag(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--state-report",
            "--review-summary",
            "--check-allowed-changes",
            "--emit-trae-command",
            "--emit-trae-handoff",
        ],
        [],
    )
    if result == 0:
        return "--emit-trae-handoff without task metadata did not fail"
    for text in (
        "--emit-trae-handoff requires --task-id",
        "--emit-trae-handoff requires --commit-message",
        "--emit-trae-handoff requires --tag-name",
    ):
        if text not in output:
            return f"missing handoff metadata requirement {text}\n{output}"
    return ""


def test_emit_trae_handoff_outputs_compact_block(module) -> str:
    result, _calls, output = run_main(
        module,
        handoff_success_args(),
        handoff_success_responses(),
    )
    if result != 0:
        return f"Trae handoff output failed\n{output}"
    required = (
        "trae_handoff_instruction=true",
        "handoff_block_start",
        "发给：Trae",
        "TASK-277 审查、验证、提交、tag",
        "项目：",
        "E:\\GPT\\TradingSystem_Starter",
        "当前 HEAD：",
        "8217709 TASK-276 implement fast preflight state report stdout",
        "当前 tag：",
        "v0.5.77-task-276-fast-preflight-state-report",
        "只允许修改：",
        "tools/run_fast_no_trade_preflight.py",
        "tools/test_run_fast_no_trade_preflight.py",
        "重点确认：",
        "- preflight PASS",
        "- allowed_change_check=PASS",
        "- MQ5 inventory 仍为 7 files",
        "- Buy / Sell / OrderSend / PositionOpen / CTrade 无匹配",
        "验证：",
        "py tools/run_fast_no_trade_preflight.py --workflow-preset tooling-preflight --state-report --review-summary --emit-trae-command --emit-trae-handoff",
        "全部 PASS 且 tag 不存在后连续执行：",
        "git add tools/run_fast_no_trade_preflight.py tools/test_run_fast_no_trade_preflight.py",
        'git commit -m "TASK-277 implement compact Trae handoff instruction output"',
        "git tag v0.5.78-task-277-fast-preflight-trae-handoff",
        "git rev-parse v0.5.78-task-277-fast-preflight-trae-handoff",
        "输出：",
        "handoff_block_end",
    )
    for text in required:
        if text not in output:
            return f"Trae handoff block missing {text}\n{output}"
    handoff = output.split("handoff_block_start", 1)[-1]
    first_handoff_line = handoff.strip().splitlines()[0]
    if first_handoff_line != "发给：Trae":
        return f"handoff block first line was not 发给：Trae\n{output}"
    if "&&" in handoff:
        return f"Trae handoff block used &&\n{output}"
    return ""


def test_emit_trae_handoff_blocks_on_allowed_change_fail(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--state-report",
            "--review-summary",
            "--check-allowed-changes",
            "--allow",
            "docs/CURRENT_TASK.md",
            "--emit-trae-command",
            "--emit-trae-handoff",
            "--task-id",
            "TASK-277",
            "--commit-message",
            "TASK-277 implement compact Trae handoff instruction output",
            "--tag-name",
            "v0.5.78-task-277-fast-preflight-trae-handoff",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git log --oneline -1", completed("git", 0, stdout="8217709 TASK-276 implement fast preflight state report stdout\n")),
            ("git tag --points-at HEAD", completed("git", 0, stdout="v0.5.77-task-276-fast-preflight-state-report\n")),
            ("git diff --name-only", completed("git", 0, stdout="docs/PROJECT_STATE.md\n")),
            ("git status --short", completed("git", 0, stdout=" M docs/PROJECT_STATE.md\n")),
        ],
    )
    if result == 0:
        return "allowed-change failure did not block Trae handoff"
    if "handoff_block_start" in output or "trae_handoff_instruction=true" in output:
        return f"Trae handoff printed despite allowed-change failure\n{output}"
    if "suggested_git_add=BLOCKED" not in output:
        return f"blocked suggested_git_add summary missing\n{output}"
    return ""


def test_emit_trae_handoff_blocks_when_suggested_git_add_skipped(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--state-report",
            "--review-summary",
            "--emit-trae-command",
            "--emit-trae-handoff",
            "--task-id",
            "TASK-277",
            "--commit-message",
            "TASK-277 implement compact Trae handoff instruction output",
            "--tag-name",
            "v0.5.78-task-277-fast-preflight-trae-handoff",
        ],
        [],
    )
    if result == 0:
        return "SKIPPED suggested_git_add path did not fail Trae handoff"
    if "handoff_block_start" in output or "trae_handoff_instruction=true" in output:
        return f"Trae handoff printed despite skipped allowed-change guard\n{output}"
    return ""


def test_emit_trae_handoff_rejects_invalid_tag_and_commit_message(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--state-report",
            "--review-summary",
            "--check-allowed-changes",
            "--emit-trae-command",
            "--emit-trae-handoff",
            "--task-id",
            "TASK-277",
            "--commit-message",
            "TASK-277 line one\nline two",
            "--tag-name",
            "release tag",
        ],
        [],
    )
    if result == 0:
        return "invalid handoff metadata did not fail"
    for text in (
        "--commit-message must not contain newlines",
        "--tag-name must start with v and must not contain spaces or newlines",
    ):
        if text not in output:
            return f"missing invalid handoff metadata message {text}\n{output}"
    return ""


def test_compact_report_not_printed_by_default(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile"],
        [("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1))],
    )
    if result != 0:
        return f"default preflight failed\n{output}"
    if "fast_no_trade_compact_report=true" in output:
        return f"compact report printed without --compact-report\n{output}"
    return ""


def test_compact_report_outputs_required_fields(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile", "--compact-report"],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git log --oneline -1", completed("git", 0, stdout="90bb6b8 TASK-277 implement compact Trae handoff instruction output\n")),
            ("git tag --points-at HEAD", completed("git", 0, stdout="v0.5.78-task-277-fast-preflight-trae-handoff\n")),
            ("git diff --name-only", completed("git", 0, stdout="tools/run_fast_no_trade_preflight.py\n")),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=(
                        " M tools/run_fast_no_trade_preflight.py\n"
                        "?? scratch.txt\n"
                        "?? .vscode/\n"
                        "?? logs/localhost-3000.out.log\n"
                        "?? package-lock.json\n"
                        "?? tools/__pycache__/\n"
                    ),
                ),
            ),
        ],
    )
    if result != 0:
        return f"compact report preflight failed\n{output}"
    required = (
        "fast_no_trade_compact_report=true",
        "fast_no_trade_state_report=true",
        "current_head=90bb6b8 TASK-277 implement compact Trae handoff instruction output",
        "current_tags_at_head=v0.5.78-task-277-fast-preflight-trae-handoff",
        "workflow_preset=NONE",
        "profile=SKIPPED",
        "mode=default",
        "allowed_change_guard=false",
        "allowed_change_check=SKIPPED",
        "unexpected_changes_count=0",
        "modified_files=tools/run_fast_no_trade_preflight.py",
        "untracked_files=scratch.txt",
        "fast_no_trade_review_summary=true",
        "preflight_result=PASS",
        "review-summary=PASS",
        "trae_command_preview=SKIPPED",
        "trae_handoff_instruction=SKIPPED",
        "mq5_inventory_expected=7 files",
        "trading_keywords=false",
        "mt5_run=false",
        "trading_executed=false",
        "manifest_created=false",
        "fixture_created=false",
        "report_created=false",
        "external_evidence_copied=false",
        "suggested_git_add=SKIPPED",
    )
    for text in required:
        if text not in output:
            return f"compact report missing {text}\n{output}"
    compact_report = output.split("fast_no_trade_compact_report=true", 1)[-1]
    for ignored in (".vscode", "logs/localhost-3000", "package-lock.json", "tools/__pycache__"):
        if ignored in compact_report:
            return f"compact report included known untracked item {ignored}\n{output}"
    return ""


def test_compact_report_with_workflow_command_and_handoff(module) -> str:
    result, _calls, output = run_main(
        module,
        handoff_success_args() + ["--compact-report"],
        handoff_success_responses(),
    )
    if result != 0:
        return f"compact report with workflow/command/handoff failed\n{output}"
    required = (
        "fast_no_trade_compact_report=true",
        "fast_no_trade_state_report=true",
        "workflow_preset=tooling-preflight",
        "allowed_change_guard=true",
        "allowed_change_check=PASS",
        "fast_no_trade_review_summary=true",
        "preflight_result=PASS",
        "review-summary=PASS",
        "trae_command_preview=PASS",
        "trae_handoff_instruction=PASS",
        "suggested_git_add=tools/run_fast_no_trade_preflight.py tools/test_run_fast_no_trade_preflight.py",
        "command_block_start",
        "handoff_block_start",
    )
    for text in required:
        if text not in output:
            return f"compact report workflow integration missing {text}\n{output}"
    return ""


def test_compact_report_reports_failure_state(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow",
            "docs/CURRENT_TASK.md",
            "--review-summary",
            "--state-report",
            "--emit-trae-command",
            "--emit-trae-handoff",
            "--compact-report",
            "--task-id",
            "TASK-278",
            "--commit-message",
            "TASK-278 implement compact preflight combined report output",
            "--tag-name",
            "v0.5.79-task-278-compact-preflight-report",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git log --oneline -1", completed("git", 0, stdout="90bb6b8 TASK-277 implement compact Trae handoff instruction output\n")),
            ("git tag --points-at HEAD", completed("git", 0, stdout="v0.5.78-task-277-fast-preflight-trae-handoff\n")),
            ("git diff --name-only", completed("git", 0, stdout="docs/PROJECT_STATE.md\n")),
            ("git status --short", completed("git", 0, stdout=" M docs/PROJECT_STATE.md\n")),
        ],
    )
    if result == 0:
        return "compact report failure scenario did not fail"
    required = (
        "fast_no_trade_compact_report=true",
        "preflight_result=FAIL",
        "allowed_change_guard=true",
        "allowed_change_check=FAIL",
        "unexpected_changes_count=1",
        "modified_files=docs/PROJECT_STATE.md",
        "suggested_git_add=BLOCKED",
        "trae_command_preview=BLOCKED",
        "trae_handoff_instruction=BLOCKED",
    )
    for text in required:
        if text not in output:
            return f"compact report failure output missing {text}\n{output}"
    return ""


def test_workflow_closure_audit_not_printed_by_default(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile"],
        [("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1))],
    )
    if result != 0:
        return f"default preflight failed\n{output}"
    if "workflow_closure_audit=true" in output:
        return f"closure audit printed without --workflow-closure-audit\n{output}"
    return ""


def test_workflow_closure_audit_outputs_required_fields(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile", "--workflow-closure-audit"],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git log --oneline -1", completed("git", 0, stdout="7e93d14 TASK-278 implement compact preflight combined report output\n")),
            ("git tag --points-at HEAD", completed("git", 0, stdout="v0.5.79-task-278-compact-preflight-report\n")),
            ("git diff --name-only", completed("git", 0, stdout="tools/run_fast_no_trade_preflight.py\n")),
            (
                "git status --short",
                completed(
                    "git",
                    0,
                    stdout=(
                        " M tools/run_fast_no_trade_preflight.py\n"
                        "?? scratch.txt\n"
                        "?? .vscode/\n"
                        "?? logs/localhost-3000.out.log\n"
                        "?? package-lock.json\n"
                        "?? tools/__pycache__/\n"
                    ),
                ),
            ),
        ],
    )
    if result != 0:
        return f"closure audit preflight failed\n{output}"
    required = (
        "workflow_closure_audit=true",
        "release_ready_closure_audit=true",
        "stdout_only=true",
        "fast_no_trade_state_report=true",
        "fast_no_trade_review_summary=true",
        "workflow_preset=NONE",
        "profile=SKIPPED",
        "allowed_change_check=SKIPPED",
        "validator_self_test_summary=PASS",
        "preflight_result=PASS",
        "review-summary=PASS",
        "trae_command_preview=SKIPPED",
        "trae_handoff_instruction=SKIPPED",
        "mq5_inventory_expected=7 files",
        "trading_keywords=false",
        "no_mt5_run=true",
        "no_trading=true",
        "no_manifest=true",
        "no_fixture=true",
        "no_report=true",
        "no_external_evidence=true",
        "mt5_run=false",
        "trading_executed=false",
        "manifest_created=false",
        "fixture_created=false",
        "report_created=false",
        "external_evidence_copied=false",
        "closure_audit_ready=PASS",
        "suggested_git_add=SKIPPED",
    )
    for text in required:
        if text not in output:
            return f"closure audit missing {text}\n{output}"
    closure_report = output.split("workflow_closure_audit=true", 1)[-1]
    for ignored in (".vscode", "logs/localhost-3000", "package-lock.json", "tools/__pycache__"):
        if ignored in closure_report:
            return f"closure audit included known untracked item {ignored}\n{output}"
    return ""


def test_workflow_closure_audit_with_workflow_command_and_handoff(module) -> str:
    result, _calls, output = run_main(
        module,
        handoff_success_args() + ["--workflow-closure-audit"],
        handoff_success_responses(),
    )
    if result != 0:
        return f"closure audit with workflow/command/handoff failed\n{output}"
    required = (
        "workflow_closure_audit=true",
        "release_ready_closure_audit=true",
        "workflow_preset=tooling-preflight",
        "allowed_change_guard=true",
        "allowed_change_check=PASS",
        "validator_self_test_summary=PASS",
        "trae_command_preview=PASS",
        "trae_handoff_instruction=PASS",
        "suggested_git_add=tools/run_fast_no_trade_preflight.py tools/test_run_fast_no_trade_preflight.py",
        "command_block_start",
        "handoff_block_start",
    )
    for text in required:
        if text not in output:
            return f"closure audit workflow integration missing {text}\n{output}"
    return ""


def test_workflow_closure_audit_reports_failure_state(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow",
            "docs/CURRENT_TASK.md",
            "--review-summary",
            "--state-report",
            "--emit-trae-command",
            "--emit-trae-handoff",
            "--workflow-closure-audit",
            "--task-id",
            "TASK-280",
            "--commit-message",
            "TASK-280 implement no-trade development workflow closure audit",
            "--tag-name",
            "v0.5.81-task-280-no-trade-workflow-closure-audit",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git log --oneline -1", completed("git", 0, stdout="7e93d14 TASK-278 implement compact preflight combined report output\n")),
            ("git tag --points-at HEAD", completed("git", 0, stdout="v0.5.79-task-278-compact-preflight-report\n")),
            ("git diff --name-only", completed("git", 0, stdout="mq5/TradingSystem.mq5\n")),
            ("git status --short", completed("git", 0, stdout=" M mq5/TradingSystem.mq5\n")),
        ],
    )
    if result == 0:
        return "closure audit failure scenario did not fail"
    required = (
        "workflow_closure_audit=true",
        "preflight_result=FAIL",
        "allowed_change_guard=true",
        "allowed_change_check=FAIL",
        "validator_self_test_summary=FAIL",
        "unexpected_changes_count=1",
        "modified_files=mq5/TradingSystem.mq5",
        "suggested_git_add=BLOCKED",
        "trae_command_preview=BLOCKED",
        "trae_handoff_instruction=BLOCKED",
        "closure_audit_ready=FAIL",
    )
    for text in required:
        if text not in output:
            return f"closure audit failure output missing {text}\n{output}"
    return ""


def test_final_milestone_report_not_printed_by_default(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile"],
        [("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1))],
    )
    if result != 0:
        return f"default preflight failed\n{output}"
    if "final_milestone_report=true" in output:
        return f"final milestone report printed without --final-milestone-report\n{output}"
    return ""


def test_final_milestone_report_outputs_required_fields(module) -> str:
    result, _calls, output = run_main(
        module,
        ["--skip-profile", "--final-milestone-report"],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git log --oneline -1", completed("git", 0, stdout="098a985 TASK-289 reconcile observability helper validator tracking gap\n")),
            ("git tag --points-at HEAD", completed("git", 0, stdout="v0.5.88-task-289-reconcile-observability-helper-validator-tracking\n")),
            ("git diff --name-only", completed("git", 0, stdout="tools/run_fast_no_trade_preflight.py\n")),
            ("git status --short", completed("git", 0, stdout=" M tools/run_fast_no_trade_preflight.py\n?? .vscode/\n")),
        ],
    )
    if result != 0:
        return f"final milestone preflight failed\n{output}"
    required = (
        "final_milestone_report=true",
        "release_ready_milestone_closure=true",
        "stdout_only=true",
        "TASK-266_to_TASK-289_status=covered",
        "task_range=TASK-266..TASK-289",
        "preflight_state_report=covered",
        "review_summary=covered",
        "allowed_change_check=covered",
        "workflow_preset=covered",
        "trae_handoff_blocks=covered",
        "validator_self_test_results=covered",
        "validator_self_test_summary=PASS",
        "mq5-inventory=PASS",
        "mq5-no-trade-observability=PASS",
        "mq5-static-interface-consistency=PASS",
        "mq5-static-include-consistency=PASS",
        "mq5-lifecycle-route-consistency=PASS",
        "mq5-observability-helper-consistency=PASS",
        "mq5-telemetry-aggregation=PASS",
        "project-state-docs=PASS",
        "project-state-docs-self-test=PASS",
        "mq5_inventory_expected=7 files",
        "trading_keywords=false",
        "no_mt5_run=true",
        "no_mql5_compile=true",
        "no_trading=true",
        "no_manifest=true",
        "no_fixture=true",
        "no_report=true",
        "no_external_evidence=true",
        "mql5_compile_executed=false",
        "git_add_executed=false",
        "git_commit_executed=false",
        "git_tag_executed=false",
        "task_id=TASK-290",
        "tag_name=v0.5.89-task-290-final-no-trade-workflow-milestone-report",
        "milestone_closure_ready=PASS",
    )
    for text in required:
        if text not in output:
            return f"final milestone report missing {text}\n{output}"
    return ""


def test_final_milestone_report_with_workflow_command_handoff_and_compressed_summary(module) -> str:
    result, _calls, output = run_main(
        module,
        handoff_success_args() + ["--final-milestone-report", "--compact-report", "--compressed-summary"],
        handoff_success_responses(),
    )
    if result != 0:
        return f"final milestone with workflow/command/handoff failed\n{output}"
    required = (
        "final_milestone_report=true",
        "release_ready_milestone_closure=true",
        "workflow_preset=tooling-preflight",
        "allowed_change_guard=true",
        "allowed_change_check=PASS",
        "trae_command_preview=PASS",
        "trae_handoff_instruction=PASS",
        "suggested_git_add=tools/run_fast_no_trade_preflight.py tools/test_run_fast_no_trade_preflight.py",
        "command_block_start",
        "handoff_block_start",
    )
    for text in required:
        if text not in output:
            return f"final milestone workflow integration missing {text}\n{output}"
    return ""


def test_final_milestone_report_reports_failure_state(module) -> str:
    result, _calls, output = run_main(
        module,
        [
            "--skip-profile",
            "--check-allowed-changes",
            "--allow",
            "docs/CURRENT_TASK.md",
            "--review-summary",
            "--state-report",
            "--emit-trae-command",
            "--emit-trae-handoff",
            "--final-milestone-report",
        ],
        [
            ("rg Buy|Sell|OrderSend|PositionOpen|CTrade mq5", completed("rg", 1)),
            ("git log --oneline -1", completed("git", 0, stdout="098a985 TASK-289 reconcile observability helper validator tracking gap\n")),
            ("git tag --points-at HEAD", completed("git", 0, stdout="v0.5.88-task-289-reconcile-observability-helper-validator-tracking\n")),
            ("git diff --name-only", completed("git", 0, stdout="mq5/TradingSystem.mq5\n")),
            ("git status --short", completed("git", 0, stdout=" M mq5/TradingSystem.mq5\n")),
        ],
    )
    if result == 0:
        return "final milestone failure scenario did not fail"
    required = (
        "final_milestone_report=true",
        "preflight_result=FAIL",
        "allowed_change_check=FAIL",
        "validator_self_test_summary=FAIL",
        "unexpected_changes_count=1",
        "modified_files=mq5/TradingSystem.mq5",
        "trae_command_preview=BLOCKED",
        "trae_handoff_instruction=BLOCKED",
        "milestone_closure_ready=FAIL",
    )
    for text in required:
        if text not in output:
            return f"final milestone failure output missing {text}\n{output}"
    return ""


def main() -> int:
    if not PREFLIGHT_PATH.exists():
        return fail(f"preflight script not found: {PREFLIGHT_PATH}")

    module = load_preflight_module()
    tests = [
        test_default_runs_fast_profile,
        test_rg_no_match_exit_one_passes,
        test_skip_profile_omits_release_bundle,
        test_allowed_change_guard_allows_explicit_files,
        test_allowed_change_guard_allows_prefix,
        test_allow_preset_doc_state_expands_allowed_files,
        test_allow_preset_tooling_preflight_expands_allowed_files,
        test_allow_preset_mq5_observability_expands_allowed_files,
        test_allow_preset_stacks_with_allow,
        test_allow_preset_stacks_with_allow_prefix,
        test_unknown_allow_preset_fails,
        test_allow_preset_requires_check_allowed_changes,
        test_allowed_change_guard_rejects_unallowed_tracked_diff,
        test_allowed_change_guard_rejects_unallowed_untracked_file,
        test_allowed_change_guard_ignores_known_untracked_items,
        test_doc_only_with_allowed_change_guard_passes,
        test_strict_mq5_with_allowed_change_guard_passes,
        test_rg_match_exit_zero_fails,
        test_doc_only_checks_mq5_diff,
        test_strict_mq5_checks_forbidden_files,
        test_backtest_manifest_diff_output_fails,
        test_unexpected_command_failure_fails,
        test_missing_rg_fails_clearly,
        test_review_summary_not_printed_by_default,
        test_review_summary_pass_doc_only_outputs_required_fields,
        test_review_summary_pass_strict_mq5_outputs_mode,
        test_review_summary_allowed_change_pass_suggests_git_add,
        test_review_summary_allowed_change_fail_blocks_git_add,
        test_review_summary_command_failure_reports_fail,
        test_emit_trae_command_requires_review_summary,
        test_emit_trae_command_requires_task_id,
        test_emit_trae_command_requires_commit_message,
        test_emit_trae_command_requires_tag_name,
        test_emit_trae_command_requires_check_allowed_changes,
        test_emit_trae_command_rejects_invalid_tag_name,
        test_emit_trae_command_rejects_commit_message_newline,
        test_emit_trae_command_outputs_command_block_from_suggested_git_add,
        test_emit_trae_command_blocks_on_allowed_change_fail,
        test_emit_trae_command_blocks_when_suggested_git_add_skipped,
        test_workflow_preset_doc_state_enables_expected_flags,
        test_workflow_preset_tooling_preflight_enables_expected_flags,
        test_workflow_preset_mq5_observability_enables_expected_flags,
        test_workflow_preset_emit_trae_command_outputs_command_block,
        test_workflow_preset_stacks_with_extra_allow,
        test_workflow_preset_stacks_with_extra_allow_prefix,
        test_unknown_workflow_preset_fails,
        test_workflow_preset_conflicts_with_manual_doc_only,
        test_workflow_preset_conflicts_with_manual_strict_mq5,
        test_workflow_preset_conflicts_with_manual_allow_preset,
        test_workflow_preset_accepts_manual_review_summary,
        test_state_report_not_printed_by_default,
        test_state_report_outputs_required_fields,
        test_state_report_outputs_none_for_empty_head_tags_and_files,
        test_state_report_with_workflow_preset_review_and_trae_command,
        test_state_report_reports_failure_state,
        test_emit_trae_handoff_requires_state_report,
        test_emit_trae_handoff_requires_review_summary,
        test_emit_trae_handoff_requires_emit_trae_command,
        test_emit_trae_handoff_requires_check_allowed_changes,
        test_emit_trae_handoff_requires_task_id_message_and_tag,
        test_emit_trae_handoff_outputs_compact_block,
        test_emit_trae_handoff_blocks_on_allowed_change_fail,
        test_emit_trae_handoff_blocks_when_suggested_git_add_skipped,
        test_emit_trae_handoff_rejects_invalid_tag_and_commit_message,
        test_compact_report_not_printed_by_default,
        test_compact_report_outputs_required_fields,
        test_compact_report_with_workflow_command_and_handoff,
        test_compact_report_reports_failure_state,
        test_workflow_closure_audit_not_printed_by_default,
        test_workflow_closure_audit_outputs_required_fields,
        test_workflow_closure_audit_with_workflow_command_and_handoff,
        test_workflow_closure_audit_reports_failure_state,
        test_final_milestone_report_not_printed_by_default,
        test_final_milestone_report_outputs_required_fields,
        test_final_milestone_report_with_workflow_command_handoff_and_compressed_summary,
        test_final_milestone_report_reports_failure_state,
    ]

    for test in tests:
        error = test(module)
        if error:
            return fail(error)

    print("Fast no-trade preflight self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
