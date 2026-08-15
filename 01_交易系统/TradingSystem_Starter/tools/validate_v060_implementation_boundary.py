#!/usr/bin/env python3
"""Validate the v0.6.0 implementation boundary recorded in project state docs.

This check is read-only. It verifies that the current project state defines
only a planning and validation boundary for v0.6.0 implementation, without
authorizing MT5 runs, MQ5 edits, new manifests, evidence copying, live trading,
or profitability claims.
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
OFFICIAL_MANIFEST_PATH = (
    "backtest/reports/manifests/"
    "TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json"
)

PASS_TEXT = "v0.6.0 implementation boundary validator PASS"
FAIL_TEXT = "v0.6.0 implementation boundary validator FAIL"

REQUIRED_MARKERS = (
    "TASK-DOC-223 define v0.6.0 implementation boundary",
    "current phase remains v0.5.0",
    "current stable tag remains v0.5.35-v060-implementation-planning-boundary-tag-completion-audit-stable-tag-completion-audit",
    "v0.5.35-v060-implementation-planning-boundary-tag-completion-audit-stable-tag-completion-audit is fixed",
    "current engineering gap: none",
    "current safety boundary gap: none",
    "current manifest gap: none",
    "workflow simplification is completed",
    "v0.6.0 implementation boundary is defined only as a planning and validation boundary",
    "release validation bundle baseline before this task was PASS 9/9",
    "tools/validate_v060_implementation_boundary.py was created as a read-only validator",
    "tools/run_release_validation_bundle.py was integrated with the v0.6.0 implementation boundary validator",
    OFFICIAL_MANIFEST_PATH,
)

NEGATED_AUTHORIZATION_MARKERS = (
    "this task does not start v0.6.0 implementation",
    "this task does not authorize live trading readiness",
    "this task does not authorize real trading availability",
    "this task does not authorize profitability claims",
    "this task does not authorize real trading",
    "this task does not authorize MT5 run",
    "this task does not authorize MQ5 modification",
    "this task does not authorize new manifest creation",
    "this task does not authorize external evidence copying",
    "this task does not authorize official manifest modification",
    "do not directly enter TASK-224",
    "do not directly enter v0.6.0 implementation",
    "do not directly run MT5",
    "do not directly modify MQ5",
    "do not create a new manifest",
    "do not copy external evidence",
    "the next task must be explicitly issued by ChatGPT",
)

NEGATING_TERMS = (
    "do not",
    "does not",
    "not ",
    "no ",
    "planning",
    "boundary",
    "must be explicitly issued",
    "must be defined",
)

SECTION_HEADING = "## TASK-DOC-223 define v0.6.0 implementation boundary"
NEXT_HEADING_PREFIX = "## "


def normalize(text: str) -> str:
    return text.lower()


def has(text: str, marker: str) -> bool:
    return marker.lower() in normalize(text)


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


def extract_task_doc_223_section(text: str) -> str | None:
    marker = SECTION_HEADING
    start = text.find(marker)
    if start == -1:
        return None
    next_heading = text.find(NEXT_HEADING_PREFIX, start + len(marker))
    if next_heading == -1:
        return text[start:]
    return text[start:next_heading]


def validate_project_state_doc_text(name: str, text: str | None) -> list[str]:
    if not text or not text.strip():
        return [f"{name}: missing project state doc content"]

    failures: list[str] = []
    section = extract_task_doc_223_section(text)
    if section is None:
        return [f"{name}: missing TASK-DOC-223 implementation boundary section"]

    for marker in REQUIRED_MARKERS:
        if not has(section, marker):
            failures.append(f"{name}: missing marker: {marker}")
    for marker in NEGATED_AUTHORIZATION_MARKERS:
        if not has(section, marker):
            failures.append(f"{name}: missing safety marker: {marker}")

    if directly_authorizes_v060_implementation(section):
        failures.append(f"{name}: directly authorizes v0.6.0 implementation")
    return failures


def validate_texts(project_state_texts: dict[str, str | None]) -> list[str]:
    failures: list[str] = []
    for name, text in project_state_texts.items():
        failures.extend(validate_project_state_doc_text(name, text))
    return failures


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_repository_texts() -> dict[str, str | None]:
    return {
        str(path.relative_to(ROOT_DIR)).replace("\\", "/"): read_text(path)
        for path in PROJECT_STATE_DOCS
    }


def main() -> int:
    failures = validate_texts(load_repository_texts())
    if failures:
        print(FAIL_TEXT)
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
