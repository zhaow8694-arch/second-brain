#!/usr/bin/env python3
"""Validate the v0.6.0 implementation planning boundary policy.

This validator is read-only. It checks that the implementation planning
boundary remains a planning gate only, and that project state docs keep the
required no-implementation / no-MT5 / no-MQ5 safety boundary.
"""

from __future__ import annotations

from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
IMPLEMENTATION_BOUNDARY_PATH = (
    ROOT_DIR / "docs" / "V060_IMPLEMENTATION_PLANNING_BOUNDARY.md"
)
PROJECT_STATE_DOCS = (
    ROOT_DIR / "docs" / "CURRENT_TASK.md",
    ROOT_DIR / "docs" / "HANDOFF_PROMPT.md",
    ROOT_DIR / "docs" / "PROJECT_STATE.md",
)
OFFICIAL_MANIFEST_PATH = (
    "backtest/reports/manifests/"
    "TASK-139_external-mt5-eurusd-m5-20240101-20240131-no-trade_manifest.json"
)

PASS_TEXT = "v0.6.0 implementation planning boundary validator PASS"
FAIL_TEXT = "v0.6.0 implementation planning boundary validator FAIL"

NEGATING_TERMS = (
    "do not",
    "does not",
    "must not",
    "not ",
    "no ",
    "separately authorized",
    "future chatgpt task",
    "future task",
    "planning",
    "boundary",
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
        if "any future v0.6.0 implementation task" in line:
            continue
        if any(term in line for term in NEGATING_TERMS):
            continue
        if any(
            marker in line
            for marker in (
                "next step",
                "next task",
                "authorize",
                "enabled",
            )
        ):
            return True
    return False


def validate_implementation_boundary_text(text: str | None) -> list[str]:
    failures: list[str] = []
    if not text or not text.strip():
        return ["missing docs/V060_IMPLEMENTATION_PLANNING_BOUNDARY.md content"]

    require_any(
        failures,
        "v0.6.0 implementation planning boundary marker",
        text,
        ("v0.6.0 implementation planning boundary",),
    )
    require_any(
        failures,
        "current phase remains v0.5.0 marker",
        text,
        ("current phase remains v0.5.0", "褰撳墠闃舵浠嶄负 v0.5.0"),
    )
    require_any(
        failures,
        "planning is not implementation marker",
        text,
        (
            "does not authorize v0.6.0 implementation",
            "does not mean v0.6.0 has started",
            "涓嶄唬琛?v0.6.0 implementation",
        ),
    )
    require_any(
        failures,
        "ChatGPT separate authorization marker",
        text,
        (
            "must be separately authorized by ChatGPT",
            "separately authorized by ChatGPT",
            "姣忎釜 implementation task 蹇呴』鐢?ChatGPT",
        ),
    )
    require_any(
        failures,
        "default no MT5 run marker",
        text,
        ("no MT5 run", "running MT5", "涓嶈繍琛?MT5"),
    )
    require_any(
        failures,
        "default no MQ5 modification marker",
        text,
        ("no MQ5 modification", "modifying MQ5", "涓嶄慨鏀?MQ5"),
    )
    require_any(
        failures,
        "default no external evidence copy marker",
        text,
        ("no external evidence copying", "copying external evidence", "涓嶅鍒?external evidence"),
    )
    require_any(
        failures,
        "default no new official manifest marker",
        text,
        ("no new official manifest creation", "creating a new manifest", "涓嶅垱寤烘柊鐨?official manifest"),
    )
    require_all(
        failures,
        "no-live-trading / no-real-trading / no-profitability markers",
        text,
        (
            "live trading readiness",
            "real trading availability",
            "profitability",
        ),
    )
    require_any(
        failures,
        "metadata-only evidence handling marker",
        text,
        ("metadata-only evidence handling",),
    )
    require_any(
        failures,
        "risk-first policy marker",
        text,
        ("risk-first policy",),
    )
    require_any(
        failures,
        "explicit authorization boundaries marker",
        text,
        ("explicit authorization boundaries",),
    )
    require_any(
        failures,
        "official manifest path marker",
        text,
        (OFFICIAL_MANIFEST_PATH,),
    )

    if directly_authorizes_v060_implementation(text):
        failures.append("implementation planning boundary directly authorizes v0.6.0 implementation")

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
        ("do not directly run MT5", "no MT5 run", "does not authorize MT5", "涓嶈鐩存帴杩愯 MT5"),
    )
    require_any(
        failures,
        f"{name}: no direct MQ5 modification marker",
        text,
        ("do not directly modify MQ5", "does not authorize MQ5", "涓嶈鐩存帴淇敼 MQ5"),
    )
    require_any(
        failures,
        f"{name}: ChatGPT next boundary marker",
        text,
        (
            "the next task boundary must be defined by ChatGPT",
            "must be defined by ChatGPT",
            "蹇呴』鍏堢敱 ChatGPT 鍒跺畾涓嬩竴浠诲姟杈圭晫",
        ),
    )

    if directly_authorizes_v060_implementation(text):
        failures.append(f"{name}: next step directly authorizes v0.6.0 implementation")

    return failures


def validate_texts(
    implementation_boundary_text: str | None,
    project_state_texts: dict[str, str | None],
) -> list[str]:
    failures = validate_implementation_boundary_text(implementation_boundary_text)
    for name, text in project_state_texts.items():
        failures.extend(validate_project_state_doc_text(name, text))
    return failures


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_repository_texts() -> tuple[str | None, dict[str, str | None]]:
    state_texts = {
        str(path.relative_to(ROOT_DIR)).replace("\\", "/"): read_text(path)
        for path in PROJECT_STATE_DOCS
    }
    return read_text(IMPLEMENTATION_BOUNDARY_PATH), state_texts


def main() -> int:
    implementation_text, state_texts = load_repository_texts()
    failures = validate_texts(implementation_text, state_texts)

    if failures:
        print(FAIL_TEXT)
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
