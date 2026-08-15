#!/usr/bin/env python3
"""Self-test for the v0.6.0 implementation planning boundary validator."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_v060_implementation_planning_boundary.py"

OFFICIAL_MANIFEST_PATH = (
    "backtest/reports/manifests/"
    "TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json"
)

COMPLETE_IMPLEMENTATION_TEXT = f"""
# v0.6.0 Implementation Planning Boundary

This document defines the v0.6.0 implementation planning boundary.
The current phase remains v0.5.0.
v0.6.0 implementation planning does not mean v0.6.0 has started and does not authorize v0.6.0 implementation.
Any future v0.6.0 implementation task must be separately authorized by ChatGPT.

Every future implementation task must default to no MT5 run.
Every future implementation task must default to no MQ5 modification.
Every future implementation task must default to no external evidence copying.
Every future implementation task must default to no new official manifest creation unless explicitly authorized.

Future tasks must preserve no live trading readiness, no real trading availability, and no profitability claims.
Future tooling must preserve metadata-only evidence handling.
Future tooling must preserve the risk-first policy.
Future tooling must preserve explicit authorization boundaries.

Official manifest path: {OFFICIAL_MANIFEST_PATH}
"""

COMPLETE_STATE_TEXT = """
Do not directly enter v0.6.0 implementation.
Do not directly run MT5.
Do not directly modify MQ5.
The next task boundary must be defined by ChatGPT.
"""


def fail(message: str) -> int:
    print("v0.6.0 implementation planning boundary self-test failed")
    print(message)
    return 1


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_v060_implementation_planning_boundary",
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
        "docs/CURRENT_TASK.md": COMPLETE_STATE_TEXT,
        "docs/HANDOFF_PROMPT.md": COMPLETE_STATE_TEXT,
        "docs/PROJECT_STATE.md": COMPLETE_STATE_TEXT,
    }


def assert_fails(validator, implementation_text: str | None, state_docs: dict[str, str], label: str) -> str:
    failures = validator.validate_texts(implementation_text, state_docs)
    if not failures:
        return f"{label}: expected failure, got PASS"
    return ""


def assert_passes(validator, implementation_text: str, state_docs: dict[str, str], label: str) -> str:
    failures = validator.validate_texts(implementation_text, state_docs)
    if failures:
        return f"{label}: expected PASS, got failures: {failures}"
    return ""


def test_missing_boundary_content(validator) -> str:
    return assert_fails(
        validator,
        None,
        complete_state_docs(),
        "missing implementation planning boundary content",
    )


def test_missing_boundary_marker(validator) -> str:
    text = COMPLETE_IMPLEMENTATION_TEXT.replace("v0.6.0 implementation planning boundary", "next phase plan")
    text = text.replace("v0.6.0 Implementation Planning Boundary", "Next Phase Plan")
    return assert_fails(
        validator,
        text,
        complete_state_docs(),
        "missing implementation planning boundary marker",
    )


def test_missing_chatgpt_authorization(validator) -> str:
    text = COMPLETE_IMPLEMENTATION_TEXT.replace(
        "Any future v0.6.0 implementation task must be separately authorized by ChatGPT.\n",
        "",
    )
    return assert_fails(
        validator,
        text,
        complete_state_docs(),
        "missing ChatGPT separate authorization",
    )


def test_missing_no_live_real_profitability(validator) -> str:
    text = COMPLETE_IMPLEMENTATION_TEXT.replace(
        "Future tasks must preserve no live trading readiness, no real trading availability, and no profitability claims.\n",
        "",
    )
    return assert_fails(
        validator,
        text,
        complete_state_docs(),
        "missing no-live / no-real / no-profitability claims",
    )


def test_missing_default_safety_boundary(validator) -> str:
    text = COMPLETE_IMPLEMENTATION_TEXT.replace("Every future implementation task must default to no MT5 run.\n", "")
    text = text.replace("Every future implementation task must default to no MQ5 modification.\n", "")
    text = text.replace("Every future implementation task must default to no external evidence copying.\n", "")
    return assert_fails(
        validator,
        text,
        complete_state_docs(),
        "missing default no MT5 / no MQ5 / no evidence copy boundary",
    )


def test_direct_v060_implementation_fails(validator) -> str:
    state_docs = complete_state_docs()
    state_docs["docs/CURRENT_TASK.md"] += "\nNext step: v0.6.0 implementation\n"
    return assert_fails(
        validator,
        COMPLETE_IMPLEMENTATION_TEXT,
        state_docs,
        "direct v0.6.0 implementation next step",
    )


def test_complete_required_text_passes(validator) -> str:
    return assert_passes(
        validator,
        COMPLETE_IMPLEMENTATION_TEXT,
        complete_state_docs(),
        "complete implementation planning boundary policy text",
    )


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")

    validator = load_validator_module()
    tests = [
        test_missing_boundary_content,
        test_missing_boundary_marker,
        test_missing_chatgpt_authorization,
        test_missing_no_live_real_profitability,
        test_missing_default_safety_boundary,
        test_direct_v060_implementation_fails,
        test_complete_required_text_passes,
    ]

    for test in tests:
        error = test(validator)
        if error:
            return fail(error)

    print("v0.6.0 implementation planning boundary self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
