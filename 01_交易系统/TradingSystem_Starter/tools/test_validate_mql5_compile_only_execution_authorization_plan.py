#!/usr/bin/env python3
"""Self-test for the MQL5 compile-only execution authorization plan validator."""

from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
import importlib.util
import io
import sys
import tempfile


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_mql5_compile_only_execution_authorization_plan.py"

SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."

TASK294_BOUNDARY_TEXT = """# TASK-DOC-294 future MQL5 compile-only boundary packet

- planning-only / boundary-only
- future MQL5 compile-only candidate
- Inventory only; no MT5 run; no trading authorization.
"""

TASK295_BOUNDARY_TEXT = """# TASK-295 MQL5 compile-only command discovery boundary

- command-discovery-only
- not compile execution
- not MetaEditor execution
- Inventory only; no MT5 run; no trading authorization.
"""

TASK296_BOUNDARY_TEXT = """# TASK-296 MQL5 compile-only artifact quarantine boundary

- artifact-quarantine-only
- no .ex5 artifact generated
- no compile log generated
- Inventory only; no MT5 run; no trading authorization.
"""

TASK297_BOUNDARY_TEXT = """# TASK-297 MQL5 compile-only execution boundary

- compile-only-task
- future compile-only candidate
- requires GPT explicit authorization
- artifact quarantine checked
- Inventory only; no MT5 run; no trading authorization.
"""

TASK298_DRYRUN_TEXT = """# TASK-298 MQL5 compile-only dry-run simulation

- dry-run-only
- artifact-quarantine enforced
- future compile-only task must be separately authorized by GPT
- stdout-only simulation
- Inventory only; no MT5 run; no trading authorization.
"""

TASK301_PLANNING_TEXT = """# TASK-301 v0.6.0 compile-readiness planning packet

- planning-only
- future compile-readiness candidate
- not implementation authorization
- Inventory only; no MT5 run; no trading authorization.
"""

TASK302_PREFLIGHT_GATE_TEXT = """# TASK-302 MQL5 compile-only execution preflight gate

- preflight-gate-only
- all previous compile-only boundary checks must pass before future compile execution
- artifact quarantine must pass before future compile execution
- TASK-303 must not be entered directly
- Inventory only; no MT5 run; no trading authorization.
"""

TASK303_AUTHORIZATION_PLAN_TEXT = """# TASK-303 v0.6.0 compile-only execution authorization planning packet

- planning-only
- authorization-boundary-only
- future compile-only execution candidate
- not compile execution
- not MetaEditor execution
- not MT5 run authorization
- not Strategy Tester authorization
- not backtest authorization
- not simulation trading authorization
- not real trading authorization
- not manifest generation authorization
- not evidence generation authorization
- not report generation authorization
- no MQL5 compile executed in TASK-303
- no MetaEditor executed in TASK-303
- no MT5 run in TASK-303
- no .ex5 artifact generated
- no compile log generated
- no manifest generated
- no evidence generated
- Inventory only; no MT5 run; no trading authorization.
- current HEAD: 15c675e TASK-302 implement MQL5 compile-only execution preflight gate
- current tag: v0.5.99-task-302-mql5-compile-only-preflight-gate
- MQ5 inventory remains 7 files
- Buy / Sell / OrderSend / PositionOpen / CTrade remain false
- TASK-304 must not be entered directly
- future TASK-304 must be separately authorized by GPT before any compile execution
- compile-only execution authorization requires all preflight gates PASS
- compile-only execution authorization must remain no-trade
- compile-only execution authorization must not run MT5 terminal
- compile-only execution authorization must not run Strategy Tester
- compile-only execution authorization must not create official manifest
- compile-only execution authorization must not copy external evidence
- compile-only execution authorization must include pre/post repo artifact checks
- compile-only execution authorization must check repo_ex5_artifacts=false before execution
- compile-only execution authorization must check repo_compile_logs=false before execution
- compile-only execution authorization must check trading_keywords=false before execution
- compile-only execution authorization must check MQ5 inventory remains 7 files before execution
- mql5-compile-only-boundary PASS
- mql5-compile-only-command-discovery PASS
- mql5-compile-only-artifact-quarantine PASS
- mql5-compile-only-execution-boundary PASS
- mql5-compile-only-dryrun PASS
- mql5-compile-only-dryrun-execution PASS
- mql5-compile-only-preflight-gate PASS
- v060-compile-readiness-planning PASS
- mq5-static-compile-readiness PASS
- mq5-compile-readiness-final-summary PASS
- MQ5 inventory 7 files
- trading keywords false
- repo_ex5_artifacts=false
- repo_compile_logs=false
- future GPT boundary explicitly says compile execution is allowed
"""

