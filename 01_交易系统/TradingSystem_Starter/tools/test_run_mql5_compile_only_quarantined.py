#!/usr/bin/env python3
"""Self-test for the quarantined MQL5 compile-only runner."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import subprocess
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT_DIR / "tools" / "run_mql5_compile_only_quarantined.py"

MQ5_FILES = {
    "TradingSystem.mq5": "int OnInit(){ return 0; }\n",
    "config/InputConfig.mqh": "input bool InpEnableTrading = false;\n",
    "core/EaController.mqh": "class EaController {};\n",
    "logger/Logger.mqh": "class Logger {};\n",
    "risk/RiskManager.mqh": "class RiskManager {};\n",
    "execution/ExecutionManager.mqh": "class ExecutionManager {};\n",
    "signals/SignalEngine.mqh": "class SignalEngine {};\n",
}

BOUNDARY_DOCS = (
    "V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md",
    "V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md",
    "V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md",
    "V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md",
    "V060_TASK_298_MQL5_COMPILE_ONLY_DRYRUN.md",
    "V060_TASK_301_V060_COMPILE_READINESS_PLANNING.md",
    "V060_TASK_302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE.md",
    "V060_TASK_303_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN.md",
)


def fail(message: str) -> int:
    print("Quarantined MQL5 compile-only runner self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_mql5_compile_only_quarantined",
        RUNNER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec: {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_project(root: Path, *, missing_doc: str = "", mq5_overrides=None) -> None:
    for name in BOUNDARY_DOCS:
        if name == missing_doc:
            continue
        write_text(root / "docs" / name, f"# {name}\n")

    files = dict(MQ5_FILES)
    if mq5_overrides:
        files.update(mq5_overrides)
    for rel_path, text in files.items():
        write_text(root / "mq5" / rel_path, text)


def run_main(module, root: Path, args: list[str], *, runner=None, metaeditor_path: Path | None = None):
    output = io.StringIO()
    kwargs = {"root_dir": root}
    if runner is not None:
        kwargs["runner"] = runner
    if metaeditor_path is not None:
        kwargs["metaeditor_path"] = metaeditor_path
    with redirect_stdout(output):
        result = module.main(args, **kwargs)
    return result, output.getvalue()


def run_main_with_remove_tree(
    module,
    root: Path,
    args: list[str],
    *,
    runner=None,
    metaeditor_path: Path | None = None,
    remove_tree=None,
):
    output = io.StringIO()
    kwargs = {"root_dir": root}
    if runner is not None:
        kwargs["runner"] = runner
    if metaeditor_path is not None:
        kwargs["metaeditor_path"] = metaeditor_path
    if remove_tree is not None:
        kwargs["remove_tree"] = remove_tree
    with redirect_stdout(output):
        result = module.main(args, **kwargs)
    return result, output.getvalue()


def snapshot_files(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())


def write_fake_compile_log(command, text: str) -> None:
    for part in command:
        part_text = str(part)
        if part_text.startswith("/log:"):
            Path(part_text[len("/log:") :]).write_text(text, encoding="utf-8")


def write_fake_quarantine_ex5(command, text: str = "fake ex5\n") -> None:
    for part in command:
        part_text = str(part)
        if part_text.startswith("/compile:"):
            compile_target = Path(part_text[len("/compile:") :])
            write_text(compile_target.with_suffix(".ex5"), text)


def test_dry_run_does_not_call_metaeditor(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        calls = []

        def fake_runner(command):
            calls.append(tuple(command))
            return subprocess.CompletedProcess(list(command), 0, stdout="", stderr="")

        before = snapshot_files(root)
        result, output = run_main(module, root, [], runner=fake_runner)
        after = snapshot_files(root)
        if result != 0:
            return f"dry-run should pass\n{output}"
        if calls:
            return f"dry-run called runner unexpectedly: {calls}"
        if before != after:
            return "dry-run modified project files"
        for text in (
            "dry_run=true",
            "metaeditor_executed=false",
            "mql5_compile_executed=false",
            "compile_target_is_quarantine_copy=false",
            "repo_ex5_artifacts=false",
            "repo_compile_logs=false",
        ):
            if text not in output:
                return f"dry-run missing stdout field {text}\n{output}"
    return ""


def test_execute_with_fake_metaeditor_success(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "repo"
        outside = Path(temp_dir) / "outside"
        root.mkdir()
        outside.mkdir()
        build_project(root)
        fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
        write_text(fake_metaeditor, "fake exe\n")
        calls = []

        def fake_runner(command):
            calls.append(tuple(command))
            return subprocess.CompletedProcess(list(command), 0, stdout="compile ok", stderr="")

        before = snapshot_files(root)
        result, output = run_main(
            module,
            root,
            ["--execute", "--quarantine-parent", str(outside)],
            runner=fake_runner,
            metaeditor_path=fake_metaeditor,
        )
        after = snapshot_files(root)
        if result != 0:
            return f"fake successful MetaEditor should pass\n{output}"
        if len(calls) != 1:
            return f"expected one fake MetaEditor call, got {len(calls)}"
        line = " ".join(str(part) for part in calls[0])
        if "terminal64.exe" in line or "Strategy Tester" in line:
            return f"forbidden executable/path used\n{line}"
        if "/compile:" not in line or "/log:" not in line:
            return f"compile command missing required switches\n{line}"
        if str(root) in line and str(outside) not in line:
            return f"compile command did not target quarantine copy\n{line}"
        if before != after:
            return "execute modified project files"
        if any(outside.iterdir()):
            return "quarantine directory was not cleaned"
        for text in (
            "mql5_compile_only_quarantined_execution=true",
            "compile_only_authorized_by_TASK_304=true",
            "quarantine_dir_outside_repo=true",
            "metaeditor_executed=true",
            "mql5_compile_executed=true",
            "compile_target_is_quarantine_copy=true",
            "quarantine_deleted=true",
            "repo_ex5_artifacts=false",
            "repo_compile_logs=false",
            "trading_keywords=false",
        ):
            if text not in output:
                return f"execute success missing stdout field {text}\n{output}"
    return ""


def test_execute_fake_metaeditor_failure_cleans_quarantine(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "repo"
        outside = Path(temp_dir) / "outside"
        root.mkdir()
        outside.mkdir()
        build_project(root)
        fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
        write_text(fake_metaeditor, "fake exe\n")

        def fake_runner(command):
            return subprocess.CompletedProcess(list(command), 9, stdout="", stderr="compile failed")

        result, output = run_main(
            module,
            root,
            ["--execute", "--quarantine-parent", str(outside)],
            runner=fake_runner,
            metaeditor_path=fake_metaeditor,
        )
        if result == 0:
            return f"fake MetaEditor failure should fail\n{output}"
        if any(outside.iterdir()):
            return "quarantine directory was not cleaned after failure"
        if "quarantine_deleted=true" not in output:
            return f"failure output did not confirm cleanup\n{output}"
    return ""


def test_diagnostic_fake_metaeditor_failure_returns_successful_capture(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "repo"
        outside = Path(temp_dir) / "outside"
        root.mkdir()
        outside.mkdir()
        build_project(root)
        fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
        write_text(fake_metaeditor, "fake exe\n")

        def fake_runner(command):
            write_fake_compile_log(command, "compile failed line 1\ncompile failed line 2\n")
            return subprocess.CompletedProcess(list(command), 1, stdout="", stderr="compile failed")

        before = snapshot_files(root)
        result, output = run_main(
            module,
            root,
            ["--execute", "--diagnostic-capture", "--quarantine-parent", str(outside)],
            runner=fake_runner,
            metaeditor_path=fake_metaeditor,
        )
        after = snapshot_files(root)
        if result != 0:
            return f"diagnostic capture for compile exit 1 should pass\n{output}"
        if before != after:
            return "diagnostic capture wrote files to repo"
        if any(outside.iterdir()):
            return "diagnostic capture did not clean quarantine"
        required = (
            "mql5_compile_only_failure_diagnostic=true",
            "diagnostic_capture=true",
            "compile_only_authorized_by_TASK_305=true",
            "metaeditor_executed=true",
            "mql5_compile_executed=true",
            "compile_exit_code=1",
            "compile_success=false",
            "compile_failure_diagnosed=true",
            "compile_log_captured=true",
            "compile_log_stdout_only=true",
            "compile_log_saved_to_repo=false",
            "quarantine_deleted=true",
            "repo_ex5_artifacts=false",
            "repo_compile_logs=false",
            "compile_log_excerpt_start",
            "compile failed line 1",
            "compile_log_excerpt_end",
        )
        for text in required:
            if text not in output:
                return f"diagnostic failure output missing {text}\n{output}"
    return ""


def test_diagnostic_quarantine_ex5_exit_anomaly_is_classified(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "repo"
        outside = Path(temp_dir) / "outside"
        root.mkdir()
        outside.mkdir()
        build_project(root)
        fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
        write_text(fake_metaeditor, "fake exe\n")

        def fake_runner(command):
            write_fake_compile_log(command, "Result: 0 errors, 0 warnings\n")
            write_fake_quarantine_ex5(command)
            return subprocess.CompletedProcess(list(command), 1, stdout="", stderr="exit anomaly")

        before = snapshot_files(root)
        result, output = run_main(
            module,
            root,
            ["--execute", "--diagnostic-capture", "--quarantine-parent", str(outside)],
            runner=fake_runner,
            metaeditor_path=fake_metaeditor,
        )
        after = snapshot_files(root)
        if result != 0:
            return f"diagnostic artifact anomaly should pass as captured diagnostic\n{output}"
        if before != after:
            return "diagnostic artifact anomaly copied files to repo"
        if any(outside.iterdir()):
            return "diagnostic artifact anomaly did not clean quarantine"
        required = (
            "mql5_compile_diagnostic_artifact_classification=true",
            "compile_only_authorized_by_TASK_307=true",
            "compile_exit_code=1",
            "compile_log_errors=0",
            "compile_log_warnings=0",
            "compile_log_semantic_success=true",
            "quarantine_ex5_artifact_detected=true",
            "quarantine_ex5_artifact_count=1",
            "quarantine_compile_log_detected=true",
            "quarantine_compile_log_captured=true",
            "compile_result_classification=compiled_artifact_with_metaeditor_exit_code_anomaly",
            "compile_success=false",
            "task304_success_result_created=false",
            "followup_required=true",
            "quarantine_deleted=true",
            "repo_ex5_artifacts=false",
            "repo_compile_logs=false",
        )
        for text in required:
            if text not in output:
                return f"diagnostic artifact anomaly output missing {text}\n{output}"
    return ""


def test_diagnostic_fake_metaeditor_success_does_not_create_task304_result(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "repo"
        outside = Path(temp_dir) / "outside"
        root.mkdir()
        outside.mkdir()
        build_project(root)
        fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
        write_text(fake_metaeditor, "fake exe\n")

        def fake_runner(command):
            write_fake_compile_log(command, "Result: 0 errors, 0 warnings\n")
            return subprocess.CompletedProcess(list(command), 0, stdout="compile ok", stderr="")

        result, output = run_main(
            module,
            root,
            ["--execute", "--diagnostic-capture", "--quarantine-parent", str(outside)],
            runner=fake_runner,
            metaeditor_path=fake_metaeditor,
        )
        if result != 0:
            return f"diagnostic capture for compile exit 0 should pass\n{output}"
        if "compile_success=true" not in output:
            return f"diagnostic success output missing compile_success=true\n{output}"
        if (root / "docs" / "V060_TASK_304_MQL5_COMPILE_ONLY_QUARANTINED_EXECUTION_RESULT.md").exists():
            return "diagnostic success created TASK-304 success result doc"
    return ""


def test_diagnostic_repo_artifact_leak_after_runner_fails(module) -> str:
    cases = (
        ("repo .ex5 leak", "mq5/Leaked.ex5"),
        ("repo compile log leak", "compile.log"),
    )
    for label, rel_path in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            outside = Path(temp_dir) / "outside"
            root.mkdir()
            outside.mkdir()
            build_project(root)
            fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
            write_text(fake_metaeditor, "fake exe\n")

            def fake_runner(command):
                write_fake_compile_log(command, "Result: 0 errors, 0 warnings\n")
                write_text(root / rel_path, "leaked artifact\n")
                return subprocess.CompletedProcess(list(command), 1, stdout="", stderr="leaked")

            result, output = run_main(
                module,
                root,
                ["--execute", "--diagnostic-capture", "--quarantine-parent", str(outside)],
                runner=fake_runner,
                metaeditor_path=fake_metaeditor,
            )
            if result == 0:
                return f"{label} should fail after post-attempt checks\n{output}"
            if "repository contains prohibited" not in output:
                return f"{label} output missing repository artifact issue\n{output}"
    return ""


def test_diagnostic_repo_artifacts_fail(module) -> str:
    cases = (
        ("repo .ex5", "mq5/TradingSystem.ex5"),
        ("repo compile log", "compile.log"),
    )
    for label, rel_path in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_project(root)
            write_text(root / rel_path, "blocked\n")
            result, output = run_main(module, root, ["--execute", "--diagnostic-capture"])
            if result == 0:
                return f"{label} should fail diagnostic preflight\n{output}"
    return ""


def test_diagnostic_quarantine_deletion_failure_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "repo"
        outside = Path(temp_dir) / "outside"
        root.mkdir()
        outside.mkdir()
        build_project(root)
        fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
        write_text(fake_metaeditor, "fake exe\n")

        def fake_runner(command):
            write_fake_compile_log(command, "compile failed\n")
            return subprocess.CompletedProcess(list(command), 1, stdout="", stderr="compile failed")

        def failing_remove_tree(path):
            raise OSError("cleanup blocked")

        result, output = run_main_with_remove_tree(
            module,
            root,
            ["--execute", "--diagnostic-capture", "--quarantine-parent", str(outside)],
            runner=fake_runner,
            metaeditor_path=fake_metaeditor,
            remove_tree=failing_remove_tree,
        )
        if result == 0:
            return f"diagnostic cleanup failure should fail\n{output}"
        if "failed to delete quarantine directory" not in output:
            return f"diagnostic cleanup failure output missing cleanup issue\n{output}"
    return ""


def test_diagnostic_requires_execute(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        result, output = run_main(module, root, ["--diagnostic-capture"])
        if result == 0:
            return f"diagnostic without --execute should fail\n{output}"
        if "--diagnostic-capture requires --execute" not in output:
            return f"diagnostic without execute output was unclear\n{output}"
    return ""


def test_artifact_hash_capture_requires_execute_and_diagnostic(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        cases = (
            ["--artifact-hash-capture"],
            ["--execute", "--artifact-hash-capture"],
            ["--diagnostic-capture", "--artifact-hash-capture"],
        )
        for args in cases:
            result, output = run_main(module, root, args)
            if result == 0:
                return f"artifact hash capture args should fail without execute+diagnostic: {args}\n{output}"
            if "--artifact-hash-capture requires --execute --diagnostic-capture" not in output:
                return f"artifact hash capture invalid args output was unclear: {args}\n{output}"
    return ""


def test_success_reclassification_attempt_requires_full_authorization_chain(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        cases = (
            ["--success-reclassification-attempt"],
            ["--execute", "--success-reclassification-attempt"],
            ["--execute", "--diagnostic-capture", "--success-reclassification-attempt"],
            ["--artifact-hash-capture", "--success-reclassification-attempt"],
        )
        for args in cases:
            result, output = run_main(module, root, args)
            if result == 0:
                return (
                    "success reclassification attempt args should fail without "
                    f"execute+diagnostic+artifact hash: {args}\n{output}"
                )
            if (
                "--success-reclassification-attempt requires --execute "
                "--diagnostic-capture --artifact-hash-capture"
            ) not in output:
                return (
                    "success reclassification attempt invalid args output was unclear: "
                    f"{args}\n{output}"
                )
    return ""


def test_artifact_hash_capture_exit_anomaly_hashes_quarantine_ex5(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "repo"
        outside = Path(temp_dir) / "outside"
        root.mkdir()
        outside.mkdir()
        build_project(root)
        fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
        write_text(fake_metaeditor, "fake exe\n")

        def fake_runner(command):
            write_fake_compile_log(command, "Result: 0 errors, 0 warnings\n")
            write_fake_quarantine_ex5(command, "fake ex5 payload\n")
            return subprocess.CompletedProcess(list(command), 1, stdout="", stderr="exit anomaly")

        before = snapshot_files(root)
        result, output = run_main(
            module,
            root,
            [
                "--execute",
                "--diagnostic-capture",
                "--artifact-hash-capture",
                "--quarantine-parent",
                str(outside),
            ],
            runner=fake_runner,
            metaeditor_path=fake_metaeditor,
        )
        after = snapshot_files(root)
        if result != 0:
            return f"artifact hash capture should pass for exit anomaly with quarantine ex5\n{output}"
        if before != after:
            return "artifact hash capture copied files or hash metadata into repo"
        if any(outside.iterdir()):
            return "artifact hash capture did not clean quarantine"
        required = (
            "mql5_compile_artifact_hash_capture=true",
            "artifact_hash_capture_diagnostic=true",
            "compile_only_authorized_by_TASK_310=true",
            "metaeditor_executed=true",
            "mql5_compile_executed=true",
            "compile_exit_code=1",
            "compile_log_errors=0",
            "compile_log_warnings=0",
            "compile_log_semantic_success=true",
            "quarantine_ex5_artifact_detected=true",
            "quarantine_ex5_artifact_count=1",
            "artifact_hash_captured=true",
            "artifact_hash_stdout_only=true",
            "artifact_hash_saved_to_repo=false",
            "compile_result_classification=artifact_hash_captured_with_metaeditor_exit_code_anomaly",
            "compile_success=false",
            "success_reclassification_done=false",
            "task304_success_result_created=false",
            "followup_required=true",
            "quarantine_deleted=true",
            "repo_ex5_artifacts=false",
            "repo_compile_logs=false",
            "repo_mq5_modified=false",
        )
        for text in required:
            if text not in output:
                return f"artifact hash capture output missing {text}\n{output}"
        if "quarantine_ex5_artifact_sha256=NONE" in output:
            return f"artifact hash capture did not emit sha256\n{output}"
        size_line = next((line for line in output.splitlines() if line.startswith("quarantine_ex5_artifact_size_bytes=")), "")
        if not size_line or int(size_line.split("=", 1)[1]) <= 0:
            return f"artifact hash capture did not emit positive size\n{output}"
    return ""


def test_success_reclassification_attempt_passes_when_all_conditions_hold(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "repo"
        outside = Path(temp_dir) / "outside"
        root.mkdir()
        outside.mkdir()
        build_project(root)
        fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
        write_text(fake_metaeditor, "fake exe\n")

        def fake_runner(command):
            write_fake_compile_log(command, "Result: 0 errors, 0 warnings\n")
            write_fake_quarantine_ex5(command, "fake ex5 payload\n")
            return subprocess.CompletedProcess(list(command), 1, stdout="", stderr="exit anomaly")

        before = snapshot_files(root)
        result, output = run_main(
            module,
            root,
            [
                "--execute",
                "--diagnostic-capture",
                "--artifact-hash-capture",
                "--success-reclassification-attempt",
                "--quarantine-parent",
                str(outside),
            ],
            runner=fake_runner,
            metaeditor_path=fake_metaeditor,
        )
        after = snapshot_files(root)
        if result != 0:
            return f"success reclassification attempt should pass when all conditions hold\n{output}"
        if before != after:
            return "success reclassification attempt wrote artifact/hash metadata into repo"
        if any(outside.iterdir()):
            return "success reclassification attempt did not clean quarantine"
        required = (
            "mql5_compile_success_reclassification_attempt=true",
            "compile_only_authorized_by_TASK_312=true",
            "success_reclassification_attempted=true",
            "success_reclassification_decision=PASS",
            "compile_only_reclassified_success=true",
            "compile_success=true",
            "compile_success_scope=compile-only-diagnostic",
            "metaeditor_executed=true",
            "mql5_compile_executed=true",
            "compile_log_errors=0",
            "compile_log_semantic_success=true",
            "quarantine_ex5_artifact_detected=true",
            "quarantine_ex5_artifact_count=1",
            "artifact_hash_captured=true",
            "artifact_hash_stdout_only=true",
            "artifact_hash_saved_to_repo=false",
            "quarantine_deleted=true",
            "repo_ex5_artifacts=false",
            "repo_compile_logs=false",
            "repo_mq5_modified=false",
            "trading_authorization=false",
            "deployment_readiness=false",
            "backtest_readiness=false",
            "strategy_readiness=false",
        )
        for text in required:
            if text not in output:
                return f"success reclassification attempt output missing {text}\n{output}"
    return ""


def test_success_reclassification_attempt_fails_without_hash_or_artifact(module) -> str:
    cases = (
        ("no quarantine ex5", False, "Result: 0 errors, 0 warnings\n"),
        ("compile errors", True, "Result: 2 errors, 0 warnings\n"),
    )
    for label, create_artifact, log_text in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            outside = Path(temp_dir) / "outside"
            root.mkdir()
            outside.mkdir()
            build_project(root)
            fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
            write_text(fake_metaeditor, "fake exe\n")

            def fake_runner(command):
                write_fake_compile_log(command, log_text)
                if create_artifact:
                    write_fake_quarantine_ex5(command, "fake ex5 payload\n")
                return subprocess.CompletedProcess(list(command), 1, stdout="", stderr=label)

            result, output = run_main(
                module,
                root,
                [
                    "--execute",
                    "--diagnostic-capture",
                    "--artifact-hash-capture",
                    "--success-reclassification-attempt",
                    "--quarantine-parent",
                    str(outside),
                ],
                runner=fake_runner,
                metaeditor_path=fake_metaeditor,
            )
            if result == 0:
                return f"{label} should fail success reclassification decision\n{output}"
            for text in (
                "success_reclassification_attempted=true",
                "success_reclassification_decision=FAIL",
                "compile_only_reclassified_success=false",
                "compile_success=false",
                "compile_success_scope=NONE",
            ):
                if text not in output:
                    return f"{label} output missing {text}\n{output}"
    return ""


def test_success_reclassification_attempt_repo_artifact_leak_fails(module) -> str:
    cases = (
        ("repo .ex5 leak", "mq5/Leaked.ex5"),
        ("repo compile log leak", "compile.log"),
    )
    for label, rel_path in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            outside = Path(temp_dir) / "outside"
            root.mkdir()
            outside.mkdir()
            build_project(root)
            fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
            write_text(fake_metaeditor, "fake exe\n")

            def fake_runner(command):
                write_fake_compile_log(command, "Result: 0 errors, 0 warnings\n")
                write_fake_quarantine_ex5(command, "fake ex5 payload\n")
                write_text(root / rel_path, "leaked artifact\n")
                return subprocess.CompletedProcess(list(command), 1, stdout="", stderr=label)

            result, output = run_main(
                module,
                root,
                [
                    "--execute",
                    "--diagnostic-capture",
                    "--artifact-hash-capture",
                    "--success-reclassification-attempt",
                    "--quarantine-parent",
                    str(outside),
                ],
                runner=fake_runner,
                metaeditor_path=fake_metaeditor,
            )
            if result == 0:
                return f"{label} should fail success reclassification attempt\n{output}"
            if "success_reclassification_decision=FAIL" not in output:
                return f"{label} output missing failed decision\n{output}"
    return ""


def test_artifact_hash_capture_without_quarantine_ex5_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "repo"
        outside = Path(temp_dir) / "outside"
        root.mkdir()
        outside.mkdir()
        build_project(root)
        fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
        write_text(fake_metaeditor, "fake exe\n")

        def fake_runner(command):
            write_fake_compile_log(command, "Result: 0 errors, 0 warnings\n")
            return subprocess.CompletedProcess(list(command), 1, stdout="", stderr="exit anomaly")

        result, output = run_main(
            module,
            root,
            [
                "--execute",
                "--diagnostic-capture",
                "--artifact-hash-capture",
                "--quarantine-parent",
                str(outside),
            ],
            runner=fake_runner,
            metaeditor_path=fake_metaeditor,
        )
        if result == 0:
            return f"artifact hash capture should fail when no quarantine ex5 exists\n{output}"
        if "artifact_hash_captured=false" not in output:
            return f"missing artifact_hash_captured=false for no artifact case\n{output}"
    return ""


def test_artifact_hash_capture_exit_success_does_not_reclassify_success(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "repo"
        outside = Path(temp_dir) / "outside"
        root.mkdir()
        outside.mkdir()
        build_project(root)
        fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
        write_text(fake_metaeditor, "fake exe\n")

        def fake_runner(command):
            write_fake_compile_log(command, "Result: 0 errors, 0 warnings\n")
            write_fake_quarantine_ex5(command, "fake ex5 payload\n")
            return subprocess.CompletedProcess(list(command), 0, stdout="", stderr="")

        result, output = run_main(
            module,
            root,
            [
                "--execute",
                "--diagnostic-capture",
                "--artifact-hash-capture",
                "--quarantine-parent",
                str(outside),
            ],
            runner=fake_runner,
            metaeditor_path=fake_metaeditor,
        )
        if result != 0:
            return f"artifact hash capture exit-success case should pass as diagnostic\n{output}"
        for text in (
            "artifact_hash_captured=true",
            "compile_success=false",
            "success_reclassification_done=false",
            "task304_success_result_created=false",
        ):
            if text not in output:
                return f"exit-success artifact hash capture output missing {text}\n{output}"
        if (root / "docs" / "V060_TASK_304_MQL5_COMPILE_ONLY_QUARANTINED_EXECUTION_RESULT.md").exists():
            return "artifact hash capture created TASK-304 success result doc"
    return ""


def test_diagnostic_compile_log_excerpt_is_stdout_safe(module) -> str:
    if not hasattr(module, "stdout_safe_text"):
        return "runner is missing stdout_safe_text helper"
    unsafe = "compile failed: \ufffd \U0001f600\n"
    safe = module.stdout_safe_text(unsafe, encoding="gbk")
    try:
        safe.encode("gbk")
    except UnicodeEncodeError as exc:
        return f"diagnostic compile log excerpt is not stdout-safe: {exc}"
    return ""


def test_compile_log_excerpt_decodes_utf16_logs(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        compile_log = Path(temp_dir) / "compile.log"
        compile_log.write_text("Result: 0 errors, 0 warnings\n", encoding="utf-16")
        captured, excerpt = module.read_compile_log_excerpt(compile_log)
        if not captured:
            return "utf-16 compile log was not captured"
        if "Result: 0 errors" not in excerpt:
            return "utf-16 compile log excerpt was not readable"
        if "\x00" in excerpt:
            return "utf-16 compile log excerpt contains NUL bytes"
    return ""


def test_classify_exit_code_anomaly(module) -> str:
    if not hasattr(module, "classify_compile_diagnostic_result"):
        return "runner is missing classify_compile_diagnostic_result"
    result = module.classify_compile_diagnostic_result(
        1,
        "Result: 0 errors, 0 warnings",
        quarantine_ex5_artifact_detected=False,
    )
    expected = {
        "compile_log_errors": 0,
        "compile_log_warnings": 0,
        "compile_log_semantic_success": True,
        "compile_result_classification": "metaeditor_exit_code_anomaly_without_artifact",
        "metaeditor_exit_code_anomaly": True,
        "compile_success": False,
        "task304_success_result_created": False,
        "followup_required": True,
    }
    for key, value in expected.items():
        if result.get(key) != value:
            return f"classification anomaly {key} expected {value!r}, got {result.get(key)!r}"
    return ""


def test_classify_exit_code_anomaly_with_quarantine_artifact(module) -> str:
    result = module.classify_compile_diagnostic_result(
        1,
        "Result: 0 errors, 0 warnings",
        quarantine_ex5_artifact_detected=True,
    )
    if result.get("compile_result_classification") != "compiled_artifact_with_metaeditor_exit_code_anomaly":
        return f"quarantine artifact anomaly classification mismatch: {result}"
    if result.get("compile_success") is not False:
        return f"quarantine artifact anomaly must not be compile_success=true: {result}"
    if result.get("task304_success_result_created") is not False:
        return "quarantine artifact anomaly must not create TASK-304 success result"
    if result.get("followup_required") is not True:
        return f"quarantine artifact anomaly should require follow-up: {result}"
    return ""


def test_classify_exit_success_log_success(module) -> str:
    result = module.classify_compile_diagnostic_result(
        0,
        "Result: 0 errors, 0 warnings",
        quarantine_ex5_artifact_detected=True,
    )
    if result.get("compile_result_classification") != "compile_artifact_detected_exit_success":
        return f"exit success classification mismatch: {result}"
    if result.get("compile_success") is not True:
        return f"exit success should classify compile_success=true: {result}"
    if result.get("task304_success_result_created") is not False:
        return "TASK-306 classification must not create TASK-304 success result"
    return ""


def test_classify_compile_errors_present(module) -> str:
    result = module.classify_compile_diagnostic_result(1, "Result: 2 errors, 0 warnings")
    if result.get("compile_log_errors") != 2 or result.get("compile_log_warnings") != 0:
        return f"compile error counts were not parsed: {result}"
    if result.get("compile_result_classification") != "compile_errors_present":
        return f"compile errors classification mismatch: {result}"
    if result.get("compile_success") is not False:
        return f"compile errors should not be success: {result}"
    return ""


def test_classify_malformed_log(module) -> str:
    result = module.classify_compile_diagnostic_result(1, "MetaEditor returned no result footer")
    if result.get("compile_log_semantic_success") != "unknown":
        return f"malformed log should be semantic unknown: {result}"
    if result.get("compile_result_classification") != "unclassified":
        return f"malformed log should be unclassified: {result}"
    if result.get("compile_log_errors") != "UNKNOWN" or result.get("compile_log_warnings") != "UNKNOWN":
        return f"malformed log should use UNKNOWN counts: {result}"
    return ""


def test_quarantine_inside_repo_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "repo"
        root.mkdir()
        build_project(root)
        fake_metaeditor = Path(temp_dir) / "metaeditor64.exe"
        write_text(fake_metaeditor, "fake exe\n")
        result, output = run_main(
            module,
            root,
            ["--execute", "--quarantine-parent", str(root / "tmp")],
            metaeditor_path=fake_metaeditor,
        )
        if result == 0:
            return f"quarantine inside repo should fail\n{output}"
    return ""


def test_repo_ex5_compile_log_keyword_inventory_and_doc_failures(module) -> str:
    cases = (
        ("repo .ex5", {"artifact": ("mq5/TradingSystem.ex5", "binary\n")}),
        ("repo compile log", {"artifact": ("compile.log", "log\n")}),
        ("trading keyword", {"mq5_overrides": {"core/EaController.mqh": "void Probe(){ CTrade; }\n"}}),
        ("MQ5 inventory", {"remove": "logger/Logger.mqh"}),
        ("missing boundary", {"missing_doc": BOUNDARY_DOCS[0]}),
    )
    for label, case in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_project(root, missing_doc=case.get("missing_doc", ""), mq5_overrides=case.get("mq5_overrides"))
            if "artifact" in case:
                rel_path, text = case["artifact"]
                write_text(root / rel_path, text)
            if "remove" in case:
                (root / "mq5" / case["remove"]).unlink()
            result, output = run_main(module, root, [])
            if result == 0:
                return f"{label} should fail\n{output}"
    return ""


def main() -> int:
    if not RUNNER_PATH.exists():
        return fail(f"runner script not found: {RUNNER_PATH}")
    module = load_runner()
    tests = [
        test_dry_run_does_not_call_metaeditor,
        test_execute_with_fake_metaeditor_success,
        test_execute_fake_metaeditor_failure_cleans_quarantine,
        test_diagnostic_fake_metaeditor_failure_returns_successful_capture,
        test_diagnostic_quarantine_ex5_exit_anomaly_is_classified,
        test_diagnostic_fake_metaeditor_success_does_not_create_task304_result,
        test_diagnostic_repo_artifact_leak_after_runner_fails,
        test_diagnostic_repo_artifacts_fail,
        test_diagnostic_quarantine_deletion_failure_fails,
        test_diagnostic_requires_execute,
        test_artifact_hash_capture_requires_execute_and_diagnostic,
        test_success_reclassification_attempt_requires_full_authorization_chain,
        test_artifact_hash_capture_exit_anomaly_hashes_quarantine_ex5,
        test_success_reclassification_attempt_passes_when_all_conditions_hold,
        test_success_reclassification_attempt_fails_without_hash_or_artifact,
        test_success_reclassification_attempt_repo_artifact_leak_fails,
        test_artifact_hash_capture_without_quarantine_ex5_fails,
        test_artifact_hash_capture_exit_success_does_not_reclassify_success,
        test_diagnostic_compile_log_excerpt_is_stdout_safe,
        test_compile_log_excerpt_decodes_utf16_logs,
        test_classify_exit_code_anomaly,
        test_classify_exit_code_anomaly_with_quarantine_artifact,
        test_classify_exit_success_log_success,
        test_classify_compile_errors_present,
        test_classify_malformed_log,
        test_quarantine_inside_repo_fails,
        test_repo_ex5_compile_log_keyword_inventory_and_doc_failures,
    ]
    for test in tests:
        error = test(module)
        if error:
            return fail(error)
    print("Quarantined MQL5 compile-only runner self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
