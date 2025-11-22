"""Shared test fixtures for reducing duplication."""

from pathlib import Path

import pytest
from pytestshellutils.shell import Subprocess
from pytestshellutils.utils.processes import MatchString

from .helpers import run_ctt


@pytest.fixture
def run_ctt_and_check_output(shell: Subprocess):
    """Factory fixture for running CTT and checking standard output patterns."""

    def _run_and_check(*, cwd: Path, subdirname: str) -> tuple[set[Path], MatchString]:
        """Run CTT and verify standard output patterns.

        Args:
            cwd: Directory to run CTT in
            subdirname: Expected subdirectory name in output

        Returns:
            Tuple of (created file paths, stdout matcher)

        """
        ret = run_ctt(shell, cwd=cwd)

        assert ret.returncode == 0, ret.stderr

        # Check output from ctt and copier (where order can vary on Windows)
        ret.stdout.matcher.fnmatch_lines([
            'Starting Copier Template Tester for *',
            '*Note: If files were modified, pre-commit will report a failure.',
            '',
            f'Using `copier` to create: .ctt/{subdirname}',
        ])

        ret.stderr.matcher.fnmatch_lines_random([
            '*Copying from template*',
        ])

        # Collect created files
        paths = {pth.relative_to(cwd) for pth in (cwd / '.ctt').rglob('*.*') if pth.is_file()}
        return paths, ret.stdout

    return _run_and_check
