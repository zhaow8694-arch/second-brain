#!/usr/bin/env python3
"""Self-test the engineering toolchain checks CLI."""

from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap


ROOT_DIR = Path(__file__).resolve().parents[1]
TOOLCHAIN_SCRIPT = ROOT_DIR / "tools" / "run_engineering_toolchain_checks.py"
PASS_TEXT = "Engineering toolchain checks passed"
FAIL_TEXT = "Engineering toolchain checks failed"
SELF_PASS_TEXT = "Engineering toolchain self-test passed"
SELF_FAIL_TEXT = "Engineering toolchain self-test failed"
LIST_TEXT = "Engineering toolchain checks list"
JSON_LIST_NAME = "engineering_toolchain_checks"
JSON_LIST_MODE = "list"

PASS_LINES = [
    "[PASS] validate generated sample report",
    "[PASS] validate generated TASK-010 report",
    "[PASS] validate backtest runtime report validator self-test",
    "[PASS] validate runtime parser input samples",
    "[PASS] validate runtime parser input samples self-test",
    "[PASS] validate project state docs",
    "[PASS] validate project state docs self-test",
    "[PASS] validate MQ5 safety guardrails",
    "[PASS] validate MQ5 safety guardrails self-test",
    "[PASS] validate backtest set safety",
    "[PASS] validate backtest set safety self-test",
    "[PASS] validate Python tool safety",
    "[PASS] validate Python tool safety self-test",
    "[PASS] validate evidence manifest schema self-test",
    "[PASS] validate Strategy Tester HTML parser self-test",
    "[PASS] validate MT5 log no-trade parser self-test",
    "[PASS] validate evidence manifest generator self-test",
    "[PASS] validate official manifest path policy",
    "[PASS] validate official manifest path policy self-test",
]
PASS_PREFIX = "[PASS] "
EXPECTED_CHECK_NAMES = [line[len(PASS_PREFIX) :] for line in PASS_LINES]
LIST_LINES = [
    f"{index}. {name}" for index, name in enumerate(EXPECTED_CHECK_NAMES, start=1)
]


def combined_output(result):
    return ((result.stdout or "") + "\n" + (result.stderr or "")).strip()


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_toolchain(project_root, extra_args=None):
    args = [
        sys.executable,
        str(project_root / "tools" / "run_engineering_toolchain_checks.py"),
    ]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(
        args,
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )


def run_tool(project_root, script_name):
    return subprocess.run(
        [
            sys.executable,
            str(project_root / "tools" / script_name),
        ],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )


def copy_toolchain_only(project_root):
    tools_dir = project_root / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TOOLCHAIN_SCRIPT, tools_dir / "run_engineering_toolchain_checks.py")


def write_stub_script(path, output, returncode=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(
            f"""\
            import sys

            print({output!r})
            sys.exit({returncode})
            """
        ),
        encoding="utf-8",
    )


def collect_project_file_hashes(project_root):
    files = set()
    for pattern in (
        "mq5/**/*.mq5",
        "mq5/**/*.mqh",
        "backtest/sets/**/*.set",
        "backtest/reports/generated/**/*.md",
        "tools/*.py",
    ):
        files.update(
            path
            for path in project_root.glob(pattern)
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix != ".pyc"
        )

    for relative_name in (
        "docs/CURRENT_TASK.md",
        "docs/HANDOFF_PROMPT.md",
        "docs/PROJECT_STATE.md",
    ):
        path = project_root / relative_name
        if path.is_file():
            files.add(path)

    return {
        path.relative_to(project_root).as_posix(): file_sha256(path)
        for path in sorted(files)
    }


def engineering_toolchain_readonly_issues(project_root):
    before = collect_project_file_hashes(project_root)
    result = run_toolchain(project_root)
    output = combined_output(result)
    if result.returncode != 0 or PASS_TEXT not in output:
        return ["positive engineering toolchain check did not pass", output]

    after = collect_project_file_hashes(project_root)
    changed_files = [
        path
        for path in sorted(set(before) | set(after))
        if before.get(path) != after.get(path)
    ]
    if changed_files:
        return [
            "engineering toolchain modified project files",
            "\n".join(changed_files),
        ]

    return []


def create_toolchain_fixture(project_root, failing_script=None, failing_output="", failing_returncode=1):
    copy_toolchain_only(project_root)

    required_text_files = [
        project_root
        / "backtest"
        / "reports"
        / "generated"
        / "TASK-012_generated_runtime_summary_sample.md",
        project_root
        / "backtest"
        / "reports"
        / "generated"
        / "TASK-012_generated_TASK-010_v0.1.7_core_signal_log_throttle.md",
        project_root / "docs" / "CURRENT_TASK.md",
        project_root / "docs" / "HANDOFF_PROMPT.md",
        project_root / "docs" / "PROJECT_STATE.md",
    ]
    for path in required_text_files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("stub\n", encoding="utf-8")

    stubs = {
        "validate_backtest_runtime_report.py": "Validation passed",
        "test_validate_backtest_runtime_report.py": "Self-test passed",
        "validate_runtime_parser_input_samples.py": (
            "Runtime parser input samples validation passed"
        ),
        "test_validate_runtime_parser_input_samples.py": (
            "Runtime parser input samples self-test passed"
        ),
        "validate_project_state_docs.py": "Project state docs validation passed",
        "test_validate_project_state_docs.py": "Project state docs self-test passed",
        "validate_mq5_safety_guardrails.py": "MQ5 safety guardrails validation passed",
        "test_validate_mq5_safety_guardrails.py": "MQ5 safety guardrails self-test passed",
        "validate_backtest_set_safety.py": "Backtest set safety validation passed",
        "test_validate_backtest_set_safety.py": "Backtest set safety self-test passed",
        "validate_python_tool_safety.py": "Python tool safety validation passed",
        "test_validate_python_tool_safety.py": "Python tool safety self-test passed",
        "validate_evidence_manifest_schema.py": "Evidence manifest schema validation passed",
        "test_validate_evidence_manifest_schema.py": "Evidence manifest schema self-test passed",
        "parse_strategy_tester_html_report.py": '{"expertName": "TradingSystem"}',
        "test_parse_strategy_tester_html_report.py": "Strategy Tester HTML parser self-test passed",
        "parse_mt5_log_no_trade_summary.py": '{"expertName": "TradingSystem"}',
        "test_parse_mt5_log_no_trade_summary.py": "MT5 log no-trade parser self-test passed",
        "generate_evidence_manifest.py": '{"schemaVersion": "1.0"}',
        "test_generate_evidence_manifest.py": "Evidence manifest generator self-test passed",
        "validate_official_manifest_path_policy.py": "Official manifest path policy validation passed",
        "test_validate_official_manifest_path_policy.py": "Official manifest path policy self-test passed",
    }

    for script_name, output in stubs.items():
        returncode = 0
        if script_name == failing_script:
            output = failing_output
            returncode = failing_returncode
        write_stub_script(project_root / "tools" / script_name, output, returncode)


def recursive_self_test_issues(toolchain_path):
    text = toolchain_path.read_text(encoding="utf-8")
    if "test_run_engineering_toolchain_checks.py" in text:
        return ["recursive self-test inclusion detected", str(toolchain_path)]
    return []


