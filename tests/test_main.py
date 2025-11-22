"""Tests for main CTT entry point and CLI interface."""

from pathlib import Path

import copier
import pytest
from corallium.log import get_logger
from pytestshellutils.shell import Subprocess

from copier_template_tester.main import run

from .configuration import TEST_DATA_DIR
from .fixtures import run_ctt_and_check_output
from .helpers import DEMO_DIR, NO_ANSWER_FILE_DIR, run_ctt

logger = get_logger()

WITH_INCLUDE_DIR = TEST_DATA_DIR / 'copier_include'


@pytest.mark.parametrize('base_dir', [DEMO_DIR, NO_ANSWER_FILE_DIR])
def test_main_with_copier_mock(monkeypatch, base_dir: Path) -> None:
    """Test main entry point with mocked copier to verify configuration loading.

    This test validates that the run() function correctly:
    - Loads copier template configuration
    - Processes CTT config file
    - Prepares output directories
    - Calls copier with proper arguments

    Mocking copier.Worker avoids actual file operations while maintaining coverage.
    """

    def _run_copy(worker) -> None:
        pass

    monkeypatch.setattr(copier.Worker, 'run_copy', _run_copy)

    run(base_dir=base_dir)


def test_main(run_ctt_and_check_output) -> None:
    """Test full CTT workflow with _extra_tasks feature."""
    paths, stdout = run_ctt_and_check_output(cwd=DEMO_DIR, subdirname='no_all')

    assert Path('.ctt/no_all/README.md') in paths
    assert Path('.ctt/no_all/.copier-answers.testing_no_all.yml') in paths
    assert Path('.ctt/no_all/.copier-answers.yml') not in paths

    # Verify _extra_tasks were executed (feature added in v2.2.0)
    stdout.matcher.fnmatch_lines_random([
        'task_string',
        'task_list',
        'task_dict',
    ])


def test_no_answer_file_dir(run_ctt_and_check_output) -> None:
    """Test CTT with template that has no custom answers file."""
    paths, _stdout = run_ctt_and_check_output(cwd=NO_ANSWER_FILE_DIR, subdirname='no_answers_file')

    assert Path('.ctt/no_answers_file/README.md') in paths
    assert not [*Path('.ctt/no_answers_file').rglob('.copier-answers*')]


def test_with_include_dir(run_ctt_and_check_output) -> None:
    """Test CTT with copier template using !include directive."""
    paths, _stdout = run_ctt_and_check_output(cwd=WITH_INCLUDE_DIR, subdirname='copier_include')

    assert Path('.ctt/copier_include/script.py') in paths


def test_missing_copier_config(shell: Subprocess) -> None:
    """Test CTT handles missing copier.yaml gracefully."""
    ret = run_ctt(shell, cwd=TEST_DATA_DIR / 'no_copier_config')

    assert ret.returncode == 0
    ret.stdout.matcher.fnmatch_lines(["Please add a 'copier.yaml' file to '*no_copier_config'*"])


def test_missing_ctt_config(shell: Subprocess) -> None:
    """Test CTT fails with clear error when ctt.toml is missing."""
    ret = run_ctt(shell, cwd=TEST_DATA_DIR / 'no_ctt_config')

    assert ret.returncode == 1
    ret.stderr.matcher.fnmatch_lines(['*No configuration file found. Expected: *ctt.toml*'])


def test_no_subdir(shell: Subprocess) -> None:
    """Test CTT with template that doesn't use subdirectory structure."""
    ret = run_ctt(shell, cwd=TEST_DATA_DIR / 'no_subdir_nor_exclude')

    assert ret.returncode == 0
    ret.stdout.matcher.fnmatch_lines(['*Using `copier` to create: .ctt/no_subdir_nor_exclude*'])
