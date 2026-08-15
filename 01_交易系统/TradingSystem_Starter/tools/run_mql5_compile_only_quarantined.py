#!/usr/bin/env python3
"""Run a controlled quarantined MQL5 compile-only attempt.

Default mode is a dry-run plan. Passing --execute performs the compile-only
attempt against a temporary copy outside the repository, then deletes the
quarantine directory and verifies no repository artifacts were created.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import fnmatch
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime


ROOT_DIR = Path(__file__).resolve().parents[1]
SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."
TRADING_KEYWORDS = ("Buy", "Sell", "OrderSend", "PositionOpen", "CTrade")
REQUIRED_BOUNDARY_DOCS = (
    "V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md",
    "V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md",
    "V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md",
    "V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md",
    "V060_TASK_298_MQL5_COMPILE_ONLY_DRYRUN.md",
    "V060_TASK_301_V060_COMPILE_READINESS_PLANNING.md",
    "V060_TASK_302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE.md",
    "V060_TASK_303_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN.md",
)
COMPILE_LOG_PATTERNS = (
    "*.log",
    "*compile*.txt",
    "*compile*.log",
    "MetaEditor*.log",
    "mql5_compile*.log",
    "mql5_compile*.txt",
)
ALLOWED_LOG_PATTERNS = (
    "backtest/reports/samples/TASK-012_runtime_summary_sample.log",
    "logs/localhost-3000.debug.log",
    "logs/localhost-3000.err.log",
    "logs/localhost-3000.out.log",
)
DEFAULT_METAEDITOR_PATH = Path(r"C:\Program Files\MetaTrader 5\metaeditor64.exe")


@dataclass
class PreflightState:
    issues: list[str]
    mq5_inventory_files: int
    trading_keywords_found: bool
    repo_ex5_artifacts: bool
    repo_compile_logs: bool
    metaeditor_candidate: Path | None


@dataclass
class AttemptResult:
    exit_code: int
    compile_exit_code: int | None
    metaeditor_executed: bool
    mql5_compile_executed: bool
    compile_target_is_quarantine_copy: bool
    quarantine_outside_repo: bool
    quarantine_deleted: bool
    repo_mq5_modified: bool
    repo_ex5_artifacts: bool
    repo_compile_logs: bool
    trading_keywords_found: bool
    mq5_inventory_files: int
    issues: list[str]
    quarantine_dir: Path | None = None
    diagnostic_capture: bool = False
    compile_success: bool = False
    compile_failure_diagnosed: bool = False
    compile_log_captured: bool = False
    compile_log_excerpt: str = ""
    compile_log_stdout_only: bool = True
    compile_log_saved_to_repo: bool = False
    compile_log_errors: int | str = "UNKNOWN"
    compile_log_warnings: int | str = "UNKNOWN"
    compile_log_semantic_success: bool | str = "unknown"
    compile_result_classification: str = "unclassified"
    metaeditor_exit_code_anomaly: bool = False
    task304_success_result_created: bool = False
    followup_required: bool = False
    quarantine_ex5_artifact_detected: bool = False
    quarantine_ex5_artifact_count: int = 0
    quarantine_compile_log_detected: bool = False
    quarantine_compile_log_captured: bool = False
    artifact_hash_capture: bool = False
    artifact_hash_captured: bool = False
    artifact_hash_stdout_only: bool = True
    artifact_hash_saved_to_repo: bool = False
    quarantine_ex5_artifact_sha256: str = "NONE"
    quarantine_ex5_artifact_size_bytes: int = 0
    success_reclassification_attempt: bool = False
    success_reclassification_attempted: bool = False
    success_reclassification_decision: str = "NONE"
    compile_only_reclassified_success: bool = False
    compile_success_scope: str = "NONE"
    trading_authorization: bool = False
    deployment_readiness: bool = False
    backtest_readiness: bool = False
    strategy_readiness: bool = False
    success_reclassification_done: bool = False


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def relative_posix(root_dir: Path, path: Path) -> str:
    return path.relative_to(root_dir).as_posix()


def mq5_source_files(root_dir: Path) -> list[Path]:
    mq5_root = root_dir / "mq5"
    if not mq5_root.exists():
        return []
    return sorted(
        path
        for path in mq5_root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".mq5", ".mqh"}
    )


def path_is_inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def is_allowed_existing_log(rel_path: str) -> bool:
    return any(fnmatch.fnmatchcase(rel_path, pattern) for pattern in ALLOWED_LOG_PATTERNS)


def is_compile_log_candidate(path: Path) -> bool:
    return any(fnmatch.fnmatchcase(path.name, pattern) for pattern in COMPILE_LOG_PATTERNS)


def collect_mq5_inventory_issues(root_dir: Path) -> tuple[list[str], int, bool]:
    issues: list[str] = []
    files = mq5_source_files(root_dir)
    if len(files) != 7:
        issues.append(f"MQ5 inventory expected 7 files, found {len(files)}")

    trading_keyword_found = False
    for path in files:
        text = read_text(path)
        for keyword in TRADING_KEYWORDS:
            if keyword in text:
                issues.append(
                    f"{relative_posix(root_dir, path)} contains prohibited trading keyword: {keyword}"
                )
                trading_keyword_found = True
    return issues, len(files), trading_keyword_found


def collect_repo_artifact_issues(root_dir: Path) -> tuple[list[str], bool, bool]:
    issues: list[str] = []
    repo_ex5_artifacts = False
    repo_compile_logs = False

    for path in sorted(p for p in root_dir.rglob("*") if p.is_file()):
        rel_path = relative_posix(root_dir, path)
        if rel_path.startswith(".git/") or ".git/" in rel_path:
            continue
        if path.suffix.lower() == ".ex5":
            issues.append(f"repository contains prohibited .ex5 artifact: {rel_path}")
            repo_ex5_artifacts = True
            continue
        if is_compile_log_candidate(path) and not is_allowed_existing_log(rel_path):
            issues.append(f"repository contains prohibited compile log candidate: {rel_path}")
            repo_compile_logs = True
    return issues, repo_ex5_artifacts, repo_compile_logs


def collect_mq5_file_snapshot(root_dir: Path) -> dict[str, str]:
    mq5_root = root_dir / "mq5"
    snapshot: dict[str, str] = {}
    if not mq5_root.exists():
        return snapshot
    for path in sorted(p for p in mq5_root.rglob("*") if p.is_file()):
        snapshot[relative_posix(root_dir, path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def discover_metaeditor_candidate() -> Path | None:
    if DEFAULT_METAEDITOR_PATH.exists():
        return DEFAULT_METAEDITOR_PATH

    try:
        from validate_mql5_compile_only_command_discovery import (  # type: ignore
            discover_metaeditor_candidate as discover_from_task295,
        )
    except Exception:
        discover_from_task295 = None

    if discover_from_task295 is not None:
        candidate = discover_from_task295()
        if candidate:
            return Path(candidate)

    for executable in ("metaeditor64.exe", "metaeditor.exe"):
        found = shutil.which(executable)
        if found:
            return Path(found)
    return None


def is_allowed_metaeditor_path(path: Path) -> bool:
    name = path.name.lower()
    if name == "terminal64.exe":
        return False
    return name in {"metaeditor64.exe", "metaeditor.exe", "metaeditor.exe"}


def collect_boundary_issues(root_dir: Path) -> list[str]:
    issues: list[str] = []
    docs_root = root_dir / "docs"
    for name in REQUIRED_BOUNDARY_DOCS:
        if not (docs_root / name).exists():
            issues.append(f"missing required compile-only boundary doc: docs/{name}")
    return issues


def collect_preflight_state(
    root_dir: Path,
    *,
    metaeditor_path: Path | None = None,
) -> PreflightState:
    issues = collect_boundary_issues(root_dir)
    trading_system = root_dir / "mq5" / "TradingSystem.mq5"
    if not trading_system.exists():
        issues.append("missing compile target: mq5/TradingSystem.mq5")

    inventory_issues, inventory_count, trading_keywords_found = collect_mq5_inventory_issues(root_dir)
    artifact_issues, repo_ex5_artifacts, repo_compile_logs = collect_repo_artifact_issues(root_dir)
    issues.extend(inventory_issues)
    issues.extend(artifact_issues)

    candidate = metaeditor_path or discover_metaeditor_candidate()
    if candidate is None:
        issues.append("missing MetaEditor candidate")
    elif not candidate.exists():
        issues.append(f"MetaEditor candidate does not exist: {candidate}")
    elif not is_allowed_metaeditor_path(candidate):
        issues.append(f"MetaEditor candidate is not allowed: {candidate}")

    return PreflightState(
        issues=issues,
        mq5_inventory_files=inventory_count,
        trading_keywords_found=trading_keywords_found,
        repo_ex5_artifacts=repo_ex5_artifacts,
        repo_compile_logs=repo_compile_logs,
        metaeditor_candidate=candidate,
    )


def make_quarantine_dir(parent: Path) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    quarantine = parent / f"TradingSystem_Starter_TASK304_compile_quarantine_{stamp}"
    quarantine.mkdir(parents=True, exist_ok=False)
    return quarantine


def run_subprocess(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True)


def build_compile_command(metaeditor_path: Path, compile_target: Path, compile_log: Path) -> list[str]:
    return [
        str(metaeditor_path),
        f"/compile:{compile_target}",
        f"/log:{compile_log}",
    ]


def decode_compile_log_bytes(data: bytes) -> str:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")
    if b"\x00" in data[:200]:
        for encoding in ("utf-16-le", "utf-16-be"):
            decoded = data.decode(encoding, errors="replace")
            if "\x00" not in decoded[:200]:
                return decoded
    return data.decode("utf-8", errors="replace")


def read_compile_log_excerpt(
    compile_log: Path,
    *,
    max_lines: int = 200,
    max_chars: int = 20000,
) -> tuple[bool, str]:
    if not compile_log.exists() or not compile_log.is_file():
        return False, ""
    text = decode_compile_log_bytes(compile_log.read_bytes())
    lines = text.splitlines()
    excerpt = "\n".join(lines[:max_lines])
    if len(excerpt) > max_chars:
        excerpt = excerpt[:max_chars]
    return True, excerpt


def inspect_quarantine_artifacts(quarantine: Path, compile_log: Path) -> dict[str, object]:
    ex5_artifacts = sorted(
        path
        for path in quarantine.rglob("*")
        if path.is_file() and path.suffix.lower() == ".ex5"
    )
    compile_log_detected = compile_log.exists() and compile_log.is_file()
    sha256_values: list[str] = []
    total_size = 0
    for path in ex5_artifacts:
        data = path.read_bytes()
        sha256_values.append(hashlib.sha256(data).hexdigest())
        total_size += len(data)
    return {
        "quarantine_ex5_artifact_detected": bool(ex5_artifacts),
        "quarantine_ex5_artifact_count": len(ex5_artifacts),
        "quarantine_compile_log_detected": compile_log_detected,
        "artifact_hash_captured": bool(ex5_artifacts),
        "quarantine_ex5_artifact_sha256": ",".join(sha256_values) if sha256_values else "NONE",
        "quarantine_ex5_artifact_size_bytes": total_size,
    }


def stdout_safe_text(text: str, *, encoding: str | None = None) -> str:
    target_encoding = encoding or getattr(sys.stdout, "encoding", None) or "utf-8"
    return text.encode(target_encoding, errors="replace").decode(target_encoding, errors="replace")


def classify_compile_diagnostic_result(
    exit_code: int,
    compile_log_text: str,
    quarantine_ex5_artifact_detected: bool = False,
) -> dict[str, object]:
    match = re.search(r"Result:\s*(\d+)\s+errors?,\s*(\d+)\s+warnings?", compile_log_text, re.IGNORECASE)
    if match is None:
        match = re.search(r"\b(\d+)\s+errors?,\s*(\d+)\s+warnings?", compile_log_text, re.IGNORECASE)

    if match is None:
        return {
            "compile_log_errors": "UNKNOWN",
            "compile_log_warnings": "UNKNOWN",
            "compile_log_semantic_success": "unknown",
            "compile_result_classification": "unclassified",
            "metaeditor_exit_code_anomaly": False,
            "compile_success": False,
            "task304_success_result_created": False,
            "followup_required": True,
        }

    errors = int(match.group(1))
    warnings = int(match.group(2))
    semantic_success = errors == 0
    if errors > 0:
        classification = "compile_errors_present"
        compile_success = False
        followup_required = True
        anomaly = False
    elif exit_code != 0 and semantic_success:
        if quarantine_ex5_artifact_detected:
            classification = "compiled_artifact_with_metaeditor_exit_code_anomaly"
        else:
            classification = "metaeditor_exit_code_anomaly_without_artifact"
        compile_success = False
        followup_required = True
        anomaly = True
    elif exit_code == 0 and semantic_success:
        if quarantine_ex5_artifact_detected:
            classification = "compile_artifact_detected_exit_success"
        else:
            classification = "compile_log_success_exit_success"
        compile_success = True
        followup_required = False
        anomaly = False
    else:
        classification = "unclassified"
        compile_success = False
        followup_required = True
        anomaly = False

    return {
        "compile_log_errors": errors,
        "compile_log_warnings": warnings,
        "compile_log_semantic_success": semantic_success,
        "compile_result_classification": classification,
        "metaeditor_exit_code_anomaly": anomaly,
        "compile_success": compile_success,
        "task304_success_result_created": False,
        "followup_required": followup_required,
    }


def post_attempt_checks(
    root_dir: Path,
    *,
    mq5_snapshot_before: dict[str, str] | None = None,
) -> tuple[list[str], int, bool, bool, bool, bool]:
    issues: list[str] = []
    inventory_issues, inventory_count, trading_keywords_found = collect_mq5_inventory_issues(root_dir)
    artifact_issues, repo_ex5_artifacts, repo_compile_logs = collect_repo_artifact_issues(root_dir)
    repo_mq5_modified = False
    if mq5_snapshot_before is not None:
        repo_mq5_modified = collect_mq5_file_snapshot(root_dir) != mq5_snapshot_before
    if repo_mq5_modified:
        issues.append("MQ5 file snapshot changed during quarantined compile-only attempt")
    issues.extend(inventory_issues)
    issues.extend(artifact_issues)
    return (
        issues,
        inventory_count,
        trading_keywords_found,
        repo_ex5_artifacts,
        repo_compile_logs,
        repo_mq5_modified,
    )


def execute_attempt(
    root_dir: Path,
    *,
    quarantine_parent: Path,
    metaeditor_path: Path | None = None,
    runner=run_subprocess,
    diagnostic_capture: bool = False,
    artifact_hash_capture: bool = False,
    success_reclassification_attempt: bool = False,
    remove_tree=shutil.rmtree,
) -> AttemptResult:
    preflight = collect_preflight_state(root_dir, metaeditor_path=metaeditor_path)
    issues = list(preflight.issues)
    mq5_snapshot_before = collect_mq5_file_snapshot(root_dir)
    if issues:
        return AttemptResult(
            exit_code=1,
            compile_exit_code=None,
            metaeditor_executed=False,
            mql5_compile_executed=False,
            compile_target_is_quarantine_copy=False,
            quarantine_outside_repo=False,
            quarantine_deleted=True,
            repo_mq5_modified=False,
            repo_ex5_artifacts=preflight.repo_ex5_artifacts,
            repo_compile_logs=preflight.repo_compile_logs,
            trading_keywords_found=preflight.trading_keywords_found,
            mq5_inventory_files=preflight.mq5_inventory_files,
            issues=issues,
            diagnostic_capture=diagnostic_capture,
            artifact_hash_capture=artifact_hash_capture,
            success_reclassification_attempt=success_reclassification_attempt,
        )

    quarantine = make_quarantine_dir(quarantine_parent.resolve())
    quarantine_outside_repo = not path_is_inside(quarantine, root_dir)
    if not quarantine_outside_repo:
        shutil.rmtree(quarantine, ignore_errors=True)
        return AttemptResult(
            exit_code=1,
            compile_exit_code=None,
            metaeditor_executed=False,
            mql5_compile_executed=False,
            compile_target_is_quarantine_copy=False,
            quarantine_outside_repo=False,
            quarantine_deleted=not quarantine.exists(),
            repo_mq5_modified=collect_mq5_file_snapshot(root_dir) != mq5_snapshot_before,
            repo_ex5_artifacts=preflight.repo_ex5_artifacts,
            repo_compile_logs=preflight.repo_compile_logs,
            trading_keywords_found=preflight.trading_keywords_found,
            mq5_inventory_files=preflight.mq5_inventory_files,
            issues=["quarantine directory must be outside repository"],
            quarantine_dir=quarantine,
            diagnostic_capture=diagnostic_capture,
            artifact_hash_capture=artifact_hash_capture,
            success_reclassification_attempt=success_reclassification_attempt,
        )

    compile_exit_code: int | None = None
    metaeditor_executed = False
    mql5_compile_executed = False
    compile_target_is_quarantine_copy = False
    cleanup_issue = ""
    compile_log_captured = False
    compile_log_excerpt = ""
    classification = classify_compile_diagnostic_result(-1, "")
    quarantine_artifacts = {
        "quarantine_ex5_artifact_detected": False,
        "quarantine_ex5_artifact_count": 0,
        "quarantine_compile_log_detected": False,
        "artifact_hash_captured": False,
        "quarantine_ex5_artifact_sha256": "NONE",
        "quarantine_ex5_artifact_size_bytes": 0,
    }

    try:
        shutil.copytree(root_dir / "mq5", quarantine / "mq5")
        compile_target = quarantine / "mq5" / "TradingSystem.mq5"
        compile_log = quarantine / "compile.log"
        compile_target_is_quarantine_copy = (
            compile_target.exists()
            and path_is_inside(compile_target, quarantine)
            and not path_is_inside(compile_target, root_dir)
        )
        command = build_compile_command(preflight.metaeditor_candidate or Path(), compile_target, compile_log)
        metaeditor_executed = True
        mql5_compile_executed = True
        completed = runner(command)
        compile_exit_code = completed.returncode
        if diagnostic_capture:
            compile_log_captured, compile_log_excerpt = read_compile_log_excerpt(compile_log)
            quarantine_artifacts = inspect_quarantine_artifacts(quarantine, compile_log)
            classification = classify_compile_diagnostic_result(
                compile_exit_code,
                compile_log_excerpt,
                bool(quarantine_artifacts["quarantine_ex5_artifact_detected"]),
            )
            if artifact_hash_capture:
                if not quarantine_artifacts["artifact_hash_captured"]:
                    issues.append("artifact hash capture requested but no quarantine .ex5 artifact was found")
                elif (
                    compile_exit_code != 0
                    and classification["compile_log_semantic_success"] is True
                    and quarantine_artifacts["quarantine_ex5_artifact_detected"]
                ):
                    classification = {
                        **classification,
                        "compile_result_classification": (
                            "artifact_hash_captured_with_metaeditor_exit_code_anomaly"
                        ),
                        "compile_success": False,
                        "task304_success_result_created": False,
                        "followup_required": True,
                    }
                else:
                    classification = {
                        **classification,
                        "compile_result_classification": (
                            "artifact_hash_captured_no_success_reclassification"
                        ),
                        "compile_success": False,
                        "task304_success_result_created": False,
                        "followup_required": True,
                    }
            if not compile_log_captured:
                issues.append("diagnostic compile log was not captured")
        elif compile_exit_code != 0:
            issues.append(f"MetaEditor compile-only command failed with exit code {compile_exit_code}")
    finally:
        try:
            remove_tree(quarantine)
        except Exception as exc:
            cleanup_issue = f"failed to delete quarantine directory: {exc}"

    quarantine_deleted = not quarantine.exists()
    if cleanup_issue:
        issues.append(cleanup_issue)
    if not quarantine_deleted:
        issues.append("quarantine directory still exists after attempt")

    (
        post_issues,
        inventory_count,
        trading_keywords_found,
        repo_ex5_artifacts,
        repo_compile_logs,
        repo_mq5_modified,
    ) = post_attempt_checks(root_dir, mq5_snapshot_before=mq5_snapshot_before)
    issues.extend(post_issues)

    attempt_conditions_met = (
        success_reclassification_attempt
        and classification["compile_log_semantic_success"] is True
        and classification["compile_log_errors"] == 0
        and bool(quarantine_artifacts["quarantine_ex5_artifact_detected"])
        and int(quarantine_artifacts["quarantine_ex5_artifact_count"]) >= 1
        and bool(quarantine_artifacts["artifact_hash_captured"])
        and int(quarantine_artifacts["quarantine_ex5_artifact_size_bytes"]) > 0
        and quarantine_deleted
        and not repo_ex5_artifacts
        and not repo_compile_logs
        and not repo_mq5_modified
        and not trading_keywords_found
        and inventory_count == 7
    )
    success_reclassification_decision = "NONE"
    compile_only_reclassified_success = False
    compile_success_scope = "NONE"
    if success_reclassification_attempt:
        success_reclassification_decision = "PASS" if attempt_conditions_met else "FAIL"
        compile_only_reclassified_success = attempt_conditions_met
        compile_success_scope = "compile-only-diagnostic" if attempt_conditions_met else "NONE"

    compile_success = (
        attempt_conditions_met
        if success_reclassification_attempt
        else False if artifact_hash_capture else (
            bool(classification["compile_success"]) if diagnostic_capture else compile_exit_code == 0
        )
    )
    compile_failure_diagnosed = diagnostic_capture and compile_exit_code not in (None, 0)
    exit_code = 0 if not issues and (diagnostic_capture or compile_success) else 1
    if success_reclassification_attempt and not attempt_conditions_met:
        exit_code = 1

    return AttemptResult(
        exit_code=exit_code,
        compile_exit_code=compile_exit_code,
        metaeditor_executed=metaeditor_executed,
        mql5_compile_executed=mql5_compile_executed,
        compile_target_is_quarantine_copy=compile_target_is_quarantine_copy,
        quarantine_outside_repo=quarantine_outside_repo,
        quarantine_deleted=quarantine_deleted,
        repo_mq5_modified=repo_mq5_modified,
        repo_ex5_artifacts=repo_ex5_artifacts,
        repo_compile_logs=repo_compile_logs,
        trading_keywords_found=trading_keywords_found,
        mq5_inventory_files=inventory_count,
        issues=issues,
        quarantine_dir=quarantine,
        diagnostic_capture=diagnostic_capture,
        compile_success=compile_success,
        compile_failure_diagnosed=compile_failure_diagnosed,
        compile_log_captured=compile_log_captured,
        compile_log_excerpt=compile_log_excerpt,
        compile_log_errors=classification["compile_log_errors"],
        compile_log_warnings=classification["compile_log_warnings"],
        compile_log_semantic_success=classification["compile_log_semantic_success"],
        compile_result_classification=str(classification["compile_result_classification"]),
        metaeditor_exit_code_anomaly=bool(classification["metaeditor_exit_code_anomaly"]),
        task304_success_result_created=bool(classification["task304_success_result_created"]),
        followup_required=bool(classification["followup_required"]),
        quarantine_ex5_artifact_detected=bool(
            quarantine_artifacts["quarantine_ex5_artifact_detected"]
        ),
        quarantine_ex5_artifact_count=int(quarantine_artifacts["quarantine_ex5_artifact_count"]),
        quarantine_compile_log_detected=bool(quarantine_artifacts["quarantine_compile_log_detected"]),
        quarantine_compile_log_captured=compile_log_captured,
        artifact_hash_capture=artifact_hash_capture,
        artifact_hash_captured=bool(quarantine_artifacts["artifact_hash_captured"]),
        quarantine_ex5_artifact_sha256=str(quarantine_artifacts["quarantine_ex5_artifact_sha256"]),
        quarantine_ex5_artifact_size_bytes=int(quarantine_artifacts["quarantine_ex5_artifact_size_bytes"]),
        success_reclassification_attempt=success_reclassification_attempt,
        success_reclassification_attempted=success_reclassification_attempt,
        success_reclassification_decision=success_reclassification_decision,
        compile_only_reclassified_success=compile_only_reclassified_success,
        compile_success_scope=compile_success_scope,
    )


def dry_run(root_dir: Path, *, metaeditor_path: Path | None = None) -> AttemptResult:
    preflight = collect_preflight_state(root_dir, metaeditor_path=metaeditor_path)
    return AttemptResult(
        exit_code=0 if not preflight.issues else 1,
        compile_exit_code=None,
        metaeditor_executed=False,
        mql5_compile_executed=False,
        compile_target_is_quarantine_copy=False,
        quarantine_outside_repo=True,
        quarantine_deleted=True,
        repo_mq5_modified=False,
        repo_ex5_artifacts=preflight.repo_ex5_artifacts,
        repo_compile_logs=preflight.repo_compile_logs,
        trading_keywords_found=preflight.trading_keywords_found,
        mq5_inventory_files=preflight.mq5_inventory_files,
        issues=preflight.issues,
    )


def bool_text(value: bool) -> str:
    return str(value).lower()


def value_text(value: object) -> str:
    if isinstance(value, bool):
        return bool_text(value)
    return str(value)


def print_result(result: AttemptResult, *, dry_run_mode: bool) -> None:
    if result.issues:
        print("MQL5 compile-only quarantined execution failed")
        print("Issues:")
        for issue in result.issues:
            print(f"- {issue}")
    else:
        print("MQL5 compile-only quarantined execution passed")
    print("mql5_compile_only_quarantined_execution=true")
    print("compile_only_authorized_by_TASK_304=true")
    if result.diagnostic_capture:
        print("mql5_compile_only_failure_diagnostic=true")
        print("diagnostic_capture=true")
        print("compile_only_authorized_by_TASK_305=true")
        print("mql5_compile_diagnostic_artifact_classification=true")
        print("compile_only_authorized_by_TASK_307=true")
    if result.artifact_hash_capture:
        print("mql5_compile_artifact_hash_capture=true")
        print("artifact_hash_capture_diagnostic=true")
        print("compile_only_authorized_by_TASK_310=true")
    if result.success_reclassification_attempt:
        print("mql5_compile_success_reclassification_attempt=true")
        print("compile_only_authorized_by_TASK_312=true")
        print(f"success_reclassification_attempted={bool_text(result.success_reclassification_attempted)}")
        print(f"success_reclassification_decision={result.success_reclassification_decision}")
        print(f"compile_only_reclassified_success={bool_text(result.compile_only_reclassified_success)}")
        print(f"compile_success_scope={result.compile_success_scope}")
    print(f"dry_run={bool_text(dry_run_mode)}")
    print(f"quarantine_dir_outside_repo={bool_text(result.quarantine_outside_repo)}")
    print(f"metaeditor_executed={bool_text(result.metaeditor_executed)}")
    print(f"mql5_compile_executed={bool_text(result.mql5_compile_executed)}")
    print(f"compile_target_is_quarantine_copy={bool_text(result.compile_target_is_quarantine_copy)}")
    print(f"repo_mq5_modified={bool_text(result.repo_mq5_modified)}")
    print(f"repo_ex5_artifacts={bool_text(result.repo_ex5_artifacts)}")
    print(f"repo_compile_logs={bool_text(result.repo_compile_logs)}")
    print("mt5_terminal_run=false")
    print("strategy_tester_run=false")
    print("trading_executed=false")
    print("manifest_generated=false")
    print("evidence_generated=false")
    print("report_generated=false")
    print("external_evidence_copied=false")
    print(f"quarantine_deleted={bool_text(result.quarantine_deleted)}")
    print(f"mq5_inventory_files={result.mq5_inventory_files}")
    print(f"trading_keywords={bool_text(result.trading_keywords_found)}")
    if result.compile_exit_code is not None:
        print(f"compile_exit_code={result.compile_exit_code}")
    if result.diagnostic_capture:
        print(f"compile_success={bool_text(result.compile_success)}")
        print(f"compile_failure_diagnosed={bool_text(result.compile_failure_diagnosed)}")
        print(f"compile_log_captured={bool_text(result.compile_log_captured)}")
        print(f"compile_log_stdout_only={bool_text(result.compile_log_stdout_only)}")
        print(f"compile_log_saved_to_repo={bool_text(result.compile_log_saved_to_repo)}")
        print(f"compile_log_errors={value_text(result.compile_log_errors)}")
        print(f"compile_log_warnings={value_text(result.compile_log_warnings)}")
        print(f"compile_log_semantic_success={value_text(result.compile_log_semantic_success)}")
        print(f"quarantine_ex5_artifact_detected={bool_text(result.quarantine_ex5_artifact_detected)}")
        print(f"quarantine_ex5_artifact_count={result.quarantine_ex5_artifact_count}")
        print(f"quarantine_compile_log_detected={bool_text(result.quarantine_compile_log_detected)}")
        print(f"quarantine_compile_log_captured={bool_text(result.quarantine_compile_log_captured)}")
        if result.artifact_hash_capture:
            print(f"artifact_hash_captured={bool_text(result.artifact_hash_captured)}")
            print(f"artifact_hash_stdout_only={bool_text(result.artifact_hash_stdout_only)}")
            print(f"artifact_hash_saved_to_repo={bool_text(result.artifact_hash_saved_to_repo)}")
            print(f"quarantine_ex5_artifact_sha256={result.quarantine_ex5_artifact_sha256}")
            print(f"quarantine_ex5_artifact_size_bytes={result.quarantine_ex5_artifact_size_bytes}")
        print(f"compile_result_classification={result.compile_result_classification}")
        print(f"metaeditor_exit_code_anomaly={bool_text(result.metaeditor_exit_code_anomaly)}")
        print(f"success_reclassification_done={bool_text(result.success_reclassification_done)}")
        print(f"task304_success_result_created={bool_text(result.task304_success_result_created)}")
        print(f"followup_required={bool_text(result.followup_required)}")
        if result.success_reclassification_attempt:
            print(f"trading_authorization={bool_text(result.trading_authorization)}")
            print(f"deployment_readiness={bool_text(result.deployment_readiness)}")
            print(f"backtest_readiness={bool_text(result.backtest_readiness)}")
            print(f"strategy_readiness={bool_text(result.strategy_readiness)}")
        if result.compile_failure_diagnosed:
            print("compile_log_excerpt_start")
            if result.compile_log_excerpt:
                print(stdout_safe_text(result.compile_log_excerpt))
            print("compile_log_excerpt_end")
    if result.quarantine_dir is not None:
        print(f"quarantine_dir={result.quarantine_dir}")
    print(SAFETY_NOTICE)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a quarantined MQL5 compile-only attempt."
    )
    parser.add_argument("--execute", action="store_true", help="Execute MetaEditor compile-only.")
    parser.add_argument(
        "--diagnostic-capture",
        action="store_true",
        help="Capture compile failure diagnostics from the quarantined compile log.",
    )
    parser.add_argument(
        "--artifact-hash-capture",
        action="store_true",
        help="Capture quarantine .ex5 hash/size metadata to stdout during diagnostic compile.",
    )
    parser.add_argument(
        "--success-reclassification-attempt",
        action="store_true",
        help="Attempt TASK-312 compile-only success reclassification from stdout-only diagnostics.",
    )
    parser.add_argument(
        "--quarantine-parent",
        default=str(Path(tempfile.gettempdir())),
        help="Parent directory for the temporary quarantine directory.",
    )
    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    *,
    root_dir: Path | None = None,
    runner=run_subprocess,
    metaeditor_path: Path | None = None,
    remove_tree=shutil.rmtree,
) -> int:
    args = parse_args(argv)
    root = (root_dir or ROOT_DIR).resolve()
    quarantine_parent = Path(args.quarantine_parent).resolve()

    if args.success_reclassification_attempt and not (
        args.execute and args.diagnostic_capture and args.artifact_hash_capture
    ):
        print(
            "Error: --success-reclassification-attempt requires --execute "
            "--diagnostic-capture --artifact-hash-capture."
        )
        return 1
    if args.artifact_hash_capture and not (args.execute and args.diagnostic_capture):
        print("Error: --artifact-hash-capture requires --execute --diagnostic-capture.")
        return 1
    if args.diagnostic_capture and not args.execute:
        print("Error: --diagnostic-capture requires --execute.")
        return 1

    if args.execute:
        result = execute_attempt(
            root,
            quarantine_parent=quarantine_parent,
            metaeditor_path=metaeditor_path,
            runner=runner,
            diagnostic_capture=args.diagnostic_capture,
            artifact_hash_capture=args.artifact_hash_capture,
            success_reclassification_attempt=args.success_reclassification_attempt,
            remove_tree=remove_tree,
        )
        print_result(result, dry_run_mode=False)
        return result.exit_code

    result = dry_run(root, metaeditor_path=metaeditor_path)
    print_result(result, dry_run_mode=True)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