def extract_toolchain_check_names(toolchain_path):
    text = toolchain_path.read_text(encoding="utf-8")
    checks_start = text.find("CHECKS = [")
    checks_end = text.find("\ndef parse_args", checks_start)
    if checks_start == -1:
        return []
    if checks_end == -1:
        checks_end = len(text)
    return re.findall(
        r"""["']name["']\s*:\s*["']([^"']+)["']""",
        text[checks_start:checks_end],
    )


def toolchain_check_list_issues(toolchain_path):
    names = extract_toolchain_check_names(toolchain_path)
    if not names:
        return ["toolchain check list mismatch", "unable to extract toolchain check names"]

    if names == EXPECTED_CHECK_NAMES:
        return []

    missing = [name for name in EXPECTED_CHECK_NAMES if name not in names]
    unexpected = [name for name in names if name not in EXPECTED_CHECK_NAMES]
    details = ["toolchain check list mismatch"]

    for name in missing:
        details.append(f"missing toolchain check: {name}")
    for name in unexpected:
        details.append(f"unexpected toolchain check: {name}")
    if not missing and not unexpected:
        details.append("toolchain check order mismatch")

    return ["toolchain check list mismatch", "\n".join(details)]


def engineering_toolchain_pass_order_issues(output):
    pass_lines = [
        line.strip()
        for line in output.splitlines()
        if line.strip().startswith(PASS_PREFIX)
    ]
    if pass_lines == PASS_LINES:
        return []

    details = ["engineering toolchain pass order mismatch"]
    missing = [line for line in PASS_LINES if line not in pass_lines]
    unexpected = [line for line in pass_lines if line not in PASS_LINES]
    for line in missing:
        details.append(f"missing PASS line: {line}")
    for line in unexpected:
        details.append(f"unexpected PASS line: {line}")
    if not missing and not unexpected:
        details.append("PASS line order mismatch")

    return ["engineering toolchain pass order mismatch", "\n".join(details)]


def extract_pass_check_names(output):
    return [
        line.strip()[len(PASS_PREFIX) :]
        for line in output.splitlines()
        if line.strip().startswith(PASS_PREFIX)
    ]


def extract_list_check_names(output):
    names = []
    for line in output.splitlines():
        match = re.match(r"^\s*\d+\.\s+(.+?)\s*$", line)
        if match:
            names.append(match.group(1))
    return names


def engineering_toolchain_list_output_issues(output):
    if LIST_TEXT not in output:
        return ["toolchain list mismatch", "Engineering toolchain checks list not found"]
    if PASS_PREFIX in output:
        return ["--list mode unexpectedly executed checks", output]
    if PASS_TEXT in output or FAIL_TEXT in output:
        return ["--list mode unexpectedly executed checks", output]

    listed_names = extract_list_check_names(output)

    if listed_names == EXPECTED_CHECK_NAMES:
        return []

    missing = [name for name in EXPECTED_CHECK_NAMES if name not in listed_names]
    unexpected = [name for name in listed_names if name not in EXPECTED_CHECK_NAMES]
    details = ["toolchain list mismatch"]
    for name in missing:
        details.append(f"missing listed check: {name}")
    for name in unexpected:
        details.append(f"unexpected listed check: {name}")
    if not missing and not unexpected:
        details.append("toolchain list order mismatch")

    return ["toolchain list mismatch", "\n".join(details)]


def build_json_list_output(names):
    return json.dumps(
        {
            "name": JSON_LIST_NAME,
            "mode": JSON_LIST_MODE,
            "checks": [
                {"index": index, "name": name}
                for index, name in enumerate(names, start=1)
            ],
        }
    )


def build_json_list_payload(names):
    return {
        "name": JSON_LIST_NAME,
        "mode": JSON_LIST_MODE,
        "checks": [
            {"index": index, "name": name}
            for index, name in enumerate(names, start=1)
        ],
    }


def toolchain_json_schema_issues(output):
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as error:
        return ["toolchain JSON schema mismatch", str(error)]

    if not isinstance(payload, dict):
        return ["toolchain JSON schema mismatch", "top-level JSON is not an object"]

    details = []
    expected_top_keys = {"name", "mode", "checks"}
    actual_top_keys = set(payload)
    for key in sorted(expected_top_keys - actual_top_keys):
        details.append(f"missing JSON key: {key}")
    for key in sorted(actual_top_keys - expected_top_keys):
        details.append(f"unexpected JSON key: {key}")

    if payload.get("name") != JSON_LIST_NAME:
        details.append("invalid JSON name")
    if payload.get("mode") != JSON_LIST_MODE:
        details.append("invalid JSON mode")

    checks = payload.get("checks")
    if not isinstance(checks, list):
        details.append("JSON checks is not a list")
        return ["toolchain JSON schema mismatch", "\n".join(details)]

    if len(checks) != len(EXPECTED_CHECK_NAMES):
        details.append("invalid JSON checks count")

    names = []
    for expected_index, item in enumerate(checks, start=1):
        if not isinstance(item, dict):
            details.append(f"invalid JSON check item at index {expected_index}")
            continue

        expected_check_keys = {"index", "name"}
        actual_check_keys = set(item)
        for key in sorted(expected_check_keys - actual_check_keys):
            details.append(f"missing JSON check key: {key}")
        for key in sorted(actual_check_keys - expected_check_keys):
            details.append(f"unexpected JSON check key: {key}")

        check_index = item.get("index")
        if type(check_index) is not int or check_index != expected_index:
            details.append("invalid JSON check index")

        check_name = item.get("name")
        if not isinstance(check_name, str) or not check_name:
            details.append("invalid JSON check name")
        names.append(check_name)

    if names != EXPECTED_CHECK_NAMES:
        details.append("toolchain JSON list order mismatch")

    if details:
        return ["toolchain JSON schema mismatch", "\n".join(details)]

    return []


def toolchain_json_list_output_issues(output):
    if PASS_PREFIX in output or PASS_TEXT in output or FAIL_TEXT in output:
        return ["--list JSON mode unexpectedly executed checks", output]

    try:
        payload = json.loads(output)
    except json.JSONDecodeError as error:
        return ["toolchain JSON list is not valid JSON", str(error)]

    if not isinstance(payload, dict):
        return ["toolchain JSON list mismatch", "top-level JSON is not an object"]

    details = []
    if payload.get("name") != JSON_LIST_NAME:
        details.append("name mismatch")
    if payload.get("mode") != JSON_LIST_MODE:
        details.append("mode mismatch")

    checks = payload.get("checks")
    if not isinstance(checks, list):
        details.append("checks is not a list")
        return ["toolchain JSON list mismatch", "\n".join(details)]

    indexes = []
    names = []
    for item in checks:
        if not isinstance(item, dict):
            details.append("check item is not an object")
            continue
        if "index" not in item or "name" not in item:
            details.append("check item missing index or name")
        indexes.append(item.get("index"))
        names.append(item.get("name"))

    expected_indexes = list(range(1, len(EXPECTED_CHECK_NAMES) + 1))
    if indexes != expected_indexes:
        details.append("toolchain JSON list index mismatch")

    if names != EXPECTED_CHECK_NAMES:
        missing = [name for name in EXPECTED_CHECK_NAMES if name not in names]
        unexpected = [name for name in names if name not in EXPECTED_CHECK_NAMES]
        for name in missing:
            details.append(f"missing JSON listed check: {name}")
        for name in unexpected:
            details.append(f"unexpected JSON listed check: {name}")
        if not missing and not unexpected:
            details.append("toolchain JSON list order mismatch")

    if details:
        return ["toolchain JSON list mismatch", "\n".join(details)]

    return []


