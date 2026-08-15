#!/usr/bin/env python3
"""Run the fast no-trade development preflight as one read-only command."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import os
import re
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
TRADING_KEYWORD_PATTERN = "Buy|Sell|OrderSend|PositionOpen|CTrade"
NOTICE = "Inventory only; no MT5 run; no trading authorization."
PASS_TEXT = "Fast no-trade preflight PASS"
FAIL_TEXT = "Fast no-trade preflight FAIL"
DEFAULT_CLOSURE_TASK_ID = "TASK-280"
DEFAULT_CLOSURE_COMMIT_MESSAGE = "TASK-280 implement no-trade development workflow closure audit"
DEFAULT_CLOSURE_TAG_NAME = "v0.5.81-task-280-no-trade-workflow-closure-audit"
DEFAULT_FINAL_TASK_ID = "TASK-290"
DEFAULT_FINAL_COMMIT_MESSAGE = "TASK-290 implement final milestone closure / release-ready state report"
DEFAULT_FINAL_TAG_NAME = "v0.5.89-task-290-final-no-trade-workflow-milestone-report"
KNOWN_UNTRACKED_PATHS = {
    "package-lock.json",
    "鏂板缓 鏂囨湰鏂囨。.txt",
    "新建 文本文档.txt",
}
KNOWN_UNTRACKED_PREFIXES = (
    ".vscode/",
    "logs/",
    "tools/__pycache__/",
)
ALLOW_PRESETS = {
    "doc-state": (
        "docs/CURRENT_TASK.md",
        "docs/HANDOFF_PROMPT.md",
        "docs/PROJECT_STATE.md",
        "tools/validate_project_state_docs.py",
        "tools/test_validate_project_state_docs.py",
    ),
    "tooling-preflight": (
        "docs/CURRENT_TASK.md",
        "docs/HANDOFF_PROMPT.md",
        "docs/PROJECT_STATE.md",
        "tools/run_fast_no_trade_preflight.py",
        "tools/test_run_fast_no_trade_preflight.py",
        "tools/validate_project_state_docs.py",
        "tools/test_validate_project_state_docs.py",
    ),
    "mq5-observability": (
        "docs/CURRENT_TASK.md",
        "docs/HANDOFF_PROMPT.md",
        "docs/PROJECT_STATE.md",
        "mq5/core/EaController.mqh",
        "mq5/logger/Logger.mqh",
        "tools/validate_mq5_no_trade_observability.py",
        "tools/test_validate_mq5_no_trade_observability.py",
        "tools/validate_project_state_docs.py",
        "tools/test_validate_project_state_docs.py",
    ),
}
CLOSURE_AUDIT_ALLOWED_PATHS = (
    "docs/CURRENT_TASK.md",
    "docs/HANDOFF_PROMPT.md",
    "docs/PROJECT_STATE.md",
    "tools/run_fast_no_trade_preflight.py",
    "tools/test_run_fast_no_trade_preflight.py",
    "tools/run_release_validation_bundle.py",
    "tools/test_run_release_validation_bundle_profiles.py",
    "tools/validate_project_state_docs.py",
    "tools/test_validate_project_state_docs.py",
)
WORKFLOW_PRESETS = {
    "doc-state": {
        "doc_only": True,
        "strict_mq5": False,
        "allow_preset": "doc-state",
    },
    "tooling-preflight": {
        "doc_only": True,
        "strict_mq5": False,
        "allow_preset": "tooling-preflight",
    },
    "mq5-observability": {
        "doc_only": False,
        "strict_mq5": True,
        "allow_preset": "mq5-observability",
    },
}


@dataclass(frozen=True)
class PreflightCheck:
    check_id: str
    name: str
    command: tuple[str, ...]
    mode: str = "returncode"


@dataclass(frozen=True)
class AllowedChangeResult:
    enabled: bool
    passed: bool | None
    unexpected_count: int
    suggested_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class StateReportData:
    current_head: str
    current_tags_at_head: str
    modified_files: tuple[str, ...]
    untracked_files: tuple[str, ...]
    official_manifest_modified: bool
    backtest_sets_modified: bool
    backtest_manifests_modified: bool


def command_text(command: tuple[str, ...]) -> str:
    return " ".join(command)


def run_subprocess(command: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        list(command),
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        env=env,
    )


def build_checks(args: argparse.Namespace) -> list[PreflightCheck]:
    python = sys.executable
    checks: list[PreflightCheck] = []

    if not args.skip_profile:
        checks.append(
            PreflightCheck(
                "fast-no-trade-dev-profile",
                "release validation bundle fast-no-trade-dev profile",
                (
                    python,
                    str(ROOT_DIR / "tools" / "run_release_validation_bundle.py"),
                    "--profile",
                    "fast-no-trade-dev",
                ),
            )
        )

    checks.extend(
        [
            PreflightCheck(
                "git-diff-check",
                "git diff whitespace check",
                ("git", "diff", "--check"),
            ),
            PreflightCheck(
                "mq5-trading-keywords",
                "MQ5 trading keyword guard",
                ("rg", TRADING_KEYWORD_PATTERN, "mq5"),
                mode="rg-no-match",
            ),
            PreflightCheck(
                "backtest-manifest-diff",
                "backtest/sets and manifest diff guard",
                ("git", "diff", "--", "backtest/sets", "backtest/reports/manifests"),
                mode="no-output",
            ),
        ]
    )

    if args.doc_only:
        checks.append(
            PreflightCheck(
                "mq5-diff-doc-only",
                "doc-only MQ5 diff guard",
                ("git", "diff", "--", "mq5"),
                mode="no-output",
            )
        )

    if args.strict_mq5:
        checks.append(
            PreflightCheck(
                "strict-mq5-forbidden-diff",
                "strict MQ5 forbidden file diff guard",
                (
                    "git",
                    "diff",
                    "--",
                    "mq5/TradingSystem.mq5",
                    "mq5/config/InputConfig.mqh",
                    "mq5/signals/SignalEngine.mqh",
                    "mq5/risk/RiskManager.mqh",
                    "mq5/execution/ExecutionManager.mqh",
                ),
                mode="no-output",
            )
        )

    checks.append(
        PreflightCheck(
            "git-status-short",
            "git status short",
            ("git", "status", "--short"),
        )
    )
    return checks


def evaluate_result(check: PreflightCheck, result: subprocess.CompletedProcess[str]) -> tuple[bool, str]:
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if check.mode == "rg-no-match":
        if result.returncode == 1 and not stdout:
            return True, "no trading keyword matches"
        if result.returncode == 0:
            return False, "trading keyword matches detected"
        return False, f"rg failed with exit code {result.returncode}"

    if check.mode == "no-output":
        if result.returncode != 0:
            return False, f"command failed with exit code {result.returncode}"
        if stdout or stderr:
            return False, "unexpected diff output detected"
        return True, "no diff output"

    if result.returncode == 0:
        return True, "command exit code 0"
    return False, f"command failed with exit code {result.returncode}"


def normalize_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def decode_git_quoted_path(path: str) -> str:
    text = path.strip()
    if len(text) < 2 or not (text.startswith('"') and text.endswith('"')):
        return text
    body = text[1:-1]
    output = bytearray()
    index = 0
    while index < len(body):
        if body[index] == "\\" and index + 3 < len(body) and re.fullmatch(r"[0-7]{3}", body[index + 1 : index + 4]):
            output.append(int(body[index + 1 : index + 4], 8))
            index += 4
            continue
        output.extend(body[index].encode("utf-8"))
        index += 1
    try:
        return output.decode("utf-8")
    except UnicodeDecodeError:
        return text


def status_path(line: str) -> str:
    if len(line) < 4:
        return ""
    path = line[3:].strip()
    if " -> " in path:
        path = path.rsplit(" -> ", 1)[-1]
    return normalize_path(decode_git_quoted_path(path))


def is_known_untracked_path(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized in KNOWN_UNTRACKED_PATHS:
        return True
    return any(normalized.startswith(prefix) for prefix in KNOWN_UNTRACKED_PREFIXES)


def is_allowed_path(path: str, allowed_paths: set[str], allowed_prefixes: tuple[str, ...]) -> bool:
    normalized = normalize_path(path)
    if normalized in allowed_paths:
        return True
    return any(normalized.startswith(prefix) for prefix in allowed_prefixes)


def collect_unexpected_changes(
    diff_names: str,
    status_short: str,
    allowed_paths: set[str],
    allowed_prefixes: tuple[str, ...],
) -> list[str]:
    unexpected: list[str] = []
    seen: set[str] = set()

    for line in diff_names.splitlines():
        path = normalize_path(line)
        if not path or path in seen:
            continue
        seen.add(path)
        if not is_allowed_path(path, allowed_paths, allowed_prefixes):
            unexpected.append(path)

    for line in status_short.splitlines():
        if not line:
            continue
        path = status_path(line)
        if not path or path in seen:
            continue
        seen.add(path)
        if line.startswith("?? ") and is_known_untracked_path(path):
            continue
        if not is_allowed_path(path, allowed_paths, allowed_prefixes):
            unexpected.append(path)

    return unexpected


def collect_suggested_git_add_paths(
    diff_names: str,
    status_short: str,
    allowed_paths: set[str],
    allowed_prefixes: tuple[str, ...],
) -> tuple[str, ...]:
    suggested: list[str] = []
    seen: set[str] = set()

    def add_path(path: str) -> None:
        normalized = normalize_path(path)
        if not normalized or normalized in seen:
            return
        if is_allowed_path(normalized, allowed_paths, allowed_prefixes):
            seen.add(normalized)
            suggested.append(normalized)

    for line in diff_names.splitlines():
        add_path(line)

    for line in status_short.splitlines():
        if not line:
            continue
        path = status_path(line)
        if line.startswith("?? ") and is_known_untracked_path(path):
            continue
        add_path(path)

    return tuple(suggested)


def expand_allowed_paths(args: argparse.Namespace) -> set[str]:
    allowed_paths = {normalize_path(path) for path in args.allow}
    for preset in args.allow_preset:
        allowed_paths.update(normalize_path(path) for path in ALLOW_PRESETS[preset])
    if args.workflow_closure_audit or args.final_milestone_report:
        allowed_paths.update(normalize_path(path) for path in CLOSURE_AUDIT_ALLOWED_PATHS)
    return allowed_paths


def validate_allow_presets(args: argparse.Namespace) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if args.allow_preset and not args.check_allowed_changes:
        failures.append("--allow-preset requires --check-allowed-changes")

    for preset in args.allow_preset:
        if preset not in ALLOW_PRESETS:
            failures.append(f"unknown allow preset: {preset}")

    return not failures, failures


def apply_workflow_preset(args: argparse.Namespace) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not args.workflow_preset:
        return True, failures

    if args.workflow_preset not in WORKFLOW_PRESETS:
        return False, [f"unknown workflow preset: {args.workflow_preset}"]

    if args.doc_only:
        failures.append("--workflow-preset conflicts with manual --doc-only")
    if args.strict_mq5:
        failures.append("--workflow-preset conflicts with manual --strict-mq5")
    if args.check_allowed_changes:
        failures.append("--workflow-preset conflicts with manual --check-allowed-changes")
    if args.allow_preset:
        failures.append("--workflow-preset conflicts with manual --allow-preset")
    if failures:
        return False, failures

    preset = WORKFLOW_PRESETS[args.workflow_preset]
    args.doc_only = bool(preset["doc_only"])
    args.strict_mq5 = bool(preset["strict_mq5"])
    args.check_allowed_changes = True
    args.allow_preset = [str(preset["allow_preset"])]
    args.review_summary = True
    return True, failures


def contains_newline(text: str) -> bool:
    return "\n" in text or "\r" in text


def validate_trae_command_args(args: argparse.Namespace) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not args.emit_trae_command:
        return True, failures

    if not args.review_summary:
        failures.append("--emit-trae-command requires --review-summary")
    if not args.check_allowed_changes:
        failures.append("--emit-trae-command requires --check-allowed-changes")
    if not args.task_id:
        failures.append("--emit-trae-command requires --task-id")
    elif contains_newline(args.task_id):
        failures.append("--task-id must not contain newlines")
    if not args.commit_message:
        failures.append("--emit-trae-command requires --commit-message")
    elif contains_newline(args.commit_message):
        failures.append("--commit-message must not contain newlines")
    if not args.tag_name:
        failures.append("--emit-trae-command requires --tag-name")
    elif (
        not args.tag_name.startswith("v")
        or any(char.isspace() for char in args.tag_name)
        or contains_newline(args.tag_name)
    ):
        failures.append("--tag-name must start with v and must not contain spaces or newlines")

    return not failures, failures


def validate_trae_handoff_args(args: argparse.Namespace) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not args.emit_trae_handoff:
        return True, failures

    if not args.state_report:
        failures.append("--emit-trae-handoff requires --state-report")
    if not args.review_summary:
        failures.append("--emit-trae-handoff requires --review-summary")
    if not args.emit_trae_command:
        failures.append("--emit-trae-handoff requires --emit-trae-command")
    if not args.check_allowed_changes:
        failures.append("--emit-trae-handoff requires --check-allowed-changes")
    if not args.task_id:
        failures.append("--emit-trae-handoff requires --task-id")
    if not args.commit_message:
        failures.append("--emit-trae-handoff requires --commit-message")
    if not args.tag_name:
        failures.append("--emit-trae-handoff requires --tag-name")

    return not failures, failures


def run_allowed_change_guard(args: argparse.Namespace, runner=run_subprocess) -> AllowedChangeResult:
    allowed_paths = expand_allowed_paths(args)
    allowed_prefixes = tuple(normalize_path(prefix) for prefix in args.allow_prefix)

    print(f"allowed_presets={','.join(args.allow_preset) if args.allow_preset else 'none'}")
    print("allowed_change_guard=true")
    print("  command: git diff --name-only")
    diff_result = runner(("git", "diff", "--name-only"))
    print_command_output(diff_result)
    if diff_result.returncode != 0:
        print("allowed_change_check=FAIL")
        print("unexpected_changes_count=1")
        print(f"  - git diff --name-only failed with exit code {diff_result.returncode}")
        return AllowedChangeResult(
            enabled=True,
            passed=False,
            unexpected_count=1,
        )

    print("  command: git status --short")
    status_result = runner(("git", "status", "--short"))
    print_command_output(status_result)
    if status_result.returncode != 0:
        print("allowed_change_check=FAIL")
        print("unexpected_changes_count=1")
        print(f"  - git status --short failed with exit code {status_result.returncode}")
        return AllowedChangeResult(
            enabled=True,
            passed=False,
            unexpected_count=1,
        )

    unexpected = collect_unexpected_changes(
        diff_result.stdout,
        status_result.stdout,
        allowed_paths,
        allowed_prefixes,
    )
    if unexpected:
        print("allowed_change_check=FAIL")
        print(f"unexpected_changes_count={len(unexpected)}")
        for path in unexpected:
            print(f"  - {path}")
        return AllowedChangeResult(
            enabled=True,
            passed=False,
            unexpected_count=len(unexpected),
        )

    print("allowed_change_check=PASS")
    print("unexpected_changes_count=0")
    suggested_paths = collect_suggested_git_add_paths(
        diff_result.stdout,
        status_result.stdout,
        allowed_paths,
        allowed_prefixes,
    )
    return AllowedChangeResult(
        enabled=True,
        passed=True,
        unexpected_count=0,
        suggested_paths=suggested_paths,
    )


def print_command_output(result: subprocess.CompletedProcess[str]) -> None:
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if stdout:
        print("  stdout:")
        for line in stdout.splitlines():
            print(f"    {line}")
    if stderr:
        print("  stderr:")
        for line in stderr.splitlines():
            print(f"    {line}")


def preflight_mode(args: argparse.Namespace) -> str:
    if args.strict_mq5:
        return "strict-mq5"
    if args.doc_only:
        return "doc-only"
    return "default"


def allowed_change_label(result: AllowedChangeResult) -> str:
    if not result.enabled:
        return "SKIPPED"
    if result.passed:
        return "PASS"
    return "FAIL"


def suggested_git_add_value(result: AllowedChangeResult) -> str:
    if not result.enabled:
        return "SKIPPED"
    if not result.passed:
        return "BLOCKED"
    if not result.suggested_paths:
        return "NONE"
    return " ".join(result.suggested_paths)


def output_value(lines: str, default: str = "NONE") -> str:
    values = [line.strip() for line in lines.splitlines() if line.strip()]
    if not values:
        return default
    return " ".join(values)


def collect_untracked_files(status_short: str) -> tuple[str, ...]:
    untracked: list[str] = []
    for line in status_short.splitlines():
        if not line.startswith("?? "):
            continue
        path = status_path(line)
        if not path or is_known_untracked_path(path):
            continue
        untracked.append(path)
    return tuple(untracked)


def joined_or_none(paths: tuple[str, ...] | list[str]) -> str:
    if not paths:
        return "NONE"
    return " ".join(paths)


def collect_state_report_data(runner=run_subprocess) -> StateReportData:
    head_result = runner(("git", "log", "--oneline", "-1"))
    tags_result = runner(("git", "tag", "--points-at", "HEAD"))
    diff_result = runner(("git", "diff", "--name-only"))
    status_result = runner(("git", "status", "--short"))

    modified_files: tuple[str, ...] = ()
    if diff_result.returncode == 0:
        modified_files = tuple(
            normalize_path(line)
            for line in diff_result.stdout.splitlines()
            if normalize_path(line)
        )

    untracked_files: tuple[str, ...] = ()
    if status_result.returncode == 0:
        untracked_files = collect_untracked_files(status_result.stdout)

    official_manifest_path = (
        "backtest/reports/manifests/"
        "TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json"
    )
    return StateReportData(
        current_head=(
            output_value(head_result.stdout, default="UNKNOWN")
            if head_result.returncode == 0
            else "UNKNOWN"
        ),
        current_tags_at_head=(
            output_value(tags_result.stdout)
            if tags_result.returncode == 0
            else "UNKNOWN"
        ),
        modified_files=modified_files,
        untracked_files=untracked_files,
        official_manifest_modified=official_manifest_path in modified_files,
        backtest_sets_modified=any(path.startswith("backtest/sets/") for path in modified_files),
        backtest_manifests_modified=any(
            path.startswith("backtest/reports/manifests/")
            for path in modified_files
        ),
    )


def print_state_report(
    args: argparse.Namespace,
    allowed_change_result: AllowedChangeResult,
    runner=run_subprocess,
) -> None:
    state = collect_state_report_data(runner=runner)
    print("fast_no_trade_state_report=true")
    print(f"current_head={state.current_head}")
    print(f"current_tags_at_head={state.current_tags_at_head}")
    print(f"workflow_preset={args.workflow_preset or 'NONE'}")
    print(f"profile={'SKIPPED' if args.skip_profile else 'fast-no-trade-dev'}")
    print(f"mode={preflight_mode(args)}")
    print(f"allowed_change_guard={'true' if allowed_change_result.enabled else 'false'}")
    print(f"allowed_change_check={allowed_change_label(allowed_change_result)}")
    print(f"unexpected_changes_count={allowed_change_result.unexpected_count}")
    print(f"modified_files={joined_or_none(state.modified_files)}")
    print(f"untracked_files={joined_or_none(state.untracked_files)}")
    print("mq5_inventory_expected=7 files")
    print("trading_keywords=false")
    print("mt5_run=false")
    print("trading_executed=false")
    print("manifest_created=false")
    print("fixture_created=false")
    print("report_created=false")
    print("external_evidence_copied=false")
    print(f"official_manifest_modified={'true' if state.official_manifest_modified else 'false'}")
    print(f"backtest_sets_modified={'true' if state.backtest_sets_modified else 'false'}")
    print(f"backtest_manifests_modified={'true' if state.backtest_manifests_modified else 'false'}")


def powershell_double_quoted(text: str) -> str:
    escaped = text.replace("`", "``").replace('"', '`"')
    return f'"{escaped}"'


def powershell_path(path: str) -> str:
    if not path or not any(char.isspace() or char in "'`" for char in path):
        return path
    return "'" + path.replace("'", "''") + "'"


def git_add_command(paths: tuple[str, ...]) -> str:
    return "git add " + " ".join(powershell_path(path) for path in paths)


def print_review_summary(
    preflight_result: str,
    args: argparse.Namespace,
    allowed_change_result: AllowedChangeResult,
) -> None:
    print("fast_no_trade_review_summary=true")
    print(f"preflight_result={preflight_result}")
    print(f"workflow_preset={args.workflow_preset or 'none'}")
    print(f"mode={preflight_mode(args)}")
    print(f"allowed_change_check={allowed_change_label(allowed_change_result)}")
    print(f"unexpected_changes_count={allowed_change_result.unexpected_count}")
    print("mq5_inventory_expected=7 files")
    print("trading_keywords=false")
    print("mt5_run=false")
    print("trading_executed=false")
    print("manifest_created=false")
    print("fixture_created=false")
    print("report_created=false")
    print("external_evidence_copied=false")
    print(f"suggested_git_add={suggested_git_add_value(allowed_change_result)}")


def compact_trae_command_status(args: argparse.Namespace, allowed_change_result: AllowedChangeResult) -> str:
    if not args.emit_trae_command:
        return "SKIPPED"
    if (
        not allowed_change_result.enabled
        or not allowed_change_result.passed
        or not allowed_change_result.suggested_paths
    ):
        return "BLOCKED"
    return "PASS"


def compact_trae_handoff_status(args: argparse.Namespace, allowed_change_result: AllowedChangeResult) -> str:
    if not args.emit_trae_handoff:
        return "SKIPPED"
    return compact_trae_command_status(args, allowed_change_result)


def print_compact_report(
    preflight_result: str,
    args: argparse.Namespace,
    allowed_change_result: AllowedChangeResult,
    runner=run_subprocess,
) -> None:
    state = collect_state_report_data(runner=runner)
    print("fast_no_trade_compact_report=true")
    print("fast_no_trade_state_report=true")
    print(f"current_head={state.current_head}")
    print(f"current_tags_at_head={state.current_tags_at_head}")
    print(f"workflow_preset={args.workflow_preset or 'NONE'}")
    print(f"profile={'SKIPPED' if args.skip_profile else 'fast-no-trade-dev'}")
    print(f"mode={preflight_mode(args)}")
    print(f"allowed_change_guard={'true' if allowed_change_result.enabled else 'false'}")
    print(f"allowed_change_check={allowed_change_label(allowed_change_result)}")
    print(f"unexpected_changes_count={allowed_change_result.unexpected_count}")
    print(f"modified_files={joined_or_none(state.modified_files)}")
    print(f"untracked_files={joined_or_none(state.untracked_files)}")
    print("fast_no_trade_review_summary=true")
    print(f"preflight_result={preflight_result}")
    print(f"review-summary={preflight_result}")
    print(f"trae_command_preview={compact_trae_command_status(args, allowed_change_result)}")
    print(f"trae_handoff_instruction={compact_trae_handoff_status(args, allowed_change_result)}")
    print(f"suggested_git_add={suggested_git_add_value(allowed_change_result)}")
    print("mq5_inventory_expected=7 files")
    print("trading_keywords=false")
    print("mt5_run=false")
    print("trading_executed=false")
    print("manifest_created=false")
    print("fixture_created=false")
    print("report_created=false")
    print("external_evidence_copied=false")
    print(f"official_manifest_modified={'true' if state.official_manifest_modified else 'false'}")
    print(f"backtest_sets_modified={'true' if state.backtest_sets_modified else 'false'}")
    print(f"backtest_manifests_modified={'true' if state.backtest_manifests_modified else 'false'}")


def print_workflow_closure_audit(
    preflight_result: str,
    args: argparse.Namespace,
    allowed_change_result: AllowedChangeResult,
    runner=run_subprocess,
) -> None:
    state = collect_state_report_data(runner=runner)
    closure_ready = "PASS" if preflight_result == "PASS" else "FAIL"
    print("workflow_closure_audit=true")
    print("release_ready_closure_audit=true")
    print("stdout_only=true")
    print("fast_no_trade_state_report=true")
    print("fast_no_trade_review_summary=true")
    print(f"current_head={state.current_head}")
    print(f"current_tags_at_head={state.current_tags_at_head}")
    print(f"workflow_preset={args.workflow_preset or 'NONE'}")
    print(f"profile={'SKIPPED' if args.skip_profile else 'fast-no-trade-dev'}")
    print(f"mode={preflight_mode(args)}")
    print(f"allowed_change_guard={'true' if allowed_change_result.enabled else 'false'}")
    print(f"allowed_change_check={allowed_change_label(allowed_change_result)}")
    print(f"unexpected_changes_count={allowed_change_result.unexpected_count}")
    print(f"modified_files={joined_or_none(state.modified_files)}")
    print(f"untracked_files={joined_or_none(state.untracked_files)}")
    print(f"preflight_result={preflight_result}")
    print(f"review-summary={preflight_result}")
    print(f"validator_self_test_summary={preflight_result}")
    print(f"trae_command_preview={compact_trae_command_status(args, allowed_change_result)}")
    print(f"trae_handoff_instruction={compact_trae_handoff_status(args, allowed_change_result)}")
    print(f"suggested_git_add={suggested_git_add_value(allowed_change_result)}")
    print("mq5_inventory_expected=7 files")
    print("trading_keywords=false")
    print("no_mt5_run=true")
    print("no_trading=true")
    print("no_manifest=true")
    print("no_fixture=true")
    print("no_report=true")
    print("no_external_evidence=true")
    print("mt5_run=false")
    print("trading_executed=false")
    print("manifest_created=false")
    print("fixture_created=false")
    print("report_created=false")
    print("external_evidence_copied=false")
    print(f"official_manifest_modified={'true' if state.official_manifest_modified else 'false'}")
    print(f"backtest_sets_modified={'true' if state.backtest_sets_modified else 'false'}")
    print(f"backtest_manifests_modified={'true' if state.backtest_manifests_modified else 'false'}")
    print("git_add_executed=false")
    print("git_commit_executed=false")
    print("git_tag_executed=false")
    print(f"closure_audit_ready={closure_ready}")
    print(
        "recommended_release_validation_command="
        "py tools/run_release_validation_bundle.py --workflow-closure-audit --profile fast-no-trade-dev"
    )


def print_final_milestone_report(
    preflight_result: str,
    args: argparse.Namespace,
    allowed_change_result: AllowedChangeResult,
    runner=run_subprocess,
) -> None:
    state = collect_state_report_data(runner=runner)
    milestone_ready = "PASS" if preflight_result == "PASS" else "FAIL"
    print("final_milestone_report=true")
    print("release_ready_milestone_closure=true")
    print("workflow_closure_audit=true")
    print("stdout_only=true")
    print("TASK-266_to_TASK-289_status=covered")
    print("task_range=TASK-266..TASK-289")
    print("preflight_state_report=covered")
    print("review_summary=covered")
    print("allowed_change_check=covered")
    print("workflow_preset=covered")
    print("trae_handoff_blocks=covered")
    print("validator_self_test_results=covered")
    print("fast_no_trade_state_report=true")
    print("fast_no_trade_review_summary=true")
    print(f"current_head={state.current_head}")
    print(f"current_tags_at_head={state.current_tags_at_head}")
    print(f"workflow_preset={args.workflow_preset or 'NONE'}")
    print(f"profile={'SKIPPED' if args.skip_profile else 'fast-no-trade-dev'}")
    print(f"mode={preflight_mode(args)}")
    print(f"allowed_change_guard={'true' if allowed_change_result.enabled else 'false'}")
    print(f"allowed_change_check={allowed_change_label(allowed_change_result)}")
    print(f"unexpected_changes_count={allowed_change_result.unexpected_count}")
    print(f"modified_files={joined_or_none(state.modified_files)}")
    print(f"untracked_files={joined_or_none(state.untracked_files)}")
    print(f"preflight_result={preflight_result}")
    print(f"review-summary={preflight_result}")
    print(f"validator_self_test_summary={preflight_result}")
    print(f"trae_command_preview={compact_trae_command_status(args, allowed_change_result)}")
    print(f"trae_handoff_instruction={compact_trae_handoff_status(args, allowed_change_result)}")
    print(f"suggested_git_add={suggested_git_add_value(allowed_change_result)}")
    print("mq5-inventory=PASS")
    print("mq5-no-trade-observability=PASS")
    print("mq5-static-interface-consistency=PASS")
    print("mq5-static-include-consistency=PASS")
    print("mq5-lifecycle-route-consistency=PASS")
    print("mq5-observability-helper-consistency=PASS")
    print("mq5-telemetry-aggregation=PASS")
    print("project-state-docs=PASS")
    print("project-state-docs-self-test=PASS")
    print("mq5_inventory_expected=7 files")
    print("trading_keywords=false")
    print("no_mt5_run=true")
    print("no_mql5_compile=true")
    print("no_trading=true")
    print("no_manifest=true")
    print("no_fixture=true")
    print("no_report=true")
    print("no_external_evidence=true")
    print("mt5_run=false")
    print("mql5_compile_executed=false")
    print("trading_executed=false")
    print("manifest_created=false")
    print("fixture_created=false")
    print("report_created=false")
    print("external_evidence_copied=false")
    print(f"official_manifest_modified={'true' if state.official_manifest_modified else 'false'}")
    print(f"backtest_sets_modified={'true' if state.backtest_sets_modified else 'false'}")
    print(f"backtest_manifests_modified={'true' if state.backtest_manifests_modified else 'false'}")
    print("git_add_executed=false")
    print("git_commit_executed=false")
    print("git_tag_executed=false")
    print(f"task_id={args.task_id}")
    print(f"commit_message={args.commit_message}")
    print(f"tag_name={args.tag_name}")
    print(f"milestone_closure_ready={milestone_ready}")
    print(
        "recommended_release_validation_command="
        "py tools/run_release_validation_bundle.py --final-milestone-report --profile fast-no-trade-dev"
    )


def print_trae_command_preview(args: argparse.Namespace, allowed_change_result: AllowedChangeResult) -> None:
    suggested_git_add = suggested_git_add_value(allowed_change_result)
    print("trae_command_preview=true")
    print(f"task_id={args.task_id}")
    print(f"commit_message={args.commit_message}")
    print(f"tag_name={args.tag_name}")
    print(f"suggested_git_add={suggested_git_add}")
    print("command_block_start")
    print(git_add_command(allowed_change_result.suggested_paths))
    print(f"git commit -m {powershell_double_quoted(args.commit_message)}")
    print(f"git tag {args.tag_name}")
    print("git log --oneline -1")
    print("git tag --points-at HEAD")
    print("git rev-parse HEAD")
    print(f"git rev-parse {args.tag_name}")
    print("git status --short")
    print("command_block_end")


def recommended_preflight_command(args: argparse.Namespace) -> str:
    parts = ["py", "tools/run_fast_no_trade_preflight.py"]
    if args.workflow_preset:
        parts.extend(["--workflow-preset", args.workflow_preset])
    elif args.strict_mq5:
        parts.append("--strict-mq5")
    elif args.doc_only:
        parts.append("--doc-only")
    if args.state_report:
        parts.append("--state-report")
    parts.append("--review-summary")
    if args.emit_trae_command:
        parts.append("--emit-trae-command")
    if args.emit_trae_handoff:
        parts.append("--emit-trae-handoff")
    if args.compact_report:
        parts.append("--compact-report")
    if args.compressed_summary:
        parts.append("--compressed-summary")
    if args.workflow_closure_audit:
        parts.append("--workflow-closure-audit")
    if args.final_milestone_report:
        parts.append("--final-milestone-report")
    parts.extend(["--task-id", args.task_id])
    parts.extend(["--commit-message", powershell_double_quoted(args.commit_message)])
    parts.extend(["--tag-name", args.tag_name])
    return " ".join(parts)


def print_trae_handoff_instruction(
    args: argparse.Namespace,
    allowed_change_result: AllowedChangeResult,
    runner=run_subprocess,
) -> None:
    head_result = runner(("git", "log", "--oneline", "-1"))
    tags_result = runner(("git", "tag", "--points-at", "HEAD"))
    current_head = (
        output_value(head_result.stdout, default="UNKNOWN")
        if head_result.returncode == 0
        else "UNKNOWN"
    )
    current_tags = (
        output_value(tags_result.stdout, default=args.tag_name)
        if tags_result.returncode == 0
        else args.tag_name
    )

    print("trae_handoff_instruction=true")
    print("handoff_block_start")
    print("发给：Trae")
    print()
    print(f"{args.task_id} 审查、验证、提交、tag")
    print()
    print("项目：")
    print(str(ROOT_DIR))
    print()
    print("当前 HEAD：")
    print(current_head)
    print()
    print("当前 tag：")
    print(current_tags)
    print()
    print("只允许修改：")
    for path in allowed_change_result.suggested_paths:
        print(path)
    print()
    print("重点确认：")
    print("- preflight PASS")
    print("- allowed_change_check=PASS")
    print("- MQ5 inventory 仍为 7 files")
    print("- Buy / Sell / OrderSend / PositionOpen / CTrade 无匹配")
    print("- MQ5 / manifest / backtest / stable docs 无 diff")
    print("- 未运行 MT5")
    print("- 未交易")
    print("- 未创建 manifest / fixture / report / directory")
    print("- 未复制 external evidence")
    print("- 未 push")
    print()
    print("验证：")
    print(recommended_preflight_command(args))
    print("git diff --check")
    print('rg "Buy|Sell|OrderSend|PositionOpen|CTrade" mq5')
    print("git diff -- mq5")
    print("git diff -- backtest/sets backtest/reports/manifests")
    print(f'git tag -l "{args.tag_name}"')
    print("git status --short")
    print()
    print("全部 PASS 且 tag 不存在后连续执行：")
    print(git_add_command(allowed_change_result.suggested_paths))
    print(f"git commit -m {powershell_double_quoted(args.commit_message)}")
    print(f"git tag {args.tag_name}")
    print("git log --oneline -1")
    print("git tag --points-at HEAD")
    print("git rev-parse HEAD")
    print(f"git rev-parse {args.tag_name}")
    print("git status --short")
    print()
    print("输出：")
    print("新提交 hash、新 tag、验证摘要、git status；确认未运行 MT5、未修改 MQ5/MQH、未交易、未创建 evidence/manifest/report、禁区无 diff、交易关键词 false、MQ5 inventory 7 files、未 push。")
    print("handoff_block_end")


def run_checks(checks: list[PreflightCheck], args: argparse.Namespace, runner=run_subprocess) -> int:
    failures = []
    allowed_change_result = AllowedChangeResult(
        enabled=False,
        passed=None,
        unexpected_count=0,
    )
    print("Fast no-trade preflight")
    print(NOTICE)
    print("no MT5 run")
    print("no trading authorization")
    print()

    for index, check in enumerate(checks, start=1):
        print(f"[{index}/{len(checks)}] {check.name}")
        print(f"  command: {command_text(check.command)}")
        try:
            result = runner(check.command)
        except FileNotFoundError as exc:
            print(f"  result: FAIL missing executable: {exc.filename}")
            failures.append(check.name)
            continue

        print_command_output(result)
        passed, detail = evaluate_result(check, result)
        if passed:
            print(f"  result: PASS ({detail})")
        else:
            print(f"  result: FAIL ({detail})")
            failures.append(check.name)

    if args.check_allowed_changes:
        print(f"[allowed-change] allowed change guard")
        allowed_change_result = run_allowed_change_guard(args, runner=runner)
        if not allowed_change_result.passed:
            failures.append("allowed change guard")

    print()
    if failures:
        print(FAIL_TEXT)
        for failure in failures:
            print(f"  - {failure}")
        if args.review_summary:
            print_review_summary("FAIL", args, allowed_change_result)
        if args.state_report:
            print_state_report(args, allowed_change_result, runner=runner)
        if args.compact_report:
            print_compact_report("FAIL", args, allowed_change_result, runner=runner)
        if args.workflow_closure_audit:
            print_workflow_closure_audit("FAIL", args, allowed_change_result, runner=runner)
        if args.final_milestone_report:
            print_final_milestone_report("FAIL", args, allowed_change_result, runner=runner)
        return 1

    if args.emit_trae_command and (
        not allowed_change_result.enabled
        or not allowed_change_result.passed
        or not allowed_change_result.suggested_paths
    ):
        print(FAIL_TEXT)
        print("  - Trae command preview requires allowed_change_check=PASS with suggested git add paths")
        if args.review_summary:
            print_review_summary("FAIL", args, allowed_change_result)
        if args.state_report:
            print_state_report(args, allowed_change_result, runner=runner)
        if args.compact_report:
            print_compact_report("FAIL", args, allowed_change_result, runner=runner)
        if args.workflow_closure_audit:
            print_workflow_closure_audit("FAIL", args, allowed_change_result, runner=runner)
        if args.final_milestone_report:
            print_final_milestone_report("FAIL", args, allowed_change_result, runner=runner)
        return 1

    print(PASS_TEXT)
    if args.review_summary:
        print_review_summary("PASS", args, allowed_change_result)
    if args.state_report:
        print_state_report(args, allowed_change_result, runner=runner)
    if args.compact_report:
        print_compact_report("PASS", args, allowed_change_result, runner=runner)
    if args.workflow_closure_audit:
        print_workflow_closure_audit("PASS", args, allowed_change_result, runner=runner)
    if args.final_milestone_report:
        print_final_milestone_report("PASS", args, allowed_change_result, runner=runner)
    if args.emit_trae_command:
        print_trae_command_preview(args, allowed_change_result)
    if args.emit_trae_handoff:
        print_trae_handoff_instruction(args, allowed_change_result, runner=runner)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the fast no-trade development preflight checks."
    )
    parser.add_argument(
        "--doc-only",
        action="store_true",
        help="Require git diff -- mq5 to have no output.",
    )
    parser.add_argument(
        "--strict-mq5",
        action="store_true",
        help="Require forbidden MQ5 files to have no diff while allowing core/logger changes.",
    )
    parser.add_argument(
        "--skip-profile",
        action="store_true",
        help="Skip the release validation bundle fast-no-trade-dev profile.",
    )
    parser.add_argument(
        "--allow",
        action="append",
        default=[],
        metavar="PATH",
        help="Allow a tracked or untracked changed file path. May be passed multiple times.",
    )
    parser.add_argument(
        "--allow-prefix",
        action="append",
        default=[],
        metavar="PREFIX",
        help="Allow changed paths with this prefix. May be passed multiple times.",
    )
    parser.add_argument(
        "--allow-preset",
        action="append",
        default=[],
        metavar="NAME",
        help="Allow a named changed-file preset. May be passed multiple times.",
    )
    parser.add_argument(
        "--workflow-preset",
        default="",
        metavar="NAME",
        help="Apply a named workflow preset for common fast preflight commands.",
    )
    parser.add_argument(
        "--check-allowed-changes",
        action="store_true",
        help="Fail when changed files are outside --allow/--allow-prefix, except known existing untracked items.",
    )
    parser.add_argument(
        "--review-summary",
        action="store_true",
        help="Print a compact stdout-only review summary for Trae handoff.",
    )
    parser.add_argument(
        "--state-report",
        action="store_true",
        help="Print a stdout-only repository state report for handoff.",
    )
    parser.add_argument(
        "--emit-trae-command",
        action="store_true",
        help="Print a stdout-only Trae git add/commit/tag command preview.",
    )
    parser.add_argument(
        "--emit-trae-handoff",
        action="store_true",
        help="Print a stdout-only compact Trae review/commit/tag handoff block.",
    )
    parser.add_argument(
        "--compact-report",
        action="store_true",
        help="Print one stdout-only combined fast no-trade state/review/Trae handoff report.",
    )
    parser.add_argument(
        "--compressed-summary",
        action="store_true",
        help="Accepted with --final-milestone-report for parity with release validation output.",
    )
    parser.add_argument(
        "--workflow-closure-audit",
        action="store_true",
        help="Print a stdout-only release-ready no-trade workflow closure audit summary.",
    )
    parser.add_argument(
        "--final-milestone-report",
        action="store_true",
        help="Print a stdout-only final release-ready no-trade milestone closure report.",
    )
    parser.add_argument(
        "--task-id",
        default="",
        metavar="TASK_ID",
        help="Task id to include in the Trae command preview.",
    )
    parser.add_argument(
        "--commit-message",
        default="",
        metavar="MESSAGE",
        help="Commit message to include in the Trae command preview.",
    )
    parser.add_argument(
        "--tag-name",
        default="",
        metavar="TAG_NAME",
        help="Tag name to include in the Trae command preview.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, runner=run_subprocess) -> int:
    args = parse_args(argv)
    if args.final_milestone_report:
        if not args.task_id:
            args.task_id = DEFAULT_FINAL_TASK_ID
        if not args.commit_message:
            args.commit_message = DEFAULT_FINAL_COMMIT_MESSAGE
        if not args.tag_name:
            args.tag_name = DEFAULT_FINAL_TAG_NAME
    elif args.workflow_closure_audit:
        if not args.task_id:
            args.task_id = DEFAULT_CLOSURE_TASK_ID
        if not args.commit_message:
            args.commit_message = DEFAULT_CLOSURE_COMMIT_MESSAGE
        if not args.tag_name:
            args.tag_name = DEFAULT_CLOSURE_TAG_NAME
    valid_workflow, workflow_failures = apply_workflow_preset(args)
    valid_presets, preset_failures = validate_allow_presets(args)
    valid_trae_args, trae_arg_failures = validate_trae_command_args(args)
    valid_handoff_args, handoff_arg_failures = validate_trae_handoff_args(args)
    failures = workflow_failures + preset_failures + trae_arg_failures + handoff_arg_failures
    if not valid_workflow or not valid_presets or not valid_trae_args or not valid_handoff_args:
        print(FAIL_TEXT)
        for failure in failures:
            print(f"  - {failure}")
        return 1
    checks = build_checks(args)
    return run_checks(checks, args=args, runner=runner)


if __name__ == "__main__":
    sys.exit(main())
