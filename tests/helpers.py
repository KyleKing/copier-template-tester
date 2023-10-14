import shutil
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from corallium.log import get_logger
from pytestshellutils.shell import Subprocess
from pytestshellutils.utils.processes import ProcessResult

from .configuration import TEST_DATA_DIR, TEST_DIR

logger = get_logger()

CTT_CMD = ['poetry', 'run', 'ctt']
DEMO_DIR = TEST_DATA_DIR / 'copier_demo'
NO_ANSWER_FILE_DIR = TEST_DATA_DIR / 'no_answers_file_demo'


class ExpectedError(Exception):
    """Test-only exception."""


def _format_ret_kwargs(ret: ProcessResult) -> dict[Literal['stdout', 'stderr'], str]:
    """Cleanup the shell output for printing."""
    return {'stdout': f'`{ret.stdout.strip()}`', 'stderr': f'`{ret.stderr.strip()}`'}


def run_ctt(shell: Subprocess, cwd: Path, args: list[str] | None = None) -> ProcessResult:
    """Run `ctt` in the specified directory."""
    ret = shell.run(*CTT_CMD, *(args or []), cwd=cwd)
    logger.text('ran ctt', **_format_ret_kwargs(ret))
    return ret


def run_check(shell: Subprocess, *args, **kwargs) -> ProcessResult:
    """Check that the shell process completed with exit code 0."""
    ret = shell.run(*args, **kwargs)
    logger.text('run_check', _args=args, _kwargs=kwargs, **_format_ret_kwargs(ret))
    if ret.returncode != 0:
        raise RuntimeError(f'Failed to run {args} with {kwargs}')
    return ret


def add_commit(shell: Subprocess, cwd: Path) -> None:
    """Add and commit all files within the specified directory."""
    assert not cwd.is_relative_to(TEST_DIR.parent)  # Prevent accidents!
    run_check(shell, 'git', 'add', '.', cwd=cwd)
    run_check(shell, 'git', 'commit', '-m="add-commit"', cwd=cwd)


@contextmanager
def temporary_git_dir(shell: Subprocess, *, source_dir: Path | None = None) -> Generator[Path, None, None]:
    """Initialize a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        working_dir = Path(tmp_dir) / (source_dir.name if source_dir else 'subdir')
        if source_dir:
            shutil.copytree(source_dir, working_dir)
        working_dir.mkdir(exist_ok=True)

        run_check(shell, 'git', 'init', cwd=working_dir)
        # Required for Windows CI and works without issue everywhere else
        run_check(shell, 'git', 'config', '--local', 'user.email', 'tester@py.test', cwd=working_dir)
        run_check(shell, 'git', 'config', '--local', 'user.name', 'Pytest', cwd=working_dir)
        if source_dir:
            add_commit(shell, cwd=working_dir)

        yield working_dir