def extract_json_list_check_names(output):
    payload = json.loads(output)
    return [item.get("name") for item in payload.get("checks", [])]


def toolchain_json_list_pass_consistency_issues(
    json_output,
    list_output,
    pass_output,
):
    json_issue = toolchain_json_list_output_issues(json_output)
    if json_issue:
        return ["toolchain JSON/list/pass checks mismatch", "\n".join(json_issue)]

    list_issue = engineering_toolchain_list_output_issues(list_output)
    if list_issue:
        return ["toolchain JSON/list/pass checks mismatch", "\n".join(list_issue)]

    json_names = extract_json_list_check_names(json_output)
    listed_names = extract_list_check_names(list_output)
    pass_names = extract_pass_check_names(pass_output)

    if json_names == listed_names == pass_names:
        return []

    details = ["toolchain JSON/list/pass checks mismatch"]

    for name in json_names:
        if name not in listed_names:
            details.append(f"missing listed check: {name}")
        if name not in pass_names:
            details.append(f"missing PASS check: {name}")

    for name in listed_names:
        if name not in json_names:
            details.append(f"unexpected listed check: {name}")

    for name in pass_names:
        if name not in json_names:
            details.append(f"unexpected PASS check: {name}")

    for name in json_names:
        if name not in EXPECTED_CHECK_NAMES:
            details.append(f"unexpected JSON listed check: {name}")

    if len(details) == 1:
        details.append("toolchain JSON/list/pass order mismatch")

    return ["toolchain JSON/list/pass checks mismatch", "\n".join(details)]


def toolchain_list_and_pass_consistency_issues(list_output, pass_output):
    listed_names = extract_list_check_names(list_output)
    pass_names = extract_pass_check_names(pass_output)

    if listed_names == pass_names:
        return []

    missing = [name for name in pass_names if name not in listed_names]
    unexpected = [name for name in listed_names if name not in pass_names]
    details = ["toolchain list and pass checks mismatch"]
    for name in missing:
        details.append(f"missing listed check: {name}")
    for name in unexpected:
        details.append(f"unexpected listed check: {name}")
    if not missing and not unexpected:
        details.append("toolchain list/pass order mismatch")

    return ["toolchain list and pass checks mismatch", "\n".join(details)]


def engineering_toolchain_list_readonly_issues(project_root):
    before = collect_project_file_hashes(project_root)
    result = run_toolchain(project_root, ["--list"])
    output = combined_output(result)
    if result.returncode != 0:
        return ["toolchain list mismatch", output]

    list_issue = engineering_toolchain_list_output_issues(output)
    if list_issue:
        return list_issue

    after = collect_project_file_hashes(project_root)
    changed_files = [
        path
        for path in sorted(set(before) | set(after))
        if before.get(path) != after.get(path)
    ]
    if changed_files:
        return [
            "--list mode modified project files",
            "\n".join(changed_files),
        ]

    return []


def engineering_toolchain_json_list_readonly_issues(project_root):
    before = collect_project_file_hashes(project_root)
    result = run_toolchain(project_root, ["--list", "--json"])
    output = combined_output(result)
    if result.returncode != 0:
        return ["toolchain JSON list mismatch", output]

    json_issue = toolchain_json_list_output_issues(output)
    if json_issue:
        return json_issue

    schema_issue = toolchain_json_schema_issues(output)
    if schema_issue:
        return schema_issue

    after = collect_project_file_hashes(project_root)
    changed_files = [
        path
        for path in sorted(set(before) | set(after))
        if before.get(path) != after.get(path)
    ]
    if changed_files:
        return [
            "--list JSON mode modified project files",
            "\n".join(changed_files),
        ]

    return []


def engineering_toolchain_list_pass_consistency_current_project_issues(
    project_root,
    pass_output,
):
    result = run_toolchain(project_root, ["--list"])
    list_output = combined_output(result)
    if result.returncode != 0:
        return ["toolchain list and pass checks mismatch", list_output]

    list_issue = engineering_toolchain_list_output_issues(list_output)
    if list_issue:
        return list_issue

    return toolchain_list_and_pass_consistency_issues(list_output, pass_output)


def engineering_toolchain_three_mode_consistency_current_project_issues(
    project_root,
    pass_output,
):
    json_result = run_toolchain(project_root, ["--list", "--json"])
    json_output = combined_output(json_result)
    if json_result.returncode != 0:
        return ["toolchain JSON/list/pass checks mismatch", json_output]

    list_result = run_toolchain(project_root, ["--list"])
    list_output = combined_output(list_result)
    if list_result.returncode != 0:
        return ["toolchain JSON/list/pass checks mismatch", list_output]

    return toolchain_json_list_pass_consistency_issues(
        json_output,
        list_output,
        pass_output,
    )


def python_tool_safety_scan_coverage_issues(project_root, toolchain_output=None):
    tools_dir = project_root / "tools"
    expected_count = len(list(tools_dir.glob("*.py")))

    validation_result = run_tool(project_root, "validate_python_tool_safety.py")
    validation_output = combined_output(validation_result)
    if validation_result.returncode != 0 or "Python tool safety validation passed" not in validation_output:
        return ["Python tool safety scan coverage was not verified", validation_output]

    match = re.search(r"scanned python tools count:\s*(\d+)", validation_output)
    if not match:
        return ["Python tool safety scan coverage was not verified", validation_output]

    scanned_count = int(match.group(1))
    if scanned_count != expected_count:
        return [
            "Python tool safety scan count mismatch",
            f"expected scanned python tools count {expected_count} but got {scanned_count}",
        ]

    self_test_result = run_tool(project_root, "test_validate_python_tool_safety.py")
    self_test_output = combined_output(self_test_result)
    if (
        self_test_result.returncode != 0
        or "Python tool safety self-test passed" not in self_test_output
    ):
        return ["Python tool safety self-test pass line not found", self_test_output]

    if toolchain_output is None:
        toolchain_result = run_toolchain(project_root)
        toolchain_output = combined_output(toolchain_result)
        if toolchain_result.returncode != 0 or PASS_TEXT not in toolchain_output:
            return ["Python tool safety scan coverage was not verified", toolchain_output]

    if "[PASS] validate Python tool safety self-test" not in toolchain_output:
        return ["Python tool safety self-test pass line not found", toolchain_output]

    return []


def write_toolchain_check_list(path, names):
    path.parent.mkdir(parents=True, exist_ok=True)
    checks = "\n".join(f'    {{"name": "{name}"}},' for name in names)
    path.write_text(f"CHECKS = [\n{checks}\n]\n", encoding="utf-8")


