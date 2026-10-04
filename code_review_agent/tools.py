import subprocess
import sys
import os
from pathlib import Path

MAX_CHARS = 20000

TOOLS = [
    {
        "name": "read_file",
        "description": "Read a file from the repo. Path is relative to the repo root.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "search_repo",
        "description": "Search tracked files for a text pattern (like grep). Returns file:line:match.",
        "input_schema": {
            "type": "object",
            "properties": {"pattern": {"type": "string"}},
            "required": ["pattern"],
        },
    },
    {
        "name": "run_tests",
        "description": "Run the repository's Python test suite with pytest and return the results.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def read_file(repo: str, path: str) -> str:
    root = Path(repo).resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        return "Error: path outside repo"
    if not target.is_file():
        return f"Error: {path} not found"
    return target.read_text(errors="replace")[:MAX_CHARS]


def search_repo(repo: str, pattern: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo, "grep", "-n", "-I", "-e", pattern],
        capture_output=True, text=True,
    )
    return result.stdout[:MAX_CHARS] or "No matches"

def run_tests(repo: str) -> str:
    env = {
        key: os.environ[key]
        for key in [
            "PATH",
            "SYSTEMROOT",
            "TEMP",
            "TMP",
            "USERPROFILE",
            "HOME",
        ]
        if key in os.environ
    }

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=60,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return "Test status: ERROR\nTests exceeded the 60-second timeout."

    output = result.stdout

    if result.returncode == 0:
        status = "PASS"
    elif result.returncode == 1:
        status = "FAIL"
    elif result.returncode == 5:
        status = "NO TESTS"
    else:
        status = "ERROR"

    return (
        f"Test status: {status}\n"
        f"Exit code: {result.returncode}\n"
        f"{output[:MAX_CHARS]}"
    )


def run_tool(repo: str, name: str, args: dict) -> str:
    if name == "read_file":
        return read_file(repo, args["path"])
    if name == "search_repo":
        return search_repo(repo, args["pattern"])
    if name == "run_tests":
        return run_tests(repo)
    return f"Error: unknown tool {name}"
