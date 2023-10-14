from pathlib import Path

import copier
import pytest
from beartype import beartype
from corallium.log import get_logger
from pytestshellutils.shell import Subprocess

from copier_template_tester.main import run

from .configuration import TEST_DATA_DIR
from .helpers import DEMO_DIR, NO_ANSWER_FILE_DIR, run_ctt

logger = get_logger()


@pytest.mark.parametrize('base_dir', [DEMO_DIR, NO_ANSWER_FILE_DIR])
@beartype
def test_main_with_copier_mock(monkeypatch, base_dir: Path) -> None:
    """Only necessary for coverage metrics."""
    @beartype
    def _run_copy(src_path: str, dst_path: Path, **kwargs) -> None:  # noqa: ARG001
        pass

    monkeypatch.setattr(copier, 'run_copy', _run_copy)

    run(base_dir=base_dir)


@beartype
def check_run_ctt(*, shell: Subprocess, cwd: Path, subdirname: str) -> set[Path]:
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
    # Check a few of the created files:
    return {pth.relative_to(cwd) for pth in (cwd / '.ctt').rglob('*.*') if pth.is_file()}


@beartype
def test_main(shell: Subprocess) -> None:
    paths = check_run_ctt(shell=shell, cwd=DEMO_DIR, subdirname='no_all')

    assert Path('.ctt/no_all/README.md') in paths
    assert Path('.ctt/no_all/.copier-answers.testing_no_all.yml') in paths
    assert Path('.ctt/no_all/.copier-answers.yml') not in paths


@beartype
def test_no_answer_file_dir(shell: Subprocess) -> None:
    paths = check_run_ctt(shell=shell, cwd=NO_ANSWER_FILE_DIR, subdirname='no_answers_file')

    assert Path('.ctt/no_answers_file/README.md') in paths
    assert not [*Path('.ctt/no_answers_file').rglob('.copier-answers*')]


@beartype
def test_main_missing_config(shell: Subprocess) -> None:
    ret = run_ctt(shell, cwd=TEST_DATA_DIR)

    assert ret.returncode == 1
    ret.stderr.matcher.fnmatch_lines(['*No configuration file found. Expected: *ctt.toml*'])