def positive_current_project():
    if not TOOLCHAIN_SCRIPT.exists():
        return ["toolchain script not found", str(TOOLCHAIN_SCRIPT)]

    recursive_issue = recursive_self_test_issues(TOOLCHAIN_SCRIPT)
    if recursive_issue:
        return recursive_issue

    check_list_issue = toolchain_check_list_issues(TOOLCHAIN_SCRIPT)
    if check_list_issue:
        return check_list_issue

    result = run_toolchain(ROOT_DIR)
    output = combined_output(result)
    if result.returncode != 0 or PASS_TEXT not in output:
        return ["positive engineering toolchain check did not pass", output]

    missing_pass_lines = [line for line in PASS_LINES if line not in output]
    if missing_pass_lines:
        return [
            f"expected {len(PASS_LINES)} PASS lines not found",
            "\n".join(missing_pass_lines) + "\n" + output,
        ]

    pass_order_issue = engineering_toolchain_pass_order_issues(output)
    if pass_order_issue:
        return pass_order_issue

    list_readonly_issue = engineering_toolchain_list_readonly_issues(ROOT_DIR)
    if list_readonly_issue:
        return list_readonly_issue

    json_list_readonly_issue = engineering_toolchain_json_list_readonly_issues(ROOT_DIR)
    if json_list_readonly_issue:
        return json_list_readonly_issue

    list_pass_consistency_issue = (
        engineering_toolchain_list_pass_consistency_current_project_issues(
            ROOT_DIR,
            output,
        )
    )
    if list_pass_consistency_issue:
        return list_pass_consistency_issue

    three_mode_consistency_issue = (
        engineering_toolchain_three_mode_consistency_current_project_issues(
            ROOT_DIR,
            output,
        )
    )
    if three_mode_consistency_issue:
        return three_mode_consistency_issue

    scan_coverage_issue = python_tool_safety_scan_coverage_issues(ROOT_DIR, output)
    if scan_coverage_issue:
        return scan_coverage_issue

    readonly_issue = engineering_toolchain_readonly_issues(ROOT_DIR)
    if readonly_issue:
        return readonly_issue

    return []


def negative_missing_mq5_self_test():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        copy_toolchain_only(project_root)
        result = run_toolchain(project_root)
        output = combined_output(result)

    if result.returncode == 0:
        return ["missing mq5 self-test file was not detected", output]
    if FAIL_TEXT not in output:
        return ["expected Engineering toolchain checks failed output not found", output]
    if "test_validate_mq5_safety_guardrails.py" not in output:
        return ["missing mq5 self-test file was not detected", output]
    return []


def negative_missing_generated_report():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        copy_toolchain_only(project_root)
        result = run_toolchain(project_root)
        output = combined_output(result)

    if result.returncode == 0:
        return ["missing generated report was not detected", output]
    if FAIL_TEXT not in output:
        return ["expected Engineering toolchain checks failed output not found", output]
    if "TASK-012_generated_runtime_summary_sample.md" not in output:
        return ["missing generated report was not detected", output]
    return []


def negative_missing_backtest_set_validator():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        copy_toolchain_only(project_root)
        result = run_toolchain(project_root)
        output = combined_output(result)

    if result.returncode == 0:
        return ["missing backtest set safety validator was not detected", output]
    if FAIL_TEXT not in output:
        return ["expected Engineering toolchain checks failed output not found", output]
    if "validate_backtest_set_safety.py" not in output:
        return ["missing backtest set safety validator was not detected", output]
    return []


def negative_missing_backtest_set_self_test():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        copy_toolchain_only(project_root)
        result = run_toolchain(project_root)
        output = combined_output(result)

    if result.returncode == 0:
        return ["missing backtest set safety self-test was not detected", output]
    if FAIL_TEXT not in output:
        return ["expected Engineering toolchain checks failed output not found", output]
    if "test_validate_backtest_set_safety.py" not in output:
        return ["missing backtest set safety self-test was not detected", output]
    return []


def negative_missing_python_tool_safety_validator():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        copy_toolchain_only(project_root)
        result = run_toolchain(project_root)
        output = combined_output(result)

    if result.returncode == 0:
        return ["missing Python tool safety validator was not detected", output]
    if FAIL_TEXT not in output:
        return ["expected Engineering toolchain checks failed output not found", output]
    if "validate_python_tool_safety.py" not in output:
        return ["missing Python tool safety validator was not detected", output]
    return []


def negative_missing_python_tool_safety_self_test():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        copy_toolchain_only(project_root)
        result = run_toolchain(project_root)
        output = combined_output(result)

    if result.returncode == 0:
        return ["missing Python tool safety self-test was not detected", output]
    if FAIL_TEXT not in output:
        return ["expected Engineering toolchain checks failed output not found", output]
    if "test_validate_python_tool_safety.py" not in output:
        return ["missing Python tool safety self-test was not detected", output]
    return []


def negative_recursive_self_test_inclusion():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        tools_dir = project_root / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        toolchain_path = tools_dir / "run_engineering_toolchain_checks.py"
        toolchain_path.write_text(
            'CHECKS = ["tools/test_run_engineering_toolchain_checks.py"]\n',
            encoding="utf-8",
        )
        result = recursive_self_test_issues(toolchain_path)

    if not result:
        return ["recursive self-test inclusion detected was not detected", ""]
    if result[0] != "recursive self-test inclusion detected":
        return ["recursive self-test inclusion detected", "\n".join(result)]
    return []


def negative_python_tool_safety_child_failure():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        create_toolchain_fixture(
            project_root,
            failing_script="validate_python_tool_safety.py",
            failing_output="Python tool safety validation failed",
        )
        result = run_toolchain(project_root)
        output = combined_output(result)

    if result.returncode == 0:
        return ["Python tool safety child failure was not propagated", output]
    if FAIL_TEXT not in output:
        return ["expected Engineering toolchain checks failed output not found", output]
    if "validate Python tool safety" not in output:
        return ["Python tool safety child failure was not propagated", output]
    return []


def negative_backtest_set_safety_child_failure():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        create_toolchain_fixture(
            project_root,
            failing_script="validate_backtest_set_safety.py",
            failing_output="Backtest set safety validation failed",
        )
        result = run_toolchain(project_root)
        output = combined_output(result)

    if result.returncode == 0:
        return ["backtest set safety child failure was not propagated", output]
    if FAIL_TEXT not in output:
        return ["expected Engineering toolchain checks failed output not found", output]
    if "validate backtest set safety" not in output:
        return ["backtest set safety child failure was not propagated", output]
    return []


def negative_runtime_parser_input_samples_child_failure():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        create_toolchain_fixture(
            project_root,
            failing_script="validate_runtime_parser_input_samples.py",
            failing_output="Runtime parser input samples validation failed",
        )
        result = run_toolchain(project_root)
        output = combined_output(result)

    if result.returncode == 0:
        return ["runtime parser input samples child failure was not propagated", output]
    if FAIL_TEXT not in output:
        return ["expected Engineering toolchain checks failed output not found", output]
    if "validate runtime parser input samples" not in output:
        return ["runtime parser input samples child failure was not propagated", output]
    return []


