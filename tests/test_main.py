from pathlib import Path

import pytest
from copier._main import Worker
from corallium.log import get_logger
from pytestshellutils.shell import Subprocess
from pytestshellutils.utils.processes import MatchString

from copier_template_tester.main import run

from .configuration import TEST_DATA_DIR
from .helpers import DEMO_DIR, NO_ANSWER_FILE_DIR, run_ctt

logger = get_logger()

WITH_INCLUDE_DIR = TEST_DATA_DIR / 'copier_include'


@pytest.mark.parametrize('base_dir', [DEMO_DIR, NO_ANSWER_FILE_DIR])
def test_main_with_copier_mock(monkeypatch, base_dir: Path) -> None:
    """Only necessary for coverage metrics, but the .ctt/* files must exist."""

    def _run_copy(worker) -> None:
        pass

    monkeypatch.setattr(Worker, 'run_copy', _run_copy)

    run(base_dir=base_dir)


def check_run_ctt(*, shell: Subprocess, cwd: Path, subdirname: str) -> tuple[set[Path], MatchString, MatchString]:
    ret = run_ctt(shell, cwd=cwd)

    assert ret.returncode == 0, ret.stderr
    # Check output from ctt and copier (where order can vary on Windows)
    ret.stdout.matcher.fnmatch_lines(
        [
            'Starting Copier Template Tester for *',
            '*Note: If files were modified, pre-commit will report a failure.',
            '',
            f'Using `copier` to create: .ctt/{subdirname}',
        ],
    )
    ret.stderr.matcher.fnmatch_lines_random(
        [
            '*Copying from template*',
        ],
    )
    # Check a few of the created files:
    return {pth.relative_to(cwd) for pth in (cwd / '.ctt').rglob('*.*') if pth.is_file()}, ret.stdout, ret.stderr


def test_main(shell: Subprocess) -> None:
    paths, stdout, _stderr = check_run_ctt(shell=shell, cwd=DEMO_DIR, subdirname='no_all')

    assert Path('.ctt/no_all/README.md') in paths
    assert Path('.ctt/no_all/.copier-answers.testing_no_all.yml') in paths
    assert Path('.ctt/no_all/.copier-answers.yml') not in paths
    stdout.matcher.fnmatch_lines_random(
        [
            'task_string',
            'task_list',
            'task_dict',
        ],
    )


def test_no_answer_file_dir(shell: Subprocess) -> None:
    paths, _stdout, _stderr = check_run_ctt(shell=shell, cwd=NO_ANSWER_FILE_DIR, subdirname='no_answers_file')

    assert Path('.ctt/no_answers_file/README.md') in paths
    assert not [*Path('.ctt/no_answers_file').rglob('.copier-answers*')]


def test_with_include_dir(shell: Subprocess) -> None:
    paths, _stdout, _stderr = check_run_ctt(shell=shell, cwd=WITH_INCLUDE_DIR, subdirname='copier_include')

    assert Path('.ctt/copier_include/script.py') in paths


def test_missing_copier_config(shell: Subprocess) -> None:
    ret = run_ctt(shell, cwd=TEST_DATA_DIR / 'no_copier_config')

    assert ret.returncode == 0
    ret.stdout.matcher.fnmatch_lines(["Please add a 'copier.yaml' file to '*no_copier_config'*"])


def test_missing_ctt_config(shell: Subprocess) -> None:
    ret = run_ctt(shell, cwd=TEST_DATA_DIR / 'no_ctt_config')

    assert ret.returncode == 1
    ret.stderr.matcher.fnmatch_lines(['*No configuration file found. Expected: *ctt.toml*'])


def test_no_subdir(shell: Subprocess) -> None:
    ret = run_ctt(shell, cwd=TEST_DATA_DIR / 'no_subdir_nor_exclude')

    assert ret.returncode == 0
    ret.stdout.matcher.fnmatch_lines(['*Using `copier` to create: .ctt/no_subdir_nor_exclude*'])


def test_skip_tasks(shell: Subprocess) -> None:
    paths, stdout, stderr = check_run_ctt(shell=shell, cwd=DEMO_DIR, subdirname='skip_tasks')

    assert Path('.ctt/skip_tasks/README.md') in paths
    stderr.matcher.fnmatch_lines_random(
        [' > Running task 1 of 3: *', ' > Running task 2 of 3: *', ' > Running task 3 of 3: *'],
    )
    stdout.matcher.fnmatch_lines_random(['task_string', 'task_list', 'task_dict'])


def test_pre_tasks(shell: Subprocess) -> None:
    paths, stdout, stderr = check_run_ctt(shell=shell, cwd=DEMO_DIR, subdirname='pre_tasks')

    assert Path('.ctt/pre_tasks/README.md') in paths
    stderr.matcher.fnmatch_lines_random(
        [' > Running task 1 of 5: *', ' > Running task 2 of 5: *', ' > Running task 5 of 5: *'],
    )
    stdout.matcher.fnmatch_lines_random(
        [
            'pre_first',
            'template_task_from_copier_yml',
            'task_string',
        ],
    )
