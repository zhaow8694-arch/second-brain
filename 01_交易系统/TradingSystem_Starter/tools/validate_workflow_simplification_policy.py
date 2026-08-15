#!/usr/bin/env python3
"""Validate the workflow simplification boundary docs.

This validator is intentionally read-only. It only reads the workflow
simplification boundary and project state docs, then reports whether the
required workflow policy markers are present.
"""

from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKFLOW_BOUNDARY_PATH = ROOT_DIR / "docs" / "WORKFLOW_SIMPLIFICATION_BOUNDARY.md"
PROJECT_STATE_DOCS = (
    ROOT_DIR / "docs" / "CURRENT_TASK.md",
    ROOT_DIR / "docs" / "HANDOFF_PROMPT.md",
    ROOT_DIR / "docs" / "PROJECT_STATE.md",
)

PASS_TEXT = "Workflow simplification policy validator PASS"
FAIL_TEXT = "Workflow simplification policy validator FAIL"

NEGATING_TERMS = (
    "do not",
    "does not",
    "must not",
    "not ",
    "no ",
    "不得",
    "不要",
    "不代表",
    "不授权",
    "未授权",
    "separately authorized",
    "future chatgpt task",
    "future task",
)


def normalize(text: str) -> str:
    return text.lower()


def has_any(text: str, terms: tuple[str, ...]) -> bool:
    lower = normalize(text)
    return any(term.lower() in lower for term in terms)


def has_all(text: str, terms: tuple[str, ...]) -> bool:
    lower = normalize(text)
    return all(term.lower() in lower for term in terms)


def require_any(failures: list[str], label: str, text: str, terms: tuple[str, ...]) -> None:
    if not has_any(text, terms):
        failures.append(f"missing {label}")


def require_all(failures: list[str], label: str, text: str, terms: tuple[str, ...]) -> None:
    if not has_all(text, terms):
        failures.append(f"missing {label}")


def directly_authorizes_v060_implementation(text: str) -> bool:
    """Return True when a line appears to set v0.6.0 implementation as next work."""

    for raw_line in text.splitlines():
        line = normalize(raw_line.strip())
        if "v0.6.0 implementation" not in line:
            continue
        if "v0.6.0 implementation planning" in line:
            continue
        if any(term in line for term in NEGATING_TERMS):
            continue
        if any(
            marker in line
            for marker in (
                "next step",
                "next task",
                "enter",
                "start",
                "authorize",
                "进入",
                "开启",
                "授权",
            )
        ):
            return True
    return False


def validate_workflow_boundary_text(text: str | None) -> list[str]:
    failures: list[str] = []
    if not text or not text.strip():
        return ["missing docs/WORKFLOW_SIMPLIFICATION_BOUNDARY.md content"]

    require_any(
        failures,
        "efficient mode / workflow simplification marker",
        text,
        ("workflow simplification", "efficient workflow mode", "高效模式"),
    )
    require_all(
        failures,
        "GPT / Codex / Trae role boundary",
        text,
        ("GPT", "Codex", "Trae"),
    )
    require_any(
        failures,
        "Trae instruction compression rule",
        text,
        ("Trae instructions must be compressed", "Trae 指令压缩", "Trae instruction compression"),
    )
    require_any(
        failures,
        "run_release_validation_bundle.py default validation rule",
        text,
        ("run_release_validation_bundle.py",),
    )
    require_any(
        failures,
        "no infinite tag completion / audit stable tag completion chain rule",
        text,
        (
            "Do not continue infinite chains",
            "tag completion audit stable tag completion audit",
            "no infinite tag completion",
        ),
    )
    require_any(
        failures,
        "no repeated fixed boundary definition rule",
        text,
        (
            "Do not redefine a boundary",
            "no repeated definition",
            "不再重复定义",
        ),
    )
    require_any(
        failures,
        "no old TASK-DOC id reuse rule",
        text,
        ("Do not reuse old TASK-DOC ids", "不再复用旧 TASK-DOC"),
    )
    require_any(
        failures,
        "no direct v0.6.0 implementation rule",
        text,
        ("Do not directly enter v0.6.0 implementation", "不直接进入 v0.6.0 implementation"),
    )
    require_any(
        failures,
        "no MT5 rule",
        text,
        ("run MT5", "MT5 execution", "不运行 MT5"),
    )
    require_any(
        failures,
        "no MQ5 modification rule",
        text,
        ("MQ5 modification", "不修改 MQ5"),
    )
    require_any(
        failures,
        "no new manifest rule",
        text,
        ("new manifest", "不创建新 manifest"),
    )
    require_any(
        failures,
        "no external evidence copy rule",
        text,
        ("external evidence copying", "external evidence copy", "不复制 external evidence"),
    )

    if directly_authorizes_v060_implementation(text):
        failures.append("workflow boundary directly authorizes v0.6.0 implementation")

    return failures


def validate_project_state_doc_text(name: str, text: str | None) -> list[str]:
    failures: list[str] = []
    if not text or not text.strip():
        return [f"{name}: missing project state doc content"]

    require_any(
        failures,
        f"{name}: workflow simplification boundary marker",
        text,
        ("workflow simplification boundary", "workflow simplification / reconciliation", "高效模式"),
    )
    require_any(
        failures,
        f"{name}: no direct v0.6.0 implementation marker",
        text,
        ("do not directly enter v0.6.0 implementation", "不要直接进入 v0.6.0 implementation"),
    )
    require_any(
        failures,
        f"{name}: no direct MT5 run marker",
        text,
        ("no MT5 run", "does not authorize MT5", "must not run MT5", "不要直接运行 MT5", "不运行 MT5"),
    )
    require_any(
        failures,
        f"{name}: no direct MQ5 modification marker",
        text,
        (
            "does not authorize MQ5",
            "must not modify MQ5",
            "do not directly modify MQ5",
            "不要直接修改 MQ5",
            "不修改 MQ5",
        ),
    )
    require_any(
        failures,
        f"{name}: ChatGPT next boundary marker",
        text,
        (
            "the next task boundary must be defined by ChatGPT",
            "must be defined by ChatGPT",
            "必须先由 ChatGPT 制定下一任务边界",
        ),
    )

    if directly_authorizes_v060_implementation(text):
        failures.append(f"{name}: next step directly authorizes v0.6.0 implementation")

    return failures


def validate_texts(
    workflow_boundary_text: str | None,
    project_state_texts: dict[str, str | None],
) -> list[str]:
    failures = validate_workflow_boundary_text(workflow_boundary_text)
    for name, text in project_state_texts.items():
        failures.extend(validate_project_state_doc_text(name, text))
    return failures


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_repository_texts() -> tuple[str | None, dict[str, str | None]]:
    workflow_text = read_text(WORKFLOW_BOUNDARY_PATH)
    state_texts = {
        str(path.relative_to(ROOT_DIR)).replace("\\", "/"): read_text(path)
        for path in PROJECT_STATE_DOCS
    }
    return workflow_text, state_texts


def main() -> int:
    workflow_text, state_texts = load_repository_texts()
    failures = validate_texts(workflow_text, state_texts)

    if failures:
        print(FAIL_TEXT)
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
