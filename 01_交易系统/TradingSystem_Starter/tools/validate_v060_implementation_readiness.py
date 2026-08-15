#!/usr/bin/env python3
"""Validate v0.6.0 implementation readiness state.

This read-only validator checks that transition, planning, implementation
boundary, workflow simplification, and project-state validation gates are all
recorded before any future v0.6.0 implementation task is authorized.
"""

from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_STATE_DOCS = (
    ROOT_DIR / "docs" / "CURRENT_TASK.md",
    ROOT_DIR / "docs" / "HANDOFF_PROMPT.md",
    ROOT_DIR / "docs" / "PROJECT_STATE.md",
)
REQUIRED_EXISTING_FILES = (
    "docs/V060_TRANSITION_BOUNDARY.md",
    "docs/V060_IMPLEMENTATION_PLANNING_BOUNDARY.md",
    "docs/WORKFLOW_SIMPLIFICATION_BOUNDARY.md",
    "tools/validate_project_state_docs.py",
    "tools/validate_workflow_simplification_policy.py",
    "tools/validate_v060_transition_boundary.py",
    "tools/validate_v060_implementation_planning_boundary.py",
    "tools/validate_v060_implementation_boundary.py",
    "tools/run_release_validation_bundle.py",
)

PASS_TEXT = "v0.6.0 implementation readiness validator PASS"
FAIL_TEXT = "v0.6.0 implementation readiness validator FAIL"

SECTION_HEADING = "## TASK-DOC-224 prepare v0.6.0 implementation readiness"

SECTION_MARKERS = (
    SECTION_HEADING,
    "current HEAD is 78437d8 TASK-DOC-223 define v0.6.0 implementation boundary",
    "current phase remains v0.5.0",
    "current stable tag remains v0.5.35-v060-implementation-planning-boundary-tag-completion-audit-stable-tag-completion-audit",
    "workflow simplification is completed and remains active",
    "docs/V060_TRANSITION_BOUNDARY.md exists and remains unchanged",
    "docs/V060_IMPLEMENTATION_PLANNING_BOUNDARY.md exists and remains unchanged",
    "docs/EVIDENCE_ARCHIVE_AND_MANIFEST.md remains unchanged",
    "v0.6.0 transition boundary validator is ready",
    "v0.6.0 implementation planning boundary validator is ready",
    "v0.6.0 implementation boundary validator is ready",
    "workflow simplification policy validator is ready",
    "project state docs validator is ready",
    "release validation bundle includes workflow simplification, project state, transition boundary, implementation planning boundary, and implementation boundary validators",
    "release validation bundle baseline before this task was PASS 10/10",
    "tools/validate_v060_implementation_readiness.py was created as a read-only validator",
    "tools/run_release_validation_bundle.py was integrated with the v0.6.0 implementation readiness validator",
    "v0.6.0 implementation readiness is a readiness gate only",
    "current engineering gap: none",
    "current safety boundary gap: none",
    "current manifest gap: none",
    "workspace should be clean or contain only pre-existing untracked files after this task",
    "do not directly enter TASK-225",
    "do not directly enter v0.6.0 implementation",
    "the next task must be explicitly issued by ChatGPT",
)

SAFETY_MARKERS = (
    "this task does not enter v0.6.0 implementation",
    "this task does not run MT5",
    "this task does not modify MQ5",
    "this task does not create a new manifest",
    "this task does not create a fixture",
    "this task does not copy external evidence",
    "this task does not enter real trading",
    "this task does not do profitability optimization",
)

NEGATING_TERMS = (
    "do not",
    "does not",
    "not ",
    "no ",
    "readiness",
    "gate",
    "boundary",
    "must be explicitly issued",
)


def normalize(text: str) -> str:
    return text.lower()


def contains(text: str, marker: str) -> bool:
    return marker.lower() in normalize(text)


def extract_section(text: str) -> str | None:
    start = text.find(SECTION_HEADING)
    if start == -1:
        return None
    next_heading = text.find("## ", start + len(SECTION_HEADING))
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def directly_authorizes_v060_implementation(text: str) -> bool:
    for raw_line in text.splitlines():
        line = normalize(raw_line.strip())
        if "v0.6.0 implementation" not in line:
            continue
        if any(term in line for term in NEGATING_TERMS):
            continue
        if any(marker in line for marker in ("next step", "next task", "enter", "start", "authorize")):
            return True
    return False


def validate_project_state_doc_text(name: str, text: str | None) -> list[str]:
    if not text or not text.strip():
        return [f"{name}: missing project state doc content"]
    section = extract_section(text)
    if section is None:
        return [f"{name}: missing TASK-DOC-224 readiness section"]

    failures: list[str] = []
    for marker in SECTION_MARKERS:
        if not contains(section, marker):
            failures.append(f"{name}: missing readiness marker: {marker}")
    for marker in SAFETY_MARKERS:
        if not contains(section, marker):
            failures.append(f"{name}: missing safety marker: {marker}")
    if directly_authorizes_v060_implementation(section):
        failures.append(f"{name}: directly authorizes v0.6.0 implementation")
    return failures


def validate_texts(
    project_state_texts: dict[str, str | None],
    existing_files: set[str],
    release_bundle_text: str | None,
) -> list[str]:
    failures: list[str] = []
    for required_file in REQUIRED_EXISTING_FILES:
        if required_file not in existing_files:
            failures.append(f"missing required file: {required_file}")

    if not release_bundle_text or "validate_v060_implementation_readiness.py" not in release_bundle_text:
        failures.append("release validation bundle does not include implementation readiness validator")

    for name, text in project_state_texts.items():
        failures.extend(validate_project_state_doc_text(name, text))
    return failures


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_repository_texts() -> tuple[dict[str, str | None], set[str], str | None]:
    state_texts = {
        str(path.relative_to(ROOT_DIR)).replace("\\", "/"): read_text(path)
        for path in PROJECT_STATE_DOCS
    }
    existing_files = {
        str(path.relative_to(ROOT_DIR)).replace("\\", "/")
        for path in (ROOT_DIR / "docs").glob("*.md")
    }
    existing_files.update(
        str(path.relative_to(ROOT_DIR)).replace("\\", "/")
        for path in (ROOT_DIR / "tools").glob("*.py")
    )
    release_bundle_text = read_text(ROOT_DIR / "tools" / "run_release_validation_bundle.py")
    return state_texts, existing_files, release_bundle_text


def main() -> int:
    project_state_texts, existing_files, release_bundle_text = load_repository_texts()
    failures = validate_texts(project_state_texts, existing_files, release_bundle_text)
    if failures:
        print(FAIL_TEXT)
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
