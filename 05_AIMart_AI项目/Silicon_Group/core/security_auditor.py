import os
import re

SENSITIVE_PATTERNS = [
    r'sk-[A-Za-z0-9]{20,}',
    r'api[-_]?key["\s:=]+["\'][A-Za-z0-9_\-]{16,}["\']',
    r'secret["\s:=]+["\'][A-Za-z0-9_\-]{16,}["\']',
    r'token["\s:=]+["\'][A-Za-z0-9_\-]{16,}["\']',
    r'password["\s:=]+["\'][^"\']{6,}["\']',
]


def scan_file_for_leaks(filepath: str) -> list:
    issues = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                for pattern in SENSITIVE_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        masked = re.sub(pattern, "***REDACTED***", line)
                        issues.append({
                            "file": filepath,
                            "line": i,
                            "content": masked.strip(),
                        })
                        break
    except Exception as e:
        issues.append({"file": filepath, "error": str(e)})
    return issues


def scan_project(directory: str = ".") -> dict:
    report = {
        "scanned_files": 0,
        "leaks_found": 0,
        "details": [],
    }
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith((".", "node_modules", "venv", "__pycache__"))]
        for f in files:
            if f.endswith((".py", ".env", ".md", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini")):
                path = os.path.join(root, f)
                report["scanned_files"] += 1
                issues = scan_file_for_leaks(path)
                if issues:
                    report["leaks_found"] += len(issues)
                    report["details"].extend(issues)
    return report
