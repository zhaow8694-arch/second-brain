#!/usr/bin/env python3
"""Self-test for the workflow simplification policy validator."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_workflow_simplification_policy.py"


COMPLETE_WORKFLOW_TEXT = """
# Workflow Simplification Boundary

This document defines workflow simplification and efficient workflow mode.

GPT defines task boundaries.
Codex modifies only allowed files.
Trae reviews, validates, commits, tags, and audits.
Trae instructions must be compressed and focused.

Future validation should use tools/run_release_validation_bundle.py by default.

Do not continue infinite chains such as tag completion audit stable tag completion audit.
Do not redefine a boundary that has already been fixed by a stable tag.
Do not reuse old TASK-DOC ids.
Do not directly enter v0.6.0 implementation.

This boundary does not authorize MT5 execution.
This boundary does not authorize MQ5 modification.
This boundary does not authorize new manifest creation.
This boundary does not authorize external evidence copying.
"""

COMPLETE_STATE_TEXT = """
workflow simplification boundary recorded.
Do not directly enter v0.6.0 implementation.
This state does not authorize MT5 run.
This state does not authorize MQ5 modification.
The next task boundary must be defined by ChatGPT.
"""


def fail(message: str) -> int:
    print("Workflow simplification policy self-test failed")
    print(message)
    return 1


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_workflow_simplification_policy",
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


def assert_fails(validator, workflow_text: str | None, state_docs: dict[str, str], label: str) -> str:
    failures = validator.validate_texts(workflow_text, state_docs)
    if not failures:
        return f"{label}: expected failure, got PASS"
    return ""


def assert_passes(validator, workflow_text: str, state_docs: dict[str, str], label: str) -> str:
    failures = validator.validate_texts(workflow_text, state_docs)
    if failures:
        return f"{label}: expected PASS, got failures: {failures}"
    return ""


def test_missing_workflow_content(validator) -> str:
    return assert_fails(
        validator,
        "",
        complete_state_docs(),
        "missing workflow boundary content",
    )


def test_missing_role_boundary(validator) -> str:
    workflow_text = COMPLETE_WORKFLOW_TEXT.replace("GPT defines task boundaries.\n", "")
    workflow_text = workflow_text.replace("Codex modifies only allowed files.\n", "")
    workflow_text = workflow_text.replace("Trae reviews, validates, commits, tags, and audits.\n", "")
    return assert_fails(
        validator,
        workflow_text,
        complete_state_docs(),
        "missing GPT / Codex / Trae role boundary",
    )


def test_missing_trae_compression_rule(validator) -> str:
    workflow_text = COMPLETE_WORKFLOW_TEXT.replace("Trae instructions must be compressed and focused.\n", "")
    return assert_fails(
        validator,
        workflow_text,
        complete_state_docs(),
        "missing Trae compression rule",
    )


def test_missing_release_bundle_rule(validator) -> str:
    workflow_text = COMPLETE_WORKFLOW_TEXT.replace(
        "Future validation should use tools/run_release_validation_bundle.py by default.\n",
        "",
    )
    return assert_fails(
        validator,
        workflow_text,
        complete_state_docs(),
        "missing release validation bundle rule",
    )


def test_direct_v060_implementation_fails(validator) -> str:
    state_docs = complete_state_docs()
    state_docs["docs/CURRENT_TASK.md"] += "\nNext step: v0.6.0 implementation\n"
    return assert_fails(
        validator,
        COMPLETE_WORKFLOW_TEXT,
        state_docs,
        "direct v0.6.0 implementation next step",
    )


def test_complete_required_text_passes(validator) -> str:
    return assert_passes(
        validator,
        COMPLETE_WORKFLOW_TEXT,
        complete_state_docs(),
        "complete workflow policy text",
    )


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")

    validator = load_validator_module()
    tests = [
        test_missing_workflow_content,
        test_missing_role_boundary,
        test_missing_trae_compression_rule,
        test_missing_release_bundle_rule,
        test_direct_v060_implementation_fails,
        test_complete_required_text_passes,
    ]

    for test in tests:
        error = test(validator)
        if error:
            return fail(error)

    print("Workflow simplification policy self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
