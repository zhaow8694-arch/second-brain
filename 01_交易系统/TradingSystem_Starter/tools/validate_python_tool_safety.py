from pathlib import Path
import ast
import sys


FORBIDDEN_IMPORTS = {
    "MetaTrader5",
    "ccxt",
    "requests",
    "pandas",
    "numpy",
}

SUBPROCESS_METHODS = {
    "run",
    "call",
    "check_call",
    "check_output",
    "Popen",
}

FORBIDDEN_COMMANDS = {
    "git",
    "git.exe",
    "curl",
    "curl.exe",
    "wget",
    "wget.exe",
    "pip",
    "pip.exe",
    "pip3",
    "pip3.exe",
}


def relative_path(path, project_root):
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def top_level_module(module_name):
    return module_name.split(".", 1)[0] if module_name else ""


def constant_string(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = call_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
        return node.attr
    return ""


def first_command_token(command):
    if isinstance(command, (list, tuple)):
        if not command:
            return ""
        return str(command[0]).lower()
    if isinstance(command, str):
        parts = command.strip().split()
        return parts[0].lower() if parts else ""
    return ""


def literal_command_argument(node):
    value = constant_string(node)
    if value is not None:
        return value

    if isinstance(node, (ast.List, ast.Tuple)):
        values = []
        for item in node.elts:
            item_value = constant_string(item)
            if item_value is None:
                return None
            values.append(item_value)
        return values

    return None


def is_forbidden_external_command(command):
    first_token = first_command_token(command)
    if first_token in FORBIDDEN_COMMANDS:
        return first_token

    if isinstance(command, (list, tuple)):
        lowered = [part.lower() for part in command]
        if len(lowered) >= 3 and lowered[0] in {"python", "python.exe", "python3", "python3.exe"}:
            if lowered[1] == "-m" and lowered[2] == "pip":
                return "python -m pip"
        if lowered and lowered[0] in {"powershell", "powershell.exe", "pwsh", "pwsh.exe"}:
            if "iwr" in lowered[1:]:
                return "powershell iwr"
            if "invoke-webrequest" in lowered[1:]:
                return "powershell Invoke-WebRequest"

    if isinstance(command, str):
        lowered = command.strip().lower()
        if lowered.startswith(("python -m pip", "python.exe -m pip", "python3 -m pip", "python3.exe -m pip")):
            return "python -m pip"
        if lowered.startswith(("powershell iwr", "powershell.exe iwr")):
            return "powershell iwr"
        if lowered.startswith(("powershell invoke-webrequest", "powershell.exe invoke-webrequest")):
            return "powershell Invoke-WebRequest"
        if lowered.startswith(("pwsh iwr", "pwsh.exe iwr")):
            return "powershell iwr"
        if lowered.startswith(("pwsh invoke-webrequest", "pwsh.exe invoke-webrequest")):
            return "powershell Invoke-WebRequest"

    return ""


def collect_aliases(tree):
    subprocess_aliases = {"subprocess"}
    os_aliases = {"os"}
    subprocess_function_aliases = set()
    os_system_aliases = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "subprocess":
                    subprocess_aliases.add(alias.asname or alias.name)
                if alias.name == "os":
                    os_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module == "subprocess":
                for alias in node.names:
                    if alias.name in SUBPROCESS_METHODS:
                        subprocess_function_aliases.add(alias.asname or alias.name)
            elif node.module == "os":
                for alias in node.names:
                    if alias.name == "system":
                        os_system_aliases.add(alias.asname or alias.name)

    return subprocess_aliases, os_aliases, subprocess_function_aliases, os_system_aliases


def is_checked_external_call(node, aliases):
    subprocess_aliases, os_aliases, subprocess_function_aliases, os_system_aliases = aliases
    name = call_name(node.func)

    for alias in subprocess_aliases:
        prefix = f"{alias}."
        if name.startswith(prefix) and name[len(prefix) :] in SUBPROCESS_METHODS:
            return True

    for alias in os_aliases:
        if name == f"{alias}.system":
            return True

    return name in subprocess_function_aliases or name in os_system_aliases


def validate_imports(tree, display_path):
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = top_level_module(alias.name)
                if module in FORBIDDEN_IMPORTS:
                    issues.append(
                        f"{display_path}:{node.lineno} forbidden import: {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            module = top_level_module(node.module or "")
            if module in FORBIDDEN_IMPORTS:
                issues.append(
                    f"{display_path}:{node.lineno} forbidden import: {node.module}"
                )
    return issues


def validate_external_calls(tree, display_path):
    issues = []
    aliases = collect_aliases(tree)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not is_checked_external_call(node, aliases):
            continue
        if not node.args:
            continue

        command = literal_command_argument(node.args[0])
        if command is None:
            continue

        forbidden = is_forbidden_external_command(command)
        if forbidden:
            issues.append(
                f"{display_path}:{node.lineno} forbidden external command: {forbidden}"
            )

    return issues


def validate_python_file(path, project_root):
    display_path = relative_path(path, project_root)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        line = exc.lineno or 1
        return [f"{display_path}:{line} could not parse Python AST: {exc.msg}"]

    issues = []
    issues.extend(validate_imports(tree, display_path))
    issues.extend(validate_external_calls(tree, display_path))
    return issues


def validate_project(project_root):
    tools_dir = project_root / "tools"
    if not tools_dir.exists():
        return [f"{relative_path(tools_dir, project_root)} directory not found"], 0
    if not tools_dir.is_dir():
        return [f"{relative_path(tools_dir, project_root)} is not a directory"], 0

    python_files = sorted(tools_dir.glob("*.py"))
    if not python_files:
        return [f"{relative_path(tools_dir, project_root)} contains no .py files"], 0

    issues = []
    for python_file in python_files:
        issues.extend(validate_python_file(python_file, project_root))

    return issues, len(python_files)


def main():
    project_root = Path(__file__).resolve().parents[1]
    issues, scanned_count = validate_project(project_root)

    if issues:
        print("Python tool safety validation failed")
        print("Issues:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Python tool safety validation passed")
    print(f"scanned python tools count: {scanned_count}")
    print("forbidden import findings: 0")
    print("forbidden external command findings: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
