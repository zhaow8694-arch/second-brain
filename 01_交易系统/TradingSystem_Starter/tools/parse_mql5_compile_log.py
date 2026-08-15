#!/usr/bin/env python3
"""Parse MQL5 MetaEditor compile log into JSON metadata (stdout-only)."""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
import sys


PASS_SAFETY_NOTES = [
    "parsed compile log is diagnostic metadata only",
    "not live trading readiness",
    "not real trading permission",
    "not profitability claim",
    "stdout-only parse; log must not be saved into repository unless separately authorized",
]

ENCODING_BOMS = (
    (b"\xef\xbb\xbf", "utf-8-sig"),
    (b"\xff\xfe", "utf-16-le"),
    (b"\xfe\xff", "utf-16-be"),
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Parse an MQL5 MetaEditor compile log into JSON metadata."
    )
    parser.add_argument("compile_log", help="Path to a compile log file.")
    parser.add_argument(
        "--exit-code",
        type=int,
        default=0,
        help="MetaEditor exit code associated with the compile attempt.",
    )
    parser.add_argument(
        "--quarantine-ex5-detected",
        action="store_true",
        help="Whether a quarantined .ex5 artifact was detected for this attempt.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser.parse_args()


def decode_compile_log_bytes(data: bytes) -> tuple[str, str]:
    for signature, encoding in ENCODING_BOMS:
        if data.startswith(signature):
            return data.decode(encoding, errors="replace"), encoding

    if b"\x00" in data[:200]:
        for encoding in ("utf-16-le", "utf-16-be"):
            decoded = data.decode(encoding, errors="replace")
            if "\x00" not in decoded[:200]:
                return decoded, encoding

    return data.decode("utf-8", errors="replace"), "utf-8"


def read_compile_log(path: str | Path) -> tuple[str, str]:
    log_path = Path(path)
    try:
        raw = log_path.read_bytes()
    except FileNotFoundError:
        raise ValueError(f"compile log not found: {path}") from None
    except OSError as error:
        raise ValueError(f"could not read compile log: {error}") from None
    return decode_compile_log_bytes(raw)


def extract_target_path(text: str) -> str | None:
    patterns = (
        r"Compiling\s+'([^']+)'",
        r"Compiling\s+\"([^\"]+)\"",
        r"Compile\s+([^:\r\n]+\.mq5)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_build(text: str) -> str | None:
    match = re.search(r"Build\s+(\d+)", text, re.IGNORECASE)
    return match.group(1) if match else None


def extract_error_warning_counts(text: str) -> tuple[int | str, int | str]:
    patterns = (
        r"Result:\s*(\d+)\s+errors?,\s*(\d+)\s+warnings?",
        r"\b(\d+)\s+errors?,\s*(\d+)\s+warnings?",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1)), int(match.group(2))
    return "UNKNOWN", "UNKNOWN"


def extract_diagnostics(text: str, *, limit: int = 20) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for line in text.splitlines():
        normalized = line.strip()
        if not normalized:
            continue
        lowered = normalized.lower()
        if "error" in lowered and len(errors) < limit:
            errors.append(normalized)
        elif "warning" in lowered and len(warnings) < limit:
            warnings.append(normalized)
    return {"errors": errors, "warnings": warnings}


def classify_compile_result(
    exit_code: int,
    compile_log_text: str,
    *,
    quarantine_ex5_artifact_detected: bool = False,
) -> dict[str, object]:
    errors, warnings = extract_error_warning_counts(compile_log_text)
    if errors == "UNKNOWN" or warnings == "UNKNOWN":
        return {
            "compile_log_errors": errors,
            "compile_log_warnings": warnings,
            "compile_log_semantic_success": "unknown",
            "compile_result_classification": "unclassified",
            "metaeditor_exit_code_anomaly": False,
            "compile_success": False,
            "followup_required": True,
        }

    semantic_success = errors == 0
    if errors > 0:
        classification = "compile_errors_present"
        compile_success = False
        followup_required = True
        anomaly = False
    elif exit_code != 0 and semantic_success:
        if quarantine_ex5_artifact_detected:
            classification = "compiled_artifact_with_metaeditor_exit_code_anomaly"
        else:
            classification = "metaeditor_exit_code_anomaly_without_artifact"
        compile_success = False
        followup_required = True
        anomaly = True
    elif exit_code == 0 and semantic_success:
        if quarantine_ex5_artifact_detected:
            classification = "compile_artifact_detected_exit_success"
        else:
            classification = "compile_log_success_exit_success"
        compile_success = True
        followup_required = False
        anomaly = False
    else:
        classification = "unclassified"
        compile_success = False
        followup_required = True
        anomaly = False

    return {
        "compile_log_errors": errors,
        "compile_log_warnings": warnings,
        "compile_log_semantic_success": semantic_success,
        "compile_result_classification": classification,
        "metaeditor_exit_code_anomaly": anomaly,
        "compile_success": compile_success,
        "followup_required": followup_required,
    }


def parse_compile_log(
    text: str,
    *,
    encoding: str,
    exit_code: int = 0,
    quarantine_ex5_detected: bool = False,
    source_path: str | None = None,
) -> dict[str, object]:
    classification = classify_compile_result(
        exit_code,
        text,
        quarantine_ex5_artifact_detected=quarantine_ex5_detected,
    )
    diagnostics = extract_diagnostics(text)
    line_count = len(text.splitlines())

    payload = {
        "sourcePath": source_path,
        "encoding": encoding,
        "lineCount": line_count,
        "compileTarget": extract_target_path(text),
        "build": extract_build(text),
        "metaeditorExitCode": exit_code,
        "quarantineEx5Detected": quarantine_ex5_detected,
        "diagnosticSamples": diagnostics,
        "safetyNotes": PASS_SAFETY_NOTES,
    }
    payload.update(classification)
    return payload


def main():
    args = parse_args()
    try:
        text, encoding = read_compile_log(args.compile_log)
        payload = parse_compile_log(
            text,
            encoding=encoding,
            exit_code=args.exit_code,
            quarantine_ex5_detected=args.quarantine_ex5_detected,
            source_path=str(Path(args.compile_log)),
        )
    except ValueError as error:
        print(f"MQL5 compile log parser failed: {error}", file=sys.stderr)
        return 1

    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())