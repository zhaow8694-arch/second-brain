#!/usr/bin/env python3
"""Self-test for the v0.6.0 implementation readiness validator."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT_DIR / "tools" / "validate_v060_implementation_readiness.py"


COMPLETE_DOC_TEXT = """
## TASK-DOC-224 prepare v0.6.0 implementation readiness

- current HEAD is 78437d8 TASK-DOC-223 define v0.6.0 implementation boundary
- current phase remains v0.5.0
- current stable tag remains v0.5.35-v060-implementation-planning-boundary-tag-completion-audit-stable-tag-completion-audit
- workflow simplification is completed and remains active
- docs/V060_TRANSITION_BOUNDARY.md exists and remains unchanged
- docs/V060_IMPLEMENTATION_PLANNING_BOUNDARY.md exists and remains unchanged
- docs/EVIDENCE_ARCHIVE_AND_MANIFEST.md remains unchanged
- v0.6.0 transition boundary validator is ready
- v0.6.0 implementation planning boundary validator is ready
- v0.6.0 implementation boundary validator is ready
- workflow simplification policy validator is ready
- project state docs validator is ready
- release validation bundle includes workflow simplification, project state, transition boundary, implementation planning boundary, and implementation boundary validators
- release validation bundle baseline before this task was PASS 10/10
- tools/validate_v060_implementation_readiness.py was created as a read-only validator
- tools/run_release_validation_bundle.py was integrated with the v0.6.0 implementation readiness validator
- v0.6.0 implementation readiness is a readiness gate only
- this task does not enter v0.6.0 implementation
- this task does not run MT5
- this task does not modify MQ5
- this task does not create a new manifest
- this task does not create a fixture
- this task does not copy external evidence
- this task does not enter real trading
- this task does not do profitability optimization
- current engineering gap: none
- current safety boundary gap: none
- current manifest gap: none
- workspace should be clean or contain only pre-existing untracked files after this task
- do not directly enter TASK-225
- do not directly enter v0.6.0 implementation
- the next task must be explicitly issued by ChatGPT
"""

COMPLETE_FILES = {
    "docs/V060_TRANSITION_BOUNDARY.md",
    "docs/V060_IMPLEMENTATION_PLANNING_BOUNDARY.md",
    "docs/WORKFLOW_SIMPLIFICATION_BOUNDARY.md",
    "tools/validate_project_state_docs.py",
    "tools/validate_workflow_simplification_policy.py",
    "tools/validate_v060_transition_boundary.py",
    "tools/validate_v060_implementation_planning_boundary.py",
    "tools/validate_v060_implementation_boundary.py",
    "tools/run_release_validation_bundle.py",
}

COMPLETE_BUNDLE_TEXT = "tools/validate_v060_implementation_readiness.py"


def fail(message: str) -> int:
    print("v0.6.0 implementation readiness self-test failed")
    print(message)
    return 1


def load_validator_module():
    spec = importlib.util.spec_from_file_location(
        "validate_v060_implementation_readiness",
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


def assert_fails(
    validator,
    state_docs: dict[str, str | None],
    existing_files: set[str],
    bundle_text: str | None,
    label: str,
) -> str:
    failures = validator.validate_texts(state_docs, existing_files, bundle_text)
    if not failures:
        return f"{label}: expected failure, got PASS"
    return ""


def assert_passes(
    validator,
    state_docs: dict[str, str],
    existing_files: set[str],
    bundle_text: str,
    label: str,
) -> str:
    failures = validator.validate_texts(state_docs, existing_files, bundle_text)
    if failures:
        return f"{label}: expected PASS, got failures: {failures}"
    return ""


def test_missing_required_file(validator) -> str:
    files = set(COMPLETE_FILES)
    files.remove("tools/validate_v060_transition_boundary.py")
    return assert_fails(
        validator,
        complete_state_docs(),
        files,
        COMPLETE_BUNDLE_TEXT,
        "missing required validator file",
    )


def test_missing_bundle_integration(validator) -> str:
    return assert_fails(
        validator,
        complete_state_docs(),
        COMPLETE_FILES,
        "",
        "missing readiness validator bundle integration",
    )


def test_missing_readiness_section(validator) -> str:
    state_docs = complete_state_docs()
    state_docs["docs/CURRENT_TASK.md"] = ""
    return assert_fails(
        validator,
        state_docs,
        COMPLETE_FILES,
        COMPLETE_BUNDLE_TEXT,
        "missing readiness section",
    )


def test_missing_safety_marker(validator) -> str:
    state_docs = complete_state_docs()
    state_docs["docs/HANDOFF_PROMPT.md"] = state_docs["docs/HANDOFF_PROMPT.md"].replace(
        "- this task does not run MT5\n",
        "",
    )
    return assert_fails(
        validator,
        state_docs,
        COMPLETE_FILES,
        COMPLETE_BUNDLE_TEXT,
        "missing no MT5 marker",
    )


def test_direct_v060_implementation_fails(validator) -> str:
    state_docs = complete_state_docs()
    state_docs["docs/PROJECT_STATE.md"] += "\nNext step: start v0.6.0 implementation\n"
    return assert_fails(
        validator,
        state_docs,
        COMPLETE_FILES,
        COMPLETE_BUNDLE_TEXT,
        "direct v0.6.0 implementation next step",
    )


def test_complete_required_text_passes(validator) -> str:
    return assert_passes(
        validator,
        complete_state_docs(),
        COMPLETE_FILES,
        COMPLETE_BUNDLE_TEXT,
        "complete readiness state",
    )


def main() -> int:
    if not VALIDATOR_PATH.exists():
        return fail(f"validator script not found: {VALIDATOR_PATH}")

    validator = load_validator_module()
    tests = [
        test_missing_required_file,
        test_missing_bundle_integration,
        test_missing_readiness_section,
        test_missing_safety_marker,
        test_direct_v060_implementation_fails,
        test_complete_required_text_passes,
    ]

    for test in tests:
        error = test(validator)
        if error:
            return fail(error)

    print("v0.6.0 implementation readiness self-test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
