"""Support running `ctt` in `pre-commit`."""

import sys
from pathlib import Path

from corallium.log import get_logger
from corallium.shell import capture_shell

logger = get_logger()


def _ls_untracked_dir(base_dir: Path) -> set[Path]:
    """Use git to list all untracked files."""
    cmd = 'git ls-files --directory --exclude-standard --no-empty-dir --others'
    output = capture_shell(cmd=cmd, cwd=base_dir)
    return {base_dir / _d.strip() for _d in output.split('\n') if _d}


def check_for_untracked(base_dir: Path) -> None:
    """Resolves the edge case in #3 by raising when pre-commit won't error."""
    if untracked_paths := _ls_untracked_dir(base_dir):
        logger.text('pre-commit error: untracked files must be added', untracked_paths=untracked_paths)
        sys.exit(1)
