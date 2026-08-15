#!/usr/bin/env python3
"""Self-test for the v0.6.0 implementation boundary validator."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_v060_implementation_boundary.py"
OFFICIAL_MANIFEST_PATH = (
    "backtest/reports/manifests/"
    "TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json"
)


COMPLETE_DOC_TEXT = f"""
## TASK-DOC-223 define v0.6.0 implementation boundary

- current phase remains v0.5.0
- current stable tag remains v0.5.35-v060-implementation-planning-boundary-tag-completion-audit-stable-tag-completion-audit
- v0.5.35-v060-implementation-planning-boundary-tag-completion-audit-stable-tag-completion-audit is fixed
- current engineering gap: none
- current safety boundary gap: none
- current manifest gap: none
- workflow simplification is completed and remains active
- v0.6.0 implementation boundary is defined only as a planning and validation boundary
- release validation bundle baseline before this task was PASS 9/9
- tools/validate_v060_implementation_boundary.py was created as a read-only validator
- tools/run_release_validation_bundle.py was integrated with the v0.6.0 implementation boundary validator
- official manifest path: {OFFICIAL_MANIFEST_PATH}
- this task does not start v0.6.0 implementation
- this task does not authorize live trading readiness
- this task does not authorize real trading availability
- this task does not authorize profitability claims
- this task does not authorize real trading
- this task does not authorize MT5 run
- this task does not authorize MQ5 modification
- this task does not authorize new manifest creation
- this task does not authorize external evidence copying
- this task does not authorize official manifest modification
- do not directly enter TASK-224
- do not directly enter v0.6.0 implementation
- do not directly run MT5
- do not directly modify MQ5
- do not create a new manifest
- do not copy external evidence
- the next task must be explicitly issued by ChatGPT
"""


def fail(message: str) -> int:
    print("v0.6.0 implementation boundary self-test failed")
    print(message)
    return 1


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_v060_implementation_boundary",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec: {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def complete_state_docs() -> dict[str, str]:
    return {
        "docs/CURRENT_TASK.md": COMPLETE_DOC_TEXT,
        "docs/HANDOFF_PROMPT.md": COMPLETE_DOC_TEXT,
        "docs/PROJECT_STATE.md": COMPLETE_DOC_TEXT,
    }


def assert_fails(validator, state_docs: dict[str, str | None], label: str) -> str:
    failures = validator.validate_texts(state_docs)
    if not failures:
        return f"{label}: expected failure, got PASS"
    return ""


def assert_passes(validator, state_docs: dict[str, str], label: str) -> str:
    failures = validator.validate_texts(state_docs)
    if failures:
        return f"{label}: expected PASS, got failures: {failures}"
    return ""


def test_missing_doc_content(validator) -> str:
    state_docs = complete_state_docs()
    state_docs["docs/CURRENT_TASK.md"] = None
    return assert_fails(validator, state_docs, "missing project state doc content")


def test_missing_task_marker(validator) -> str:
    state_docs = complete_state_docs()
    state_docs["docs/HANDOFF_PROMPT.md"] = state_docs["docs/HANDOFF_PROMPT.md"].replace(
        "TASK-DOC-223 define v0.6.0 implementation boundary",
        "TASK-DOC-223",
    )
    return assert_fails(validator, state_docs, "missing TASK-DOC-223 boundary marker")


def test_missing_safety_marker(validator) -> str:
    state_docs = complete_state_docs()
    state_docs["docs/PROJECT_STATE.md"] = state_docs["docs/PROJECT_STATE.md"].replace(
        "- this task does not authorize MT5 run\n",
        "",
    )
    return assert_fails(validator, state_docs, "missing no MT5 marker")


def test_direct_v060_implementation_fails(validator) -> str:
    state_docs = complete_state_docs()
    state_docs["docs/CURRENT_TASK.md"] += "\nNext step: start v0.6.0 implementation\n"
    return assert_fails(validator, state_docs, "direct v0.6.0 implementation next step")


def test_complete_required_text_passes(validator) -> str:
    return assert_passes(
        validator,
        complete_state_docs(),
        "complete implementation boundary state docs",
    )


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")

    validator = load_validator_module()
    tests = [
        test_missing_doc_content,
        test_missing_task_marker,
        test_missing_safety_marker,
        test_direct_v060_implementation_fails,
        test_complete_required_text_passes,
    ]

    for test in tests:
        error = test(validator)
        if error:
            return fail(error)

    print("v0.6.0 implementation boundary self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
