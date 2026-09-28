import subprocess
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
]


def read_file(repo: str, path: str) -> str:
    root = Path(repo).resolve()
    target = (root / path).resolve()
    if root not in target.parents:
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


def run_tool(repo: str, name: str, args: dict) -> str:
    if name == "read_file":
        return read_file(repo, args["path"])
    if name == "search_repo":
        return search_repo(repo, args["pattern"])
    return f"Error: unknown tool {name}"