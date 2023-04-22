"""Support running `ctt` in `pre-commit`."""

import sys
from pathlib import Path

from beartype import beartype
from corallium.log import get_logger
from corallium.shell import capture_shell

logger = get_logger()


@beartype
def _ls_untracked_dir(base_dir: Path) -> set[Path]:
    """Use git to list all untracked files."""
    cmd = 'git ls-files --directory --exclude-standard --no-empty-dir --others'
    output = capture_shell(cmd=cmd, cwd=base_dir)
    return {base_dir / _d.strip() for _d in output.split('\n') if _d}


@beartype
def _is_relative(file_path: Path, directories: set[Path]) -> bool:
    """Returns True if the file_path is relative to any of the directories."""
    return any(file_path.is_relative_to(directory) for directory in directories)


@beartype
def check_for_untracked(output_paths: set[Path], base_dir: Path) -> None:
    """Resolves the edge case in #3 by raising when pre-commit won't error."""
    if untracked_paths := {
        untracked for untracked in _ls_untracked_dir(base_dir)
        if _is_relative(untracked, output_paths)
    }:
        logger.text('pre-commit error: untracked files must be added', untracked_paths=untracked_paths)
        sys.exit(1)
