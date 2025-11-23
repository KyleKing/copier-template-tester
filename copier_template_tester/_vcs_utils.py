"""Version Control System abstraction layer.

Provides a common interface for different VCS backends (Git, Jujutsu, etc.)
to support CTT operations across different version control systems.
"""

import subprocess
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Protocol, runtime_checkable

from corallium.shell import capture_shell


@runtime_checkable
class VCSBackend(Protocol):
    """Protocol defining VCS backend interface."""

    def get_root_dir(self, cwd: Path) -> Path:
        """Get repository root directory.

        Args:
            cwd: Current working directory within the repository

        Returns:
            Path to the repository root

        Raises:
            RuntimeError: If not in a VCS repository or command fails

        """
        ...

    def get_untracked_files(self, cwd: Path) -> list[str]:
        """Get list of untracked files.

        Args:
            cwd: Current working directory within the repository

        Returns:
            List of untracked file paths relative to repository root

        Raises:
            RuntimeError: If VCS command fails

        """
        ...

    def is_repository(self, path: Path) -> bool:
        """Check if path is within a VCS repository.

        Args:
            path: Path to check

        Returns:
            True if path is within a VCS repository

        """
        ...


class GitVCS:
    """Git version control implementation."""

    def get_root_dir(self, cwd: Path) -> Path:
        """Get git repository root directory.

        Args:
            cwd: Current working directory within the git repository

        Returns:
            Path to the git repository root

        Raises:
            RuntimeError: If not in a git repository or command fails

        """
        cmd = 'git rev-parse --show-toplevel'
        output = capture_shell(cmd=cmd, cwd=cwd)
        return Path(output.strip())

    def get_untracked_files(self, cwd: Path) -> list[str]:
        """Get list of untracked files using git status.

        Args:
            cwd: Current working directory within the git repository

        Returns:
            List of untracked file paths relative to repository root

        Raises:
            RuntimeError: If git command fails

        """
        cmd = 'git status --porcelain'
        output = capture_shell(cmd=cmd, cwd=cwd)

        untracked = []
        for line in output.strip().split('\n'):
            if not line:
                continue
            # Git status format: XY filename
            # ?? = untracked file
            if line.startswith('??'):
                filename = line[3:].strip()
                untracked.append(filename)

        return untracked

    def is_repository(self, path: Path) -> bool:
        """Check if path is within a git repository.

        Args:
            path: Path to check

        Returns:
            True if path is within a git repository

        """
        # Check for .git directory
        if (path / '.git').exists():
            return True

        # Try running git command
        try:
            self.get_root_dir(path)
            return True
        except (RuntimeError, subprocess.CalledProcessError):
            return False


class JujutsuVCS:
    """Jujutsu (jj) version control implementation."""

    def get_root_dir(self, cwd: Path) -> Path:
        """Get jj workspace root directory.

        Args:
            cwd: Current working directory within the jj workspace

        Returns:
            Path to the jj workspace root

        Raises:
            RuntimeError: If not in a jj workspace or command fails

        """
        cmd = 'jj workspace root'
        output = capture_shell(cmd=cmd, cwd=cwd)
        return Path(output.strip())

    def get_untracked_files(self, cwd: Path) -> list[str]:
        """Get list of untracked files using jj status.

        Args:
            cwd: Current working directory within the jj workspace

        Returns:
            List of untracked file paths relative to workspace root

        Raises:
            RuntimeError: If jj command fails

        """
        cmd = 'jj status'
        output = capture_shell(cmd=cmd, cwd=cwd)

        # Parse jj status output
        # Format varies but typically shows "? filename" for untracked
        untracked = []
        for line in output.strip().split('\n'):
            if not line:
                continue
            # Look for untracked file indicators
            if line.startswith('?') or 'untracked' in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    filename = parts[-1]
                    untracked.append(filename)

        return untracked

    def is_repository(self, path: Path) -> bool:
        """Check if path is within a jj workspace.

        Args:
            path: Path to check

        Returns:
            True if path is within a jj workspace

        """
        # Check for .jj directory
        if (path / '.jj').exists():
            return True

        # Try running jj command
        try:
            self.get_root_dir(path)
            return True
        except (RuntimeError, subprocess.CalledProcessError):
            return False


@lru_cache(maxsize=10)
def detect_vcs(cwd: Path) -> VCSBackend:
    """Auto-detect which VCS is in use.

    Checks for VCS markers in order of preference:
    1. Jujutsu (.jj directory or jj commands work)
    2. Git (.git directory or git commands work)

    Args:
        cwd: Directory to check for VCS

    Returns:
        Detected VCS backend instance

    Raises:
        RuntimeError: If no VCS is detected

    """
    # Check for .jj directory (Jujutsu workspace)
    if (cwd / '.jj').exists():
        return JujutsuVCS()

    # Check for .git directory (Git repository)
    if (cwd / '.git').exists():
        return GitVCS()

    # Try running jj command
    try:
        jj = JujutsuVCS()
        jj.get_root_dir(cwd)
        return jj
    except (RuntimeError, subprocess.CalledProcessError):
        pass

    # Try running git command
    try:
        git = GitVCS()
        git.get_root_dir(cwd)
        return git
    except (RuntimeError, subprocess.CalledProcessError):
        pass

    msg = f'No VCS detected in {cwd} (tried: jujutsu, git)'
    raise RuntimeError(msg)


def get_vcs(cwd: Path, vcs_type: str = 'auto') -> VCSBackend:
    """Get VCS backend instance.

    Args:
        cwd: Directory within VCS repository
        vcs_type: VCS type ('auto', 'git', 'jj', or 'jujutsu')

    Returns:
        VCS backend instance

    Raises:
        ValueError: If vcs_type is invalid
        RuntimeError: If VCS cannot be detected (auto mode) or initialized

    """
    if vcs_type == 'auto':
        return detect_vcs(cwd)
    if vcs_type == 'git':
        return GitVCS()
    if vcs_type in ('jj', 'jujutsu'):
        return JujutsuVCS()

    valid_types = ['auto', 'git', 'jj', 'jujutsu']
    msg = f"Invalid vcs_type '{vcs_type}'. Must be one of: {valid_types}"
    raise ValueError(msg)