def negative_missing_toolchain_check_name():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        toolchain_path = project_root / "tools" / "run_engineering_toolchain_checks.py"
        write_toolchain_check_list(toolchain_path, EXPECTED_CHECK_NAMES[:-1])
        result = toolchain_check_list_issues(toolchain_path)

    output = "\n".join(result)
    if not result:
        return ["missing toolchain check was not detected", ""]
    if "toolchain check list mismatch" not in output:
        return ["toolchain check list mismatch was not reported", output]
    if "missing toolchain check" not in output:
        return ["missing toolchain check was not reported", output]
    if EXPECTED_CHECK_NAMES[-1] not in output:
        return ["missing toolchain check name was not reported", output]
    return []


def negative_unexpected_toolchain_check_name():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        toolchain_path = project_root / "tools" / "run_engineering_toolchain_checks.py"
        write_toolchain_check_list(
            toolchain_path,
            EXPECTED_CHECK_NAMES + ["validate unexpected future check"],
        )
        result = toolchain_check_list_issues(toolchain_path)

    output = "\n".join(result)
    if not result:
        return ["unexpected toolchain check was not detected", ""]
    if "toolchain check list mismatch" not in output:
        return ["toolchain check list mismatch was not reported", output]
    if "unexpected toolchain check" not in output:
        return ["unexpected toolchain check was not reported", output]
    if "validate unexpected future check" not in output:
        return ["unexpected toolchain check name was not reported", output]
    return []


