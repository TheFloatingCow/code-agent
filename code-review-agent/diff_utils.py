import subprocess

def get_diff(repo_path: str, range_spec: str = None) -> str:
    """Get git diff. range_spec e.g. 'main..HEAD' or None for unstaged changes."""
    cmd = ["git", "-C", repo_path, "diff"]
    if range_spec:
        cmd.append(range_spec)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"git diff failed: {result.stderr}")
    return result.stdout