MQ5_FILES = {
    "TradingSystem.mq5": "int OnInit(){ return 0; }\n",
    "config/InputConfig.mqh": "input bool InpEnableTrading = false;\n",
    "core/EaController.mqh": "class EaController {};\n",
    "logger/Logger.mqh": "class Logger {};\n",
    "risk/RiskManager.mqh": "class RiskManager {};\n",
    "execution/ExecutionManager.mqh": "class ExecutionManager {};\n",
    "signals/SignalEngine.mqh": "class SignalEngine {};\n",
}


def fail(message: str) -> int:
    print("MQL5 compile-only execution authorization plan self-test failed")
    print(message)
    return 1


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_mql5_compile_only_execution_authorization_plan",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_project(
    root: Path,
    *,
    task294_text: str | None = TASK294_BOUNDARY_TEXT,
    task295_text: str | None = TASK295_BOUNDARY_TEXT,
    task296_text: str | None = TASK296_BOUNDARY_TEXT,
    task297_text: str | None = TASK297_BOUNDARY_TEXT,
    task298_text: str | None = TASK298_DRYRUN_TEXT,
    task301_text: str | None = TASK301_PLANNING_TEXT,
    task302_text: str | None = TASK302_PREFLIGHT_GATE_TEXT,
    task303_text: str | None = TASK303_AUTHORIZATION_PLAN_TEXT,
    mq5_overrides: dict[str, str] | None = None,
) -> None:
    docs = {
        "V060_TASK_294_MQL5_COMPILE_ONLY_BOUNDARY.md": task294_text,
        "V060_TASK_295_MQL5_COMPILE_ONLY_COMMAND_DISCOVERY.md": task295_text,
        "V060_TASK_296_MQL5_COMPILE_ONLY_ARTIFACT_QUARANTINE.md": task296_text,
        "V060_TASK_297_MQL5_COMPILE_ONLY_EXECUTION_BOUNDARY.md": task297_text,
        "V060_TASK_298_MQL5_COMPILE_ONLY_DRYRUN.md": task298_text,
        "V060_TASK_301_V060_COMPILE_READINESS_PLANNING.md": task301_text,
        "V060_TASK_302_MQL5_COMPILE_ONLY_PREFLIGHT_GATE.md": task302_text,
        "V060_TASK_303_COMPILE_ONLY_EXECUTION_AUTHORIZATION_PLAN.md": task303_text,
    }
    for name, text in docs.items():
        if text is not None:
            write_text(root / "docs" / name, text)

    files = dict(MQ5_FILES)
    if mq5_overrides:
        files.update(mq5_overrides)
    for rel_path, text in files.items():
        write_text(root / "mq5" / rel_path, text)


def run_main(module, root: Path):
    output = io.StringIO()
    with redirect_stdout(output):
        result = module.main([], root_dir=root)
    return result, output.getvalue()


def expect_pass(module, root: Path, message: str) -> str:
    before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    result, output = run_main(module, root)
    after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    if before != after:
        return f"{message}: validator created or removed files\nbefore={before}\nafter={after}"
    if result != 0:
        return f"{message}\n{output}"
    required = (
        "MQL5 compile-only execution authorization plan validation passed",
        "mql5_compile_only_execution_authorization_plan=true",
        "planning_only=true",
        "authorization_boundary_only=true",
        "compile_execution_authorized=false",
        "metaeditor_executed=false",
        "mql5_compile_executed=false",
        "mt5_run=false",
        "trading_authorization=false",
        "ex5_artifact_generated=false",
        "compile_log_generated=false",
        "repo_ex5_artifacts=false",
        "repo_compile_logs=false",
        "mq5_inventory_files=7",
        "trading_keywords=false",
        "future_task_304_requires_gpt_boundary=true",
        "all_preflight_gates_required=true",
        SAFETY_NOTICE,
    )
    for text in required:
        if text not in output:
            return f"{message}: missing stdout field {text}\n{output}"
    return ""


def expect_fail(module, root: Path, message: str) -> str:
    result, output = run_main(module, root)
    if result == 0:
        return f"{message}\n{output}"
    if "MQL5 compile-only execution authorization plan validation failed" not in output:
        return f"{message}: failure output missing header\n{output}"
    return ""