def negative_python_tool_safety_scan_coverage_failure():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        tools_dir = project_root / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        write_stub_script(
            tools_dir / "validate_python_tool_safety.py",
            "\n".join(
                [
                    "Python tool safety validation passed",
                    "scanned python tools count: 1",
                    "forbidden import findings: 0",
                    "forbidden external command findings: 0",
                ]
            ),
        )
        write_stub_script(
            tools_dir / "test_validate_python_tool_safety.py",
            "Python tool safety self-test passed",
        )
        write_stub_script(
            tools_dir / "run_engineering_toolchain_checks.py",
            "\n".join(
                [
                    "[PASS] validate Python tool safety self-test",
                    "Engineering toolchain checks passed",
                ]
            ),
        )
        (tools_dir / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
        (tools_dir / "b.py").write_text("VALUE = 2\n", encoding="utf-8")

        actual_count = len(list(tools_dir.glob("*.py")))
        result = python_tool_safety_scan_coverage_issues(project_root)

    output = "\n".join(result)
    if actual_count <= 1:
        return ["Python tool safety scan coverage fixture was not valid", str(actual_count)]
    if not result:
        return ["Python tool safety scan coverage was not verified", ""]
    if (
        "Python tool safety scan count mismatch" not in output
        and "Python tool safety scan coverage was not verified" not in output
    ):
        return ["Python tool safety scan coverage was not verified", output]
    return []


def negative_engineering_toolchain_readonly_failure():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        docs_dir = project_root / "docs"
        tools_dir = project_root / "tools"
        reports_dir = project_root / "backtest" / "reports" / "generated"
        sets_dir = project_root / "backtest" / "sets"
        mq5_dir = project_root / "mq5"
        for directory in (docs_dir, tools_dir, reports_dir, sets_dir, mq5_dir):
            directory.mkdir(parents=True, exist_ok=True)

        (docs_dir / "CURRENT_TASK.md").write_text("before\n", encoding="utf-8")
        (docs_dir / "HANDOFF_PROMPT.md").write_text("handoff\n", encoding="utf-8")
        (docs_dir / "PROJECT_STATE.md").write_text("state\n", encoding="utf-8")
        (reports_dir / "sample.md").write_text("report\n", encoding="utf-8")
        (sets_dir / "sample.set").write_text("InpEnableTrading=false\n", encoding="utf-8")
        (mq5_dir / "sample.mq5").write_text("// sample\n", encoding="utf-8")
        (tools_dir / "safe_tool.py").write_text("VALUE = 1\n", encoding="utf-8")
        (tools_dir / "run_engineering_toolchain_checks.py").write_text(
            textwrap.dedent(
                """\
                from pathlib import Path

                Path("docs/CURRENT_TASK.md").write_text("after\\n", encoding="utf-8")
                print("Engineering toolchain checks passed")
                """
            ),
            encoding="utf-8",
        )

        result = engineering_toolchain_readonly_issues(project_root)

    output = "\n".join(result)
    if not result:
        return ["engineering toolchain modified project files was not detected", ""]
    if "engineering toolchain modified project files" not in output:
        return ["engineering toolchain modified project files was not reported", output]
    if "docs/CURRENT_TASK.md" not in output:
        return ["modified project file path was not reported", output]
    return []


def negative_engineering_toolchain_json_list_readonly_failure():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        docs_dir = project_root / "docs"
        tools_dir = project_root / "tools"
        reports_dir = project_root / "backtest" / "reports" / "generated"
        sets_dir = project_root / "backtest" / "sets"
        mq5_dir = project_root / "mq5"
        for directory in (docs_dir, tools_dir, reports_dir, sets_dir, mq5_dir):
            directory.mkdir(parents=True, exist_ok=True)

        (docs_dir / "CURRENT_TASK.md").write_text("before\n", encoding="utf-8")
        (docs_dir / "HANDOFF_PROMPT.md").write_text("handoff\n", encoding="utf-8")
        (docs_dir / "PROJECT_STATE.md").write_text("state\n", encoding="utf-8")
        (reports_dir / "sample.md").write_text("report\n", encoding="utf-8")
        (sets_dir / "sample.set").write_text("InpEnableTrading=false\n", encoding="utf-8")
        (mq5_dir / "sample.mq5").write_text("// sample\n", encoding="utf-8")
        (tools_dir / "safe_tool.py").write_text("VALUE = 1\n", encoding="utf-8")
        (tools_dir / "run_engineering_toolchain_checks.py").write_text(
            textwrap.dedent(
                f"""\
                import json
                from pathlib import Path

                Path("docs/CURRENT_TASK.md").write_text("after\\n", encoding="utf-8")
                print(json.dumps({build_json_list_payload(EXPECTED_CHECK_NAMES)!r}))
                """
            ),
            encoding="utf-8",
        )

        result = engineering_toolchain_json_list_readonly_issues(project_root)

    output = "\n".join(result)
    if not result:
        return ["--list JSON mode modified project files was not detected", ""]
    if (
        "--list JSON mode modified project files" not in output
        and "JSON list mode modified project files" not in output
    ):
        return ["--list JSON mode modified project files was not reported", output]
    if "docs/CURRENT_TASK.md" not in output:
        return ["modified project file path was not reported", output]
    return []


def negative_engineering_toolchain_pass_order_failure():
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        tools_dir = project_root / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        reordered_lines = PASS_LINES[-2:] + PASS_LINES[:-2]
        write_stub_script(
            tools_dir / "run_engineering_toolchain_checks.py",
            "\n".join(reordered_lines + [PASS_TEXT]),
        )
        result = run_toolchain(project_root)
        output = combined_output(result)
        issue = engineering_toolchain_pass_order_issues(output)

    issue_output = "\n".join(issue)
    if not issue:
        return ["engineering toolchain pass order mismatch was not detected", output]
    if "engineering toolchain pass order mismatch" not in issue_output:
        return ["engineering toolchain pass order mismatch was not reported", issue_output]
    return []


def negative_engineering_toolchain_unexpected_pass_line():
    output = "\n".join(PASS_LINES + ["[PASS] validate unexpected future check", PASS_TEXT])
    issue = engineering_toolchain_pass_order_issues(output)
    issue_output = "\n".join(issue)
    if not issue:
        return ["unexpected PASS line was not detected", output]
    if "engineering toolchain pass order mismatch" not in issue_output:
        return ["engineering toolchain pass order mismatch was not reported", issue_output]
    if "unexpected PASS line" not in issue_output:
        return ["unexpected PASS line was not reported", issue_output]
    return []


def negative_toolchain_list_missing_check():
    output = "\n".join(
        [LIST_TEXT]
        + [
            f"{index}. {name}"
            for index, name in enumerate(EXPECTED_CHECK_NAMES[:-1], start=1)
        ]
    )
    issue = engineering_toolchain_list_output_issues(output)
    issue_output = "\n".join(issue)
    if not issue:
        return ["missing listed check was not detected", output]
    if "toolchain list mismatch" not in issue_output:
        return ["toolchain list mismatch was not reported", issue_output]
    if "missing listed check" not in issue_output:
        return ["missing listed check was not reported", issue_output]
    if EXPECTED_CHECK_NAMES[-1] not in issue_output:
        return ["missing listed check name was not reported", issue_output]
    return []


def negative_toolchain_list_order_failure():
    reordered_names = EXPECTED_CHECK_NAMES[-2:] + EXPECTED_CHECK_NAMES[:-2]
    output = "\n".join(
        [LIST_TEXT]
        + [f"{index}. {name}" for index, name in enumerate(reordered_names, start=1)]
    )
    issue = engineering_toolchain_list_output_issues(output)
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain list order mismatch was not detected", output]
    if "toolchain list mismatch" not in issue_output:
        return ["toolchain list mismatch was not reported", issue_output]
    if "toolchain list order mismatch" not in issue_output:
        return ["toolchain list order mismatch was not reported", issue_output]
    return []


def negative_toolchain_list_does_not_execute_child_checks():
    poison_text = "POISON CHILD CHECK EXECUTED"
    child_scripts = [
        "validate_backtest_runtime_report.py",
        "test_validate_backtest_runtime_report.py",
        "validate_runtime_parser_input_samples.py",
        "test_validate_runtime_parser_input_samples.py",
        "validate_project_state_docs.py",
        "test_validate_project_state_docs.py",
        "validate_mq5_safety_guardrails.py",
        "test_validate_mq5_safety_guardrails.py",
        "validate_backtest_set_safety.py",
        "test_validate_backtest_set_safety.py",
        "validate_python_tool_safety.py",
        "test_validate_python_tool_safety.py",
        "validate_evidence_manifest_schema.py",
        "test_validate_evidence_manifest_schema.py",
        "parse_strategy_tester_html_report.py",
        "test_parse_strategy_tester_html_report.py",
        "parse_mt5_log_no_trade_summary.py",
        "test_parse_mt5_log_no_trade_summary.py",
        "generate_evidence_manifest.py",
        "test_generate_evidence_manifest.py",
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        copy_toolchain_only(project_root)

        required_text_files = [
            project_root
            / "backtest"
            / "reports"
            / "generated"
            / "TASK-012_generated_runtime_summary_sample.md",
            project_root
            / "backtest"
            / "reports"
            / "generated"
            / "TASK-012_generated_TASK-010_v0.1.7_core_signal_log_throttle.md",
            project_root / "docs" / "CURRENT_TASK.md",
            project_root / "docs" / "HANDOFF_PROMPT.md",
            project_root / "docs" / "PROJECT_STATE.md",
        ]
        for path in required_text_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("stub\n", encoding="utf-8")

        for script_name in child_scripts:
            write_stub_script(
                project_root / "tools" / script_name,
                poison_text,
                returncode=99,
            )

        result = run_toolchain(project_root, ["--list"])
        output = combined_output(result)

    if result.returncode != 0:
        return ["toolchain list mismatch", output]

    list_issue = engineering_toolchain_list_output_issues(output)
    if list_issue:
        return list_issue

    if poison_text in output:
        return ["--list mode executed child checks", output]

    return []


def negative_toolchain_json_list_does_not_execute_child_checks():
    poison_text = "POISON CHILD CHECK EXECUTED"
    child_scripts = [
        "validate_backtest_runtime_report.py",
        "test_validate_backtest_runtime_report.py",
        "validate_runtime_parser_input_samples.py",
        "test_validate_runtime_parser_input_samples.py",
        "validate_project_state_docs.py",
        "test_validate_project_state_docs.py",
        "validate_mq5_safety_guardrails.py",
        "test_validate_mq5_safety_guardrails.py",
        "validate_backtest_set_safety.py",
        "test_validate_backtest_set_safety.py",
        "validate_python_tool_safety.py",
        "test_validate_python_tool_safety.py",
        "validate_evidence_manifest_schema.py",
        "test_validate_evidence_manifest_schema.py",
        "parse_strategy_tester_html_report.py",
        "test_parse_strategy_tester_html_report.py",
        "parse_mt5_log_no_trade_summary.py",
        "test_parse_mt5_log_no_trade_summary.py",
        "generate_evidence_manifest.py",
        "test_generate_evidence_manifest.py",
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        copy_toolchain_only(project_root)

        required_text_files = [
            project_root
            / "backtest"
            / "reports"
            / "generated"
            / "TASK-012_generated_runtime_summary_sample.md",
            project_root
            / "backtest"
            / "reports"
            / "generated"
            / "TASK-012_generated_TASK-010_v0.1.7_core_signal_log_throttle.md",
            project_root / "docs" / "CURRENT_TASK.md",
            project_root / "docs" / "HANDOFF_PROMPT.md",
            project_root / "docs" / "PROJECT_STATE.md",
        ]
        for path in required_text_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("stub\n", encoding="utf-8")

        for script_name in child_scripts:
            write_stub_script(
                project_root / "tools" / script_name,
                poison_text,
                returncode=99,
            )

        result = run_toolchain(project_root, ["--list", "--json"])
        stdout = result.stdout or ""
        output = combined_output(result)

    if result.returncode != 0:
        return ["toolchain JSON list mismatch", output]

    if poison_text in output:
        return ["--list JSON mode executed child checks", output]

    if PASS_PREFIX in output:
        return ["--list JSON mode output included PASS lines", output]

    if PASS_TEXT in output or FAIL_TEXT in output:
        return ["--list JSON mode unexpectedly executed checks", output]

    json_issue = toolchain_json_list_output_issues(stdout)
    if json_issue:
        return json_issue

    schema_issue = toolchain_json_schema_issues(stdout)
    if schema_issue:
        return schema_issue

    return []


def negative_toolchain_list_pass_missing_listed_check():
    list_output = "\n".join(
        [LIST_TEXT]
        + [
            f"{index}. {name}"
            for index, name in enumerate(EXPECTED_CHECK_NAMES[:-1], start=1)
        ]
    )
    pass_output = "\n".join(PASS_LINES + [PASS_TEXT])
    issue = toolchain_list_and_pass_consistency_issues(list_output, pass_output)
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain list and pass checks mismatch was not detected", ""]
    if "toolchain list and pass checks mismatch" not in issue_output:
        return ["toolchain list and pass checks mismatch was not reported", issue_output]
    if "missing listed check" not in issue_output:
        return ["missing listed check was not reported", issue_output]
    if EXPECTED_CHECK_NAMES[-1] not in issue_output:
        return ["missing listed check name was not reported", issue_output]
    return []


def negative_toolchain_list_pass_unexpected_listed_check():
    listed_names = EXPECTED_CHECK_NAMES + ["validate unexpected future check"]
    list_output = "\n".join(
        [LIST_TEXT]
        + [f"{index}. {name}" for index, name in enumerate(listed_names, start=1)]
    )
    pass_output = "\n".join(PASS_LINES + [PASS_TEXT])
    issue = toolchain_list_and_pass_consistency_issues(list_output, pass_output)
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain list and pass checks mismatch was not detected", ""]
    if "toolchain list and pass checks mismatch" not in issue_output:
        return ["toolchain list and pass checks mismatch was not reported", issue_output]
    if "unexpected listed check" not in issue_output:
        return ["unexpected listed check was not reported", issue_output]
    if "validate unexpected future check" not in issue_output:
        return ["unexpected listed check name was not reported", issue_output]
    return []


def negative_toolchain_list_pass_order_failure():
    reordered_names = EXPECTED_CHECK_NAMES[-2:] + EXPECTED_CHECK_NAMES[:-2]
    list_output = "\n".join(
        [LIST_TEXT]
        + [f"{index}. {name}" for index, name in enumerate(reordered_names, start=1)]
    )
    pass_output = "\n".join(PASS_LINES + [PASS_TEXT])
    issue = toolchain_list_and_pass_consistency_issues(list_output, pass_output)
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain list/pass order mismatch was not detected", ""]
    if "toolchain list and pass checks mismatch" not in issue_output:
        return ["toolchain list and pass checks mismatch was not reported", issue_output]
    if "toolchain list/pass order mismatch" not in issue_output:
        return ["toolchain list/pass order mismatch was not reported", issue_output]
    return []


def negative_toolchain_json_list_missing_check():
    output = build_json_list_output(EXPECTED_CHECK_NAMES[:-1])
    issue = toolchain_json_list_output_issues(output)
    issue_output = "\n".join(issue)
    if not issue:
        return ["missing JSON listed check was not detected", output]
    if "toolchain JSON list mismatch" not in issue_output:
        return ["toolchain JSON list mismatch was not reported", issue_output]
    if "missing JSON listed check" not in issue_output:
        return ["missing JSON listed check was not reported", issue_output]
    if EXPECTED_CHECK_NAMES[-1] not in issue_output:
        return ["missing JSON listed check name was not reported", issue_output]
    return []


def negative_toolchain_json_list_order_failure():
    reordered_names = EXPECTED_CHECK_NAMES[-2:] + EXPECTED_CHECK_NAMES[:-2]
    output = build_json_list_output(reordered_names)
    issue = toolchain_json_list_output_issues(output)
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain JSON list order mismatch was not detected", output]
    if "toolchain JSON list mismatch" not in issue_output:
        return ["toolchain JSON list mismatch was not reported", issue_output]
    if "toolchain JSON list order mismatch" not in issue_output:
        return ["toolchain JSON list order mismatch was not reported", issue_output]
    return []


def negative_toolchain_json_list_invalid_json():
    issue = toolchain_json_list_output_issues("not json")
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain JSON list is not valid JSON was not detected", ""]
    if "toolchain JSON list is not valid JSON" not in issue_output:
        return ["toolchain JSON list is not valid JSON was not reported", issue_output]
    return []


def negative_toolchain_json_list_unexpected_check():
    output = build_json_list_output(
        EXPECTED_CHECK_NAMES + ["validate unexpected future check"]
    )
    issue = toolchain_json_list_output_issues(output)
    issue_output = "\n".join(issue)
    if not issue:
        return ["unexpected JSON listed check was not detected", output]
    if "toolchain JSON list mismatch" not in issue_output:
        return ["toolchain JSON list mismatch was not reported", issue_output]
    if "unexpected JSON listed check" not in issue_output:
        return ["unexpected JSON listed check was not reported", issue_output]
    if "validate unexpected future check" not in issue_output:
        return ["unexpected JSON listed check name was not reported", issue_output]
    return []


def negative_toolchain_three_mode_list_mismatch():
    json_output = build_json_list_output(EXPECTED_CHECK_NAMES)
    list_output = "\n".join(
        [LIST_TEXT]
        + [
            f"{index}. {name}"
            for index, name in enumerate(EXPECTED_CHECK_NAMES[:-1], start=1)
        ]
    )
    pass_output = "\n".join(PASS_LINES + [PASS_TEXT])
    issue = toolchain_json_list_pass_consistency_issues(
        json_output,
        list_output,
        pass_output,
    )
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain JSON/list/pass checks mismatch was not detected", ""]
    if "toolchain JSON/list/pass checks mismatch" not in issue_output:
        return ["toolchain JSON/list/pass checks mismatch was not reported", issue_output]
    if "missing listed check" not in issue_output:
        return ["missing listed check was not reported", issue_output]
    if EXPECTED_CHECK_NAMES[-1] not in issue_output:
        return ["missing listed check name was not reported", issue_output]
    return []


def negative_toolchain_three_mode_pass_mismatch():
    json_output = build_json_list_output(EXPECTED_CHECK_NAMES)
    list_output = "\n".join(
        [LIST_TEXT]
        + [
            f"{index}. {name}"
            for index, name in enumerate(EXPECTED_CHECK_NAMES, start=1)
        ]
    )
    pass_output = "\n".join(PASS_LINES[:-1] + [PASS_TEXT])
    issue = toolchain_json_list_pass_consistency_issues(
        json_output,
        list_output,
        pass_output,
    )
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain JSON/list/pass checks mismatch was not detected", ""]
    if "toolchain JSON/list/pass checks mismatch" not in issue_output:
        return ["toolchain JSON/list/pass checks mismatch was not reported", issue_output]
    if "missing PASS check" not in issue_output:
        return ["missing PASS check was not reported", issue_output]
    if EXPECTED_CHECK_NAMES[-1] not in issue_output:
        return ["missing PASS check name was not reported", issue_output]
    return []


def negative_toolchain_three_mode_order_mismatch():
    json_names = EXPECTED_CHECK_NAMES[:-2] + [
        EXPECTED_CHECK_NAMES[-1],
        EXPECTED_CHECK_NAMES[-2],
    ]
    json_output = build_json_list_output(json_names)
    list_output = "\n".join(
        [LIST_TEXT]
        + [
            f"{index}. {name}"
            for index, name in enumerate(EXPECTED_CHECK_NAMES, start=1)
        ]
    )
    pass_output = "\n".join(PASS_LINES + [PASS_TEXT])
    issue = toolchain_json_list_pass_consistency_issues(
        json_output,
        list_output,
        pass_output,
    )
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain JSON/list/pass order mismatch was not detected", ""]
    if "toolchain JSON/list/pass checks mismatch" not in issue_output:
        return ["toolchain JSON/list/pass checks mismatch was not reported", issue_output]
    if (
        "toolchain JSON/list/pass order mismatch" not in issue_output
        and "toolchain JSON list order mismatch" not in issue_output
    ):
        return ["toolchain JSON/list/pass order mismatch was not reported", issue_output]
    return []


def negative_toolchain_three_mode_json_unexpected_check():
    json_output = build_json_list_output(
        EXPECTED_CHECK_NAMES + ["validate unexpected future check"]
    )
    list_output = "\n".join(
        [LIST_TEXT]
        + [
            f"{index}. {name}"
            for index, name in enumerate(EXPECTED_CHECK_NAMES, start=1)
        ]
    )
    pass_output = "\n".join(PASS_LINES + [PASS_TEXT])
    issue = toolchain_json_list_pass_consistency_issues(
        json_output,
        list_output,
        pass_output,
    )
    issue_output = "\n".join(issue)
    if not issue:
        return ["unexpected JSON listed check was not detected", ""]
    if "toolchain JSON/list/pass checks mismatch" not in issue_output:
        return ["toolchain JSON/list/pass checks mismatch was not reported", issue_output]
    if "unexpected JSON listed check" not in issue_output:
        return ["unexpected JSON listed check was not reported", issue_output]
    if "validate unexpected future check" not in issue_output:
        return ["unexpected JSON listed check name was not reported", issue_output]
    return []


def negative_toolchain_json_schema_missing_name():
    payload = build_json_list_payload(EXPECTED_CHECK_NAMES)
    del payload["name"]
    issue = toolchain_json_schema_issues(json.dumps(payload))
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain JSON schema mismatch was not detected", ""]
    if "toolchain JSON schema mismatch" not in issue_output:
        return ["toolchain JSON schema mismatch was not reported", issue_output]
    if "missing JSON key: name" not in issue_output:
        return ["missing JSON key: name was not reported", issue_output]
    return []


def negative_toolchain_json_schema_extra_top_level_key():
    payload = build_json_list_payload(EXPECTED_CHECK_NAMES)
    payload["extra"] = "unexpected"
    issue = toolchain_json_schema_issues(json.dumps(payload))
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain JSON schema mismatch was not detected", ""]
    if "toolchain JSON schema mismatch" not in issue_output:
        return ["toolchain JSON schema mismatch was not reported", issue_output]
    if "unexpected JSON key: extra" not in issue_output:
        return ["unexpected JSON key: extra was not reported", issue_output]
    return []


def negative_toolchain_json_schema_missing_check_index():
    payload = build_json_list_payload(EXPECTED_CHECK_NAMES)
    del payload["checks"][0]["index"]
    issue = toolchain_json_schema_issues(json.dumps(payload))
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain JSON schema mismatch was not detected", ""]
    if "toolchain JSON schema mismatch" not in issue_output:
        return ["toolchain JSON schema mismatch was not reported", issue_output]
    if "missing JSON check key: index" not in issue_output:
        return ["missing JSON check key: index was not reported", issue_output]
    return []


def negative_toolchain_json_schema_invalid_check_index():
    payload = build_json_list_payload(EXPECTED_CHECK_NAMES)
    payload["checks"][0]["index"] = "1"
    issue = toolchain_json_schema_issues(json.dumps(payload))
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain JSON schema mismatch was not detected", ""]
    if "toolchain JSON schema mismatch" not in issue_output:
        return ["toolchain JSON schema mismatch was not reported", issue_output]
    if "invalid JSON check index" not in issue_output:
        return ["invalid JSON check index was not reported", issue_output]
    return []


def negative_toolchain_json_schema_invalid_check_name():
    payload = build_json_list_payload(EXPECTED_CHECK_NAMES)
    payload["checks"][0]["name"] = 123
    issue = toolchain_json_schema_issues(json.dumps(payload))
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain JSON schema mismatch was not detected", ""]
    if "toolchain JSON schema mismatch" not in issue_output:
        return ["toolchain JSON schema mismatch was not reported", issue_output]
    if "invalid JSON check name" not in issue_output:
        return ["invalid JSON check name was not reported", issue_output]
    return []


def negative_toolchain_json_schema_checks_not_list():
    payload = build_json_list_payload(EXPECTED_CHECK_NAMES)
    payload["checks"] = {}
    issue = toolchain_json_schema_issues(json.dumps(payload))
    issue_output = "\n".join(issue)
    if not issue:
        return ["toolchain JSON schema mismatch was not detected", ""]
    if "toolchain JSON schema mismatch" not in issue_output:
        return ["toolchain JSON schema mismatch was not reported", issue_output]
    if "JSON checks is not a list" not in issue_output:
        return ["JSON checks is not a list was not reported", issue_output]
    return []


def main():
    failures = []
    for test in (
        positive_current_project,
        negative_missing_mq5_self_test,
        negative_missing_generated_report,
        negative_missing_backtest_set_validator,
        negative_missing_backtest_set_self_test,
        negative_missing_python_tool_safety_validator,
        negative_missing_python_tool_safety_self_test,
        negative_recursive_self_test_inclusion,
        negative_python_tool_safety_child_failure,
        negative_backtest_set_safety_child_failure,
        negative_runtime_parser_input_samples_child_failure,
        negative_missing_toolchain_check_name,
        negative_unexpected_toolchain_check_name,
        negative_python_tool_safety_scan_coverage_failure,
        negative_engineering_toolchain_readonly_failure,
        negative_engineering_toolchain_json_list_readonly_failure,
        negative_engineering_toolchain_pass_order_failure,
        negative_engineering_toolchain_unexpected_pass_line,
        negative_toolchain_list_missing_check,
        negative_toolchain_list_order_failure,
        negative_toolchain_list_does_not_execute_child_checks,
        negative_toolchain_json_list_does_not_execute_child_checks,
        negative_toolchain_list_pass_missing_listed_check,
        negative_toolchain_list_pass_unexpected_listed_check,
        negative_toolchain_list_pass_order_failure,
        negative_toolchain_json_list_missing_check,
        negative_toolchain_json_list_order_failure,
        negative_toolchain_json_list_invalid_json,
        negative_toolchain_json_list_unexpected_check,
        negative_toolchain_three_mode_list_mismatch,
        negative_toolchain_three_mode_pass_mismatch,
        negative_toolchain_three_mode_order_mismatch,
        negative_toolchain_three_mode_json_unexpected_check,
        negative_toolchain_json_schema_missing_name,
        negative_toolchain_json_schema_extra_top_level_key,
        negative_toolchain_json_schema_missing_check_index,
        negative_toolchain_json_schema_invalid_check_index,
        negative_toolchain_json_schema_invalid_check_name,
        negative_toolchain_json_schema_checks_not_list,
    ):
        result = test()
        if result:
            failures.append(result)

    if failures:
        print(SELF_FAIL_TEXT)
        for failure in failures:
            label = failure[0]
            output = failure[1] if len(failure) > 1 else ""
            print(f"- {label}")
            if output:
                print(output)
        return 1

    print(SELF_PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
