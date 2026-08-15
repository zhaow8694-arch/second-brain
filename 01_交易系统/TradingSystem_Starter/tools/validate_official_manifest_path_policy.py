#!/usr/bin/env python3
"""Validate an official manifest filename/path against the defined policy.

Rules (from docs/EVIDENCE_ARCHIVE_AND_MANIFEST.md):
  - official manifest directory: backtest/reports/manifests/
  - manifest filename: {taskId}_{evidenceSetId}_manifest.json
  - taskId: TASK-\\d+
  - evidenceSetId: ASCII safe characters only (a-zA-Z0-9 hyphen underscore dot)
  - no spaces in evidenceSetId
  - no Chinese characters in manifest filename
  - no absolute paths
  - no path traversal (..)
  - no overwriting existing manifest
  - does NOT create the manifest directory
"""

from pathlib import Path
import argparse
import re
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
PASS_TEXT = "Official manifest path policy validation passed"
FAIL_TEXT = "Official manifest path policy validation failed"

OFFICIAL_MANIFESTS_DIR = Path("backtest") / "reports" / "manifests"
TASK_ID_PATTERN = re.compile(r"^TASK-\d+$")
EVIDENCE_SET_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")
MANIFEST_FILENAME_PATTERN = re.compile(
    r"^(TASK-\d+)_([a-zA-Z0-9_.-]+)_manifest\.json$"
)
CHINESE_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
PATH_TRAVERSAL_PATTERN = re.compile(r"(?:^|[/\\])\.\.[/\\]")


def validate_manifest_path(manifest_rel_path_str, check_overwrite=True, root_dir=None):
    issues = []
    manifest_path = Path(manifest_rel_path_str)

    if manifest_path.is_absolute():
        issues.append("absolute path not allowed")
        return issues

    path_str = manifest_path.as_posix()

    if PATH_TRAVERSAL_PATTERN.search(path_str):
        issues.append("path traversal not allowed")

    if CHINESE_CHAR_PATTERN.search(manifest_path.name):
        issues.append("Chinese characters not allowed in manifest filename")

    dir_part = manifest_path.parent
    official_str = OFFICIAL_MANIFESTS_DIR.as_posix()
    dir_str = dir_part.as_posix()

    if dir_str != official_str:
        issues.append(
            f"manifest directory must be '{official_str}', got '{dir_str}'"
        )

    filename = manifest_path.name
    match = MANIFEST_FILENAME_PATTERN.match(filename)
    if not match:
        issues.append(
            f"filename must match {{taskId}}_{{evidenceSetId}}_manifest.json, "
            f"got '{filename}'"
        )
    else:
        task_id = match.group(1)
        evidence_set_id = match.group(2)

        if not TASK_ID_PATTERN.match(task_id):
            issues.append(f"invalid taskId format: '{task_id}'")

        if " " in evidence_set_id:
            issues.append(f"evidenceSetId must not contain spaces: '{evidence_set_id}'")

        if not EVIDENCE_SET_ID_PATTERN.match(evidence_set_id):
            issues.append(
                f"evidenceSetId contains invalid characters: '{evidence_set_id}'"
            )

    if check_overwrite:
        base = root_dir if root_dir is not None else ROOT_DIR
        full_target = base / manifest_path
        if full_target.exists():
            issues.append(f"target manifest already exists: '{manifest_rel_path_str}'")

    return issues


def main():
    parser = argparse.ArgumentParser(
        description="Validate an official manifest filename/path against policy."
    )
    parser.add_argument(
        "--manifest-path",
        required=True,
        help="Relative path of the manifest (e.g. backtest/reports/manifests/TASK-099_example_manifest.json)",
    )
    parser.add_argument(
        "--no-check-overwrite",
        action="store_true",
        help="Skip checking if manifest already exists.",
    )
    args = parser.parse_args()

    issues = validate_manifest_path(
        args.manifest_path,
        check_overwrite=not args.no_check_overwrite,
    )

    if issues:
        print(FAIL_TEXT)
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print(PASS_TEXT)
        sys.exit(0)


if __name__ == "__main__":
    main()
