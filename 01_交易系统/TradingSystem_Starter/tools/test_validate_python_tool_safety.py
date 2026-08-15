from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap


PASS_TEXT = "Python tool safety validation passed"
FAIL_TEXT = "Python tool safety validation failed"
SELF_TEST_PASS_TEXT = "Python tool safety self-test passed"
SELF_TEST_FAIL_TEXT = "Python tool safety self-test failed"
REQUIRED_V020_TOOL_PATHS = [
    Path("tools/validate_runtime_parser_input_samples.py"),
    Path("tools/test_validate_runtime_parser_input_samples.py"),
    Path("tools/generate_runtime_parser_input_samples_audit.py"),
]


def combined_output(result):
    return f"{result.stdout}\n{result.stderr}"


def run_validator(project_root):
    return subprocess.run(
        [sys.executable, "tools/validate_python_tool_safety.py"],
        cwd=project_root,
        text=True,
        capture_output=True,
    )


def write_tool(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def copy_validator(real_project_root, temp_project):
    source = real_project_root / "tools" / "validate_python_tool_safety.py"
    target = temp_project / "tools" / "validate_python_tool_safety.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def run_temp_case(real_project_root, files):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_project = Path(temp_dir)
        copy_validator(real_project_root, temp_project)
        for relative_path, content in files.items():
            write_tool(temp_project / relative_path, content)
        return run_validator(temp_project)


def expect_success(result, required_texts):
    output = combined_output(result)
    if result.returncode != 0 or PASS_TEXT not in output:
        return False
    return all(required_text in output for required_text in required_texts)


def expect_failure(result, required_texts):
    output = combined_output(result)
    if result.returncode == 0 or FAIL_TEXT not in output:
        return False
    return all(required_text in output for required_text in required_texts)


def python_tool_scan_count_issues(project_root):
    result = run_validator(project_root)
    output = combined_output(result)
    match = re.search(r"scanned python tools count:\s*(\d+)", output)
    expected_count = len(list((project_root / "tools").glob("*.py")))
    if not match:
        return ["python tool scan count mismatch", "scanned python tools count not found"]

    actual_count = int(match.group(1))
    if actual_count != expected_count:
        return [
            "python tool scan count mismatch",
            f"expected scanned python tools count {expected_count} but got {actual_count}",
        ]
    return []


def python_tool_required_v020_coverage_issues(project_root):
    scanned_paths = {
        path.relative_to(project_root)
        for path in (project_root / "tools").glob("*.py")
    }
    missing_paths = [
        required_path
        for required_path in REQUIRED_V020_TOOL_PATHS
        if required_path not in scanned_paths
    ]
    if not missing_paths:
        return []

    return [
        "python tool v0.2.0 coverage missing",
        *[str(path).replace("\\", "/") for path in missing_paths],
    ]


def test_positive_current_project(real_project_root):
    result = run_validator(real_project_root)
    return expect_success(
        result,
        [
            "forbidden import findings: 0",
            "forbidden external command findings: 0",
        ],
    )


def test_positive_scan_count_matches(real_project_root):
    return not python_tool_scan_count_issues(real_project_root)


def test_positive_required_v020_tool_coverage(real_project_root):
    return not python_tool_required_v020_coverage_issues(real_project_root)


def test_required_v020_tool_coverage_missing_detected(real_project_root):
    del real_project_root
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_project = Path(temp_dir)
        for required_path in REQUIRED_V020_TOOL_PATHS[:-1]:
            write_tool(temp_project / required_path, "VALUE = 1\n")
        issues = python_tool_required_v020_coverage_issues(temp_project)

    output = "\n".join(issues)
    return (
        bool(issues)
        and "python tool v0.2.0 coverage missing" in output
        and "tools/generate_runtime_parser_input_samples_audit.py" in output
    )


def test_forbidden_import_requests(real_project_root):
    result = run_temp_case(
        real_project_root,
        {"tools/bad_tool.py": "import requests\n"},
    )
    return expect_failure(result, ["forbidden import", "requests"])


def test_forbidden_import_pandas(real_project_root):
    result = run_temp_case(
        real_project_root,
        {"tools/bad_tool.py": "import pandas as pd\n"},
    )
    return expect_failure(result, ["forbidden import", "pandas"])


def test_forbidden_import_numpy(real_project_root):
    result = run_temp_case(
        real_project_root,
        {"tools/bad_tool.py": "from numpy import array\n"},
    )
    return expect_failure(result, ["forbidden import", "numpy"])


def test_forbidden_import_alias_requests(real_project_root):
    result = run_temp_case(
        real_project_root,
        {"tools/bad_tool.py": "import requests as rq\n"},
    )
    return expect_failure(result, ["forbidden import", "requests"])


def test_forbidden_from_import_pandas(real_project_root):
    result = run_temp_case(
        real_project_root,
        {"tools/bad_tool.py": "from pandas import DataFrame\n"},
    )
    return expect_failure(result, ["forbidden import", "pandas"])


def test_forbidden_nested_import_numpy(real_project_root):
    result = run_temp_case(
        real_project_root,
        {"tools/bad_tool.py": "from numpy.random import rand\n"},
    )
    return expect_failure(result, ["forbidden import", "numpy"])


def test_forbidden_import_alias_metatrader5(real_project_root):
    result = run_temp_case(
        real_project_root,
        {"tools/bad_tool.py": "import MetaTrader5 as mt5\n"},
    )
    return expect_failure(result, ["forbidden import", "MetaTrader5"])


def test_forbidden_from_import_ccxt(real_project_root):
    result = run_temp_case(
        real_project_root,
        {"tools/bad_tool.py": "from ccxt import binance\n"},
    )
    return expect_failure(result, ["forbidden import", "ccxt"])


def test_forbidden_external_git(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "tools/bad_tool.py": """
                import subprocess
                subprocess.run(["git", "status"])
            """,
        },
    )
    return expect_failure(result, ["forbidden external command", "git"])


