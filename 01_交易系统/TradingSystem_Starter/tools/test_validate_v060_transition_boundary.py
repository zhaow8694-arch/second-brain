#!/usr/bin/env python3
"""Self-test for the v0.6.0 transition boundary validator."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_v060_transition_boundary.py"


COMPLETE_V060_TEXT = """
# v0.6.0 Transition Boundary

This document defines the v0.6.0 transition boundary.
Any v0.6.0 implementation task must be separately authorized by a future ChatGPT task.
Codex must not independently enter v0.6.0 implementation.
Trae must not independently trigger v0.6.0 implementation.
The readiness tag completion is fixed by v0.5.26-v060-transition-boundary-definition-readiness-tag-completion.
Do not directly enter v0.6.0 implementation.
"""

COMPLETE_WORKFLOW_TEXT = """
workflow simplification and efficient workflow mode are active.
GPT defines task boundaries.
Codex modifies only allowed files.
Trae reviews and validates.
Trae instructions must be compressed.
The prior tag completion / audit stable tag completion chain is closed.
"""

COMPLETE_STATE_TEXT = """
Do not directly enter v0.6.0 implementation.
This state does not authorize MT5 run.
This state does not authorize MQ5 modification.
The next task boundary must be defined by ChatGPT.
"""


def fail(message: str) -> int:
    print("v0.6.0 transition boundary self-test failed")
    print(message)
    return 1


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_v060_transition_boundary",
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


def assert_fails(
    validator,
    v060_text: str | None,
    workflow_text: str | None,
    state_docs: dict[str, str],
    label: str,
) -> str:
    failures = validator.validate_texts(v060_text, workflow_text, state_docs)
    if not failures:
        return f"{label}: expected failure, got PASS"
    return ""


def assert_passes(
    validator,
    v060_text: str,
    workflow_text: str,
    state_docs: dict[str, str],
    label: str,
) -> str:
    failures = validator.validate_texts(v060_text, workflow_text, state_docs)
    if failures:
        return f"{label}: expected PASS, got failures: {failures}"
    return ""


def test_missing_boundary_file_content(validator) -> str:
    return assert_fails(
        validator,
        None,
        COMPLETE_WORKFLOW_TEXT,
        complete_state_docs(),
        "missing V060 boundary content",
    )


def test_incomplete_boundary_content(validator) -> str:
    return assert_fails(
        validator,
        "# v0.6.0 Transition Boundary\n",
        COMPLETE_WORKFLOW_TEXT,
        complete_state_docs(),
        "incomplete V060 boundary content",
    )


def test_missing_workflow_context(validator) -> str:
    return assert_fails(
        validator,
        COMPLETE_V060_TEXT,
        "",
        complete_state_docs(),
        "missing workflow simplification context",
    )


def test_forbidden_direct_implementation(validator) -> str:
    state_docs = complete_state_docs()
    state_docs["docs/CURRENT_TASK.md"] += "\nNext step: v0.6.0 implementation\n"
    return assert_fails(
        validator,
        COMPLETE_V060_TEXT,
        COMPLETE_WORKFLOW_TEXT,
        state_docs,
        "direct v0.6.0 implementation next step",
    )


def test_complete_required_text_passes(validator) -> str:
    return assert_passes(
        validator,
        COMPLETE_V060_TEXT,
        COMPLETE_WORKFLOW_TEXT,
        complete_state_docs(),
        "complete v0.6.0 transition boundary policy text",
    )


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")

    validator = load_validator_module()
    tests = [
        test_missing_boundary_file_content,
        test_incomplete_boundary_content,
        test_missing_workflow_context,
        test_forbidden_direct_implementation,
        test_complete_required_text_passes,
    ]

    for test in tests:
        error = test(validator)
        if error:
            return fail(error)

    print("v0.6.0 transition boundary self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
