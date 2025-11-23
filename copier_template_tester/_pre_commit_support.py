"""Support running `ctt` in `pre-commit` with VCS abstraction."""

import sys
from pathlib import Path

from corallium.log import get_logger

from ._vcs_utils import get_vcs

logger = get_logger()


def _ls_untracked_dir(base_dir: Path, vcs_type: str = 'auto') -> set[Path]:
    """Use VCS to list all untracked files.

    Args:
        base_dir: Base directory to check for untracked files
        vcs_type: VCS type ('auto', 'git', 'jj'). Defaults to 'auto'.

    Returns:
        Set of paths to untracked files/directories

    """
    vcs = get_vcs(base_dir, vcs_type=vcs_type)
    untracked = vcs.get_untracked_files(base_dir)
    return {base_dir / _d.strip() for _d in untracked if _d}


def check_for_untracked(base_dir: Path, vcs_type: str = 'auto') -> None:
    """Resolve edge case in #3 by raising when pre-commit won't error.

    Args:
        base_dir: Base directory to check for untracked files
        vcs_type: VCS type ('auto', 'git', 'jj'). Defaults to 'auto'.

    """
    if untracked_paths := _ls_untracked_dir(base_dir, vcs_type=vcs_type):
        logger.text('pre-commit error: untracked files must be added', untracked_paths=untracked_paths)
        sys.exit(1)
