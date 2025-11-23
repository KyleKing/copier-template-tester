"""Git repository utilities with VCS abstraction support."""

from functools import lru_cache
from pathlib import Path

from ._vcs_utils import get_vcs


@lru_cache(maxsize=3)
def resolve_git_root_dir(base_dir: Path, vcs_type: str = 'auto') -> Path:
    """Resolve the VCS repository root directory.

    Uses VCS abstraction layer to support multiple version control systems.
    Defaults to auto-detection but can be explicitly specified.

    Args:
        base_dir: Directory within a VCS repository
        vcs_type: VCS type ('auto', 'git', 'jj'). Defaults to 'auto'.

    Returns:
        Path to the VCS repository root directory

    Raises:
        RuntimeError: If VCS command fails (e.g., not in a repository)
        ValueError: If vcs_type is invalid

    """
    vcs = get_vcs(base_dir, vcs_type=vcs_type)
    return vcs.get_root_dir(base_dir)