def test_forbidden_external_git_exe(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "tools/bad_tool.py": """
                import subprocess
                subprocess.check_call(["git.exe", "status"])
            """,
        },
    )
    return expect_failure(result, ["forbidden external command", "git.exe"])


def test_forbidden_external_git_tuple(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "tools/bad_tool.py": """
                import subprocess
                subprocess.check_output(("git", "status"))
            """,
        },
    )
    return expect_failure(result, ["forbidden external command", "git"])


def test_forbidden_external_curl_popen(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "tools/bad_tool.py": """
                import subprocess
                subprocess.Popen(["curl", "https://example.com"])
            """,
        },
    )
    return expect_failure(result, ["forbidden external command", "curl"])


def test_forbidden_external_git_string(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "tools/bad_tool.py": """
                import subprocess
                subprocess.run("git status")
            """,
        },
    )
    return expect_failure(result, ["forbidden external command", "git"])


def test_forbidden_external_pip(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "tools/bad_tool.py": """
                import os
                os.system("pip install requests")
            """,
        },
    )
    return expect_failure(result, ["forbidden external command", "pip"])


def test_forbidden_external_python_m_pip(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "tools/bad_tool.py": """
                import subprocess
                subprocess.run(["python", "-m", "pip", "install", "requests"])
            """,
        },
    )
    return expect_failure(result, ["forbidden external command", "python -m pip"])


def test_forbidden_external_pip3(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "tools/bad_tool.py": """
                import os
                os.system("pip3 install numpy")
            """,
        },
    )
    return expect_failure(result, ["forbidden external command", "pip3"])


def test_forbidden_external_wget(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "tools/bad_tool.py": """
                import os
                os.system("wget https://example.com")
            """,
        },
    )
    return expect_failure(result, ["forbidden external command", "wget"])


def test_forbidden_external_powershell_invoke_webrequest(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "tools/bad_tool.py": """
                import os
                os.system("powershell Invoke-WebRequest https://example.com")
            """,
        },
    )
    return expect_failure(
        result,
        ["forbidden external command", "powershell Invoke-WebRequest"],
    )


def test_forbidden_external_powershell_iwr(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "tools/bad_tool.py": """
                import os
                os.system("powershell iwr https://example.com")
            """,
        },
    )
    return expect_failure(result, ["forbidden external command", "powershell iwr"])


