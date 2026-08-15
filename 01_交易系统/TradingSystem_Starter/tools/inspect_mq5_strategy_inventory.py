#!/usr/bin/env python3
"""Read-only MQ5 strategy inventory scanner.

The tool inventories MQ5/MQH source files before future implementation work.
It does not modify files, run MT5, create reports, create manifests, or copy
external evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MQ5_ROOT = ROOT_DIR / "MQ5"

SAFETY_NOTICE = "Inventory only; no MT5 run; no trading authorization."

SOURCE_EXTENSIONS = (".mq5", ".mqh")
INPUT_LINE_PATTERN = re.compile(r"^\s*(?:input|sinput)\b", re.IGNORECASE)

TRADING_KEYWORDS = (
    "CTrade",
    "OrderSend",
    "OrderSendAsync",
    "PositionOpen",
    "PositionClose",
    "OrderModify",
    "OrderClose",
    "Buy",
    "Sell",
)

LIFECYCLE_KEYWORDS = ("OnInit", "OnTick", "OnDeinit")


def normalize_root(path: str | Path) -> Path:
    root = Path(path)
    if not root.is_absolute():
        root = ROOT_DIR / root
    return root.resolve()


def read_source(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig", errors="replace")


def find_source_files(root: Path) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    return sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in SOURCE_EXTENSIONS
        ),
        key=lambda path: path.relative_to(root).as_posix().lower(),
    )


def count_input_parameter_lines(text: str) -> int:
    return sum(1 for line in text.splitlines() if INPUT_LINE_PATTERN.search(line))


def keyword_presence(text: str, keywords: tuple[str, ...]) -> dict[str, bool]:
    return {keyword: keyword in text for keyword in keywords}


def analyze_file(root: Path, path: Path) -> dict[str, Any]:
    text = read_source(path)
    trading_keywords = keyword_presence(text, TRADING_KEYWORDS)
    lifecycle = keyword_presence(text, LIFECYCLE_KEYWORDS)
    return {
        "path": path.relative_to(root).as_posix(),
        "extension": path.suffix.lower(),
        "inputParameterLines": count_input_parameter_lines(text),
        "hasInpEnableTrading": "InpEnableTrading" in text,
        "hasRiskManager": "RiskManager" in text,
        "hasSignalEngine": "SignalEngine" in text,
        "tradingKeywords": trading_keywords,
        "hasTradingKeywords": any(trading_keywords.values()),
        "lifecycle": lifecycle,
    }


def summarize(files: list[dict[str, Any]], root_exists: bool) -> dict[str, Any]:
    trading_keyword_file_counts = {
        keyword: sum(1 for file_info in files if file_info["tradingKeywords"][keyword])
        for keyword in TRADING_KEYWORDS
    }
    lifecycle_file_counts = {
        keyword: sum(1 for file_info in files if file_info["lifecycle"][keyword])
        for keyword in LIFECYCLE_KEYWORDS
    }
    return {
        "rootExists": root_exists,
        "totalFiles": len(files),
        "mq5Files": sum(1 for file_info in files if file_info["extension"] == ".mq5"),
        "mqhFiles": sum(1 for file_info in files if file_info["extension"] == ".mqh"),
        "inputParameterLines": sum(file_info["inputParameterLines"] for file_info in files),
        "filesWithInpEnableTrading": sum(1 for file_info in files if file_info["hasInpEnableTrading"]),
        "filesWithRiskManager": sum(1 for file_info in files if file_info["hasRiskManager"]),
        "filesWithSignalEngine": sum(1 for file_info in files if file_info["hasSignalEngine"]),
        "filesWithTradingKeywords": sum(1 for file_info in files if file_info["hasTradingKeywords"]),
        "tradingKeywordFileCounts": trading_keyword_file_counts,
        "lifecycleFileCounts": lifecycle_file_counts,
    }


def build_inventory(root: Path) -> dict[str, Any]:
    root_exists = root.exists() and root.is_dir()
    files = [analyze_file(root, path) for path in find_source_files(root)]
    summary = summarize(files, root_exists)
    return {
        "status": "PASS",
        "notice": SAFETY_NOTICE,
        "scannedRoot": str(root),
        "rootExists": root_exists,
        "fileCounts": {
            "mq5": summary["mq5Files"],
            "mqh": summary["mqhFiles"],
            "total": summary["totalFiles"],
        },
        "files": files,
        "summary": summary,
    }


def print_text_inventory(inventory: dict[str, Any]) -> None:
    summary = inventory["summary"]
    print("MQ5 strategy inventory PASS")
    print(SAFETY_NOTICE)
    print(f"scanned root: {inventory['scannedRoot']}")
    print(
        "summary: "
        f"mq5={summary['mq5Files']} "
        f"mqh={summary['mqhFiles']} "
        f"total={summary['totalFiles']} "
        f"inputParameterLines={summary['inputParameterLines']} "
        f"InpEnableTradingFiles={summary['filesWithInpEnableTrading']} "
        f"RiskManagerFiles={summary['filesWithRiskManager']} "
        f"SignalEngineFiles={summary['filesWithSignalEngine']} "
        f"TradingKeywordFiles={summary['filesWithTradingKeywords']}"
    )
    for file_info in inventory["files"]:
        lifecycle_hits = [
            name for name, present in file_info["lifecycle"].items() if present
        ]
        trading_hits = [
            name for name, present in file_info["tradingKeywords"].items() if present
        ]
        print(
            "- "
            f"{file_info['path']}: "
            f"inputs={file_info['inputParameterLines']} "
            f"InpEnableTrading={file_info['hasInpEnableTrading']} "
            f"RiskManager={file_info['hasRiskManager']} "
            f"SignalEngine={file_info['hasSignalEngine']} "
            f"tradingKeywords={','.join(trading_hits) if trading_hits else 'none'} "
            f"lifecycle={','.join(lifecycle_hits) if lifecycle_hits else 'none'}"
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only MQ5 strategy inventory scanner.",
    )
    parser.add_argument(
        "--mq5-root",
        default=str(DEFAULT_MQ5_ROOT),
        help="MQ5 source root to scan. Defaults to repository MQ5/.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit stable JSON output.",
    )
    parser.add_argument(
        "--fail-on-missing-root",
        action="store_true",
        help="Fail instead of returning an empty inventory when the root is missing.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = normalize_root(args.mq5_root)

    if args.fail_on_missing_root and not root.exists():
        failure = {
            "status": "FAIL",
            "notice": SAFETY_NOTICE,
            "scannedRoot": str(root),
            "rootExists": False,
            "errors": ["MQ5 root does not exist"],
        }
        if args.json:
            print(json.dumps(failure, indent=2, sort_keys=True))
        else:
            print("MQ5 strategy inventory FAIL")
            print(SAFETY_NOTICE)
            print(f"scanned root: {root}")
            print("error: MQ5 root does not exist")
        return 1

    inventory = build_inventory(root)
    if args.json:
        print(json.dumps(inventory, indent=2, sort_keys=True))
    else:
        print_text_inventory(inventory)
    return 0


if __name__ == "__main__":
    sys.exit(main())