def positive_test_complete_fixture_passes(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        return expect_pass(module, root, "complete authorization plan fixture should pass")


def negative_test_missing_task303_doc(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task303_text=None)
        return expect_fail(module, root, "missing TASK-303 plan doc should fail")


def negative_test_missing_previous_boundary_doc(module) -> str:
    cases = (
        {"task294_text": None},
        {"task295_text": None},
        {"task296_text": None},
        {"task297_text": None},
        {"task298_text": None},
        {"task301_text": None},
        {"task302_text": None},
    )
    for case in cases:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            build_project(root, **case)
            error = expect_fail(module, root, f"missing previous boundary doc should fail: {case}")
            if error:
                return error
    return ""


def negative_test_missing_planning_only(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task303_text=TASK303_AUTHORIZATION_PLAN_TEXT.replace("- planning-only\n", ""))
        return expect_fail(module, root, "missing planning-only should fail")


def negative_test_missing_authorization_boundary_only(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(
            root,
            task303_text=TASK303_AUTHORIZATION_PLAN_TEXT.replace(
                "- authorization-boundary-only\n",
                "",
            ),
        )
        return expect_fail(module, root, "missing authorization-boundary-only should fail")


def negative_test_missing_not_compile_execution(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, task303_text=TASK303_AUTHORIZATION_PLAN_TEXT.replace("- not compile execution\n", ""))
        return expect_fail(module, root, "missing not compile execution should fail")


def negative_test_missing_no_compile_phrase(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(
            root,
            task303_text=TASK303_AUTHORIZATION_PLAN_TEXT.replace(
                "- no MQL5 compile executed in TASK-303\n",
                "",
            ),
        )
        return expect_fail(module, root, "missing no MQL5 compile executed should fail")


def negative_test_missing_no_metaeditor_phrase(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(
            root,
            task303_text=TASK303_AUTHORIZATION_PLAN_TEXT.replace(
                "- no MetaEditor executed in TASK-303\n",
                "",
            ),
        )
        return expect_fail(module, root, "missing no MetaEditor executed should fail")


def negative_test_missing_no_ex5_phrase(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(
            root,
            task303_text=TASK303_AUTHORIZATION_PLAN_TEXT.replace(
                "- no .ex5 artifact generated\n",
                "",
            ),
        )
        return expect_fail(module, root, "missing no .ex5 artifact generated should fail")


def negative_test_missing_no_compile_log_phrase(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(
            root,
            task303_text=TASK303_AUTHORIZATION_PLAN_TEXT.replace(
                "- no compile log generated\n",
                "",
            ),
        )
        return expect_fail(module, root, "missing no compile log generated should fail")


def negative_test_missing_task304_boundary_phrase(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        text = TASK303_AUTHORIZATION_PLAN_TEXT.replace(
            "- future TASK-304 must be separately authorized by GPT before any compile execution\n",
            "",
        ).replace(
            "- TASK-304 must not be entered directly\n",
            "",
        )
        build_project(root, task303_text=text)
        return expect_fail(module, root, "missing TASK-304 boundary phrase should fail")


def negative_test_repo_ex5_artifact_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        write_text(root / "mq5" / "TradingSystem.ex5", "binary placeholder\n")
        return expect_fail(module, root, ".ex5 artifact in repo should fail")


def negative_test_compile_log_fails(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        write_text(root / "compile.log", "compile log placeholder\n")
        return expect_fail(module, root, "compile log in repo should fail")


def positive_test_existing_localhost_log_allowed(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        write_text(root / "logs" / "localhost-3000.debug.log", "existing local dev log\n")
        return expect_pass(module, root, "localhost dev log should be allowed")


def negative_test_mq5_inventory_not_seven(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root)
        (root / "mq5" / "logger" / "Logger.mqh").unlink()
        return expect_fail(module, root, "MQ5 inventory other than 7 should fail")


def negative_test_trading_keyword_present(module) -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        build_project(root, mq5_overrides={"core/EaController.mqh": "void Probe(){ CTrade; }\n"})
        return expect_fail(module, root, "trading keyword should fail")


def positive_test_does_not_import_subprocess(module) -> str:
    if hasattr(module, "subprocess"):
        return "validator module must not import subprocess"
    return ""


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")

    module = load_validator()
    tests = [
        positive_test_complete_fixture_passes,
        negative_test_missing_task303_doc,
        negative_test_missing_previous_boundary_doc,
        negative_test_missing_planning_only,
        negative_test_missing_authorization_boundary_only,
        negative_test_missing_not_compile_execution,
        negative_test_missing_no_compile_phrase,
        negative_test_missing_no_metaeditor_phrase,
        negative_test_missing_no_ex5_phrase,
        negative_test_missing_no_compile_log_phrase,
        negative_test_missing_task304_boundary_phrase,
        negative_test_repo_ex5_artifact_fails,
        negative_test_compile_log_fails,
        positive_test_existing_localhost_log_allowed,
        negative_test_mq5_inventory_not_seven,
        negative_test_trading_keyword_present,
        positive_test_does_not_import_subprocess,
    ]
    for test in tests:
        error = test(module)
        if error:
            return fail(error)

    print("MQL5 compile-only execution authorization plan self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
