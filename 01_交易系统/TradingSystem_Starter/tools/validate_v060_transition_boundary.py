#!/usr/bin/env python3
"""Validate the v0.6.0 transition boundary policy.

The check is read-only. It validates the v0.6.0 transition boundary together
with the later workflow simplification boundary overlay, without modifying any
repository files.
"""

from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
V060_BOUNDARY_PATH = ROOT_DIR / "docs" / "V060_TRANSITION_BOUNDARY.md"
WORKFLOW_BOUNDARY_PATH = ROOT_DIR / "docs" / "WORKFLOW_SIMPLIFICATION_BOUNDARY.md"
PROJECT_STATE_DOCS = (
    ROOT_DIR / "docs" / "CURRENT_TASK.md",
    ROOT_DIR / "docs" / "HANDOFF_PROMPT.md",
    ROOT_DIR / "docs" / "PROJECT_STATE.md",
)

PASS_TEXT = "v0.6.0 transition boundary validator PASS"
FAIL_TEXT = "v0.6.0 transition boundary validator FAIL"

NEGATING_TERMS = (
    "do not",
    "does not",
    "must not",
    "not ",
    "no ",
    "separately authorized",
    "separately and explicitly authorized",
    "future chatgpt task",
    "future task",
    "不得",
    "不要",
    "不代表",
    "不授权",
    "未授权",
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
    for raw_line in text.splitlines():
        line = normalize(raw_line.strip())
        if "v0.6.0 implementation" not in line:
            continue
        if "v0.6.0 implementation planning" in line:
            continue
        if line.startswith("authorize v0.6.0 implementation:"):
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


def validate_boundary_texts(
    v060_boundary_text: str | None,
    workflow_boundary_text: str | None,
) -> list[str]:
    failures: list[str] = []
    if not v060_boundary_text or not v060_boundary_text.strip():
        return ["missing docs/V060_TRANSITION_BOUNDARY.md content"]

    workflow_text = workflow_boundary_text or ""
    combined_text = f"{v060_boundary_text}\n{workflow_text}"

    require_any(
        failures,
        "efficient mode / workflow simplification marker",
        combined_text,
        ("workflow simplification", "efficient workflow mode", "高效模式"),
    )
    require_all(
        failures,
        "GPT / Codex / Trae role boundary",
        combined_text,
        ("GPT", "Codex", "Trae"),
    )
    require_any(
        failures,
        "Trae instruction compression rule",
        combined_text,
        ("Trae instructions must be compressed", "Trae 指令压缩", "Trae instruction compression"),
    )
    require_any(
        failures,
        "fixed tag completion / audit stable tag completion record",
        combined_text,
        (
            "tag completion",
            "audit stable tag completion",
            "stable tag completion",
        ),
    )
    require_any(
        failures,
        "no direct v0.6.0 implementation rule",
        v060_boundary_text,
        ("Do not directly enter v0.6.0 implementation", "不直接进入 v0.6.0 implementation"),
    )

    if directly_authorizes_v060_implementation(combined_text):
        failures.append("boundary directly authorizes v0.6.0 implementation")

    return failures


def validate_project_state_doc_text(name: str, text: str | None) -> list[str]:
    failures: list[str] = []
    if not text or not text.strip():
        return [f"{name}: missing project state doc content"]

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
    v060_boundary_text: str | None,
    workflow_boundary_text: str | None,
    project_state_texts: dict[str, str | None],
) -> list[str]:
    failures = validate_boundary_texts(v060_boundary_text, workflow_boundary_text)
    for name, text in project_state_texts.items():
        failures.extend(validate_project_state_doc_text(name, text))
    return failures


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_repository_texts() -> tuple[str | None, str | None, dict[str, str | None]]:
    state_texts = {
        str(path.relative_to(ROOT_DIR)).replace("\\", "/"): read_text(path)
        for path in PROJECT_STATE_DOCS
    }
    return read_text(V060_BOUNDARY_PATH), read_text(WORKFLOW_BOUNDARY_PATH), state_texts


def main() -> int:
    v060_text, workflow_text, state_texts = load_repository_texts()
    failures = validate_texts(v060_text, workflow_text, state_texts)

    if failures:
        print(FAIL_TEXT)
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
