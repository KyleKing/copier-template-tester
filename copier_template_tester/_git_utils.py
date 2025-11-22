"""Git repository utilities."""

from functools import lru_cache
from pathlib import Path

from corallium.shell import capture_shell


@lru_cache(maxsize=3)
def resolve_git_root_dir(base_dir: Path) -> Path:
    """Resolve the git repository root directory.

    Uses `git rev-parse --show-toplevel` to find the root directory of the
    git repository containing the specified directory. Result is cached for
    performance.

    Args:
        base_dir: Directory within a git repository

    Returns:
        Path to the git repository root directory

    Raises:
        RuntimeError: If git command fails (e.g., not in a git repository)

    """
    cmd = 'git rev-parse --show-toplevel'
    output = capture_shell(cmd=cmd, cwd=base_dir)
    return Path(output.strip())