def test_safe_string_not_flagged(real_project_root):
    result = run_temp_case(
        real_project_root,
        {
            "tools/safe_tool.py": '''
                TEXT = "git add git commit pip install curl wget OrderSend CTrade Buy Sell"
            ''',
        },
    )
    return expect_success(result, [PASS_TEXT])


def test_invalid_python_syntax(real_project_root):
    result = run_temp_case(
        real_project_root,
        {"tools/bad_syntax.py": "def broken(:\n"},
    )
    return expect_failure(result, ["could not parse Python AST"])


def test_scan_count_mismatch_detected(real_project_root):
    del real_project_root
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_project = Path(temp_dir)
        write_tool(
            temp_project / "tools" / "validate_python_tool_safety.py",
            """
                print("Python tool safety validation passed")
                print("scanned python tools count: 1")
                print("forbidden import findings: 0")
                print("forbidden external command findings: 0")
            """,
        )
        write_tool(temp_project / "tools" / "a.py", "VALUE = 1\n")
        write_tool(temp_project / "tools" / "b.py", "VALUE = 2\n")
        issues = python_tool_scan_count_issues(temp_project)

    output = "\n".join(issues)
    return (
        bool(issues)
        and "python tool scan count mismatch" in output
        and "expected scanned python tools count" in output
    )


def main():
    real_project_root = Path(__file__).resolve().parents[1]
    checks = [
        ("positive validation did not pass", test_positive_current_project),
        ("python tool scan count mismatch", test_positive_scan_count_matches),
        (
            "v0.2.0 runtime parser input sample tools were not covered",
            test_positive_required_v020_tool_coverage,
        ),
        (
            "missing v0.2.0 runtime parser input sample tool coverage was not detected",
            test_required_v020_tool_coverage_missing_detected,
        ),
        ("forbidden import requests was not detected", test_forbidden_import_requests),
        ("forbidden import pandas was not detected", test_forbidden_import_pandas),
        ("forbidden import numpy was not detected", test_forbidden_import_numpy),
        (
            "forbidden import alias requests was not detected",
            test_forbidden_import_alias_requests,
        ),
        (
            "forbidden from-import pandas was not detected",
            test_forbidden_from_import_pandas,
        ),
        (
            "forbidden nested import numpy was not detected",
            test_forbidden_nested_import_numpy,
        ),
        (
            "forbidden import alias MetaTrader5 was not detected",
            test_forbidden_import_alias_metatrader5,
        ),
        ("forbidden from-import ccxt was not detected", test_forbidden_from_import_ccxt),
        ("forbidden external command git was not detected", test_forbidden_external_git),
        (
            "forbidden external command git.exe was not detected",
            test_forbidden_external_git_exe,
        ),
        (
            "forbidden external command git tuple was not detected",
            test_forbidden_external_git_tuple,
        ),
        (
            "forbidden external command curl was not detected",
            test_forbidden_external_curl_popen,
        ),
        (
            "forbidden external command git string was not detected",
            test_forbidden_external_git_string,
        ),
        ("forbidden external command pip was not detected", test_forbidden_external_pip),
        (
            "forbidden external command python -m pip was not detected",
            test_forbidden_external_python_m_pip,
        ),
        ("forbidden external command pip3 was not detected", test_forbidden_external_pip3),
        ("forbidden external command wget was not detected", test_forbidden_external_wget),
        (
            "forbidden external command powershell Invoke-WebRequest was not detected",
            test_forbidden_external_powershell_invoke_webrequest,
        ),
        (
            "forbidden external command powershell iwr was not detected",
            test_forbidden_external_powershell_iwr,
        ),
        ("safe string false positive detected", test_safe_string_not_flagged),
        ("invalid Python syntax was not detected", test_invalid_python_syntax),
        ("python tool scan count mismatch was not detected", test_scan_count_mismatch_detected),
    ]

    failures = []
    for failure_message, check in checks:
        if not check(real_project_root):
            failures.append(failure_message)

    if failures:
        print(SELF_TEST_FAIL_TEXT)
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(SELF_TEST_PASS_TEXT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
