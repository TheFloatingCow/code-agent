import subprocess

def get_diff(repo_path: str, range_spec: str = None) -> str:

    """
    Get a Git diff.

    Without a range, compare HEAD against the current working tree,
    including both staged and unstaged tracked changes.

    With a range, compare the specified Git revisions.
    """
     
    cmd = ["git", "-C", repo_path, "diff"]

    if range_spec:
        cmd.append(range_spec)
    else:
        cmd.append("HEAD")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"git diff failed: {result.stderr}")

    return result.stdout