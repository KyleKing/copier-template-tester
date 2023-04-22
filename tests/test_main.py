from pathlib import Path

import copier
from beartype import beartype
from corallium.log import get_logger
from pytestshellutils.shell import Subprocess

from copier_template_tester.main import run

from .configuration import TEST_DATA_DIR
from .helpers import DEMO_DIR, run_ctt

logger = get_logger()


@beartype
def test_main_with_copier_mock(monkeypatch) -> None:
    """Only necessary for coverage metrics."""
    @beartype
    def _run_auto(src_path: str, dst_path: Path, **kwargs) -> None:  # noqa: ARG001
        pass

    monkeypatch.setattr(copier, 'run_auto', _run_auto)

    run(base_dir=DEMO_DIR)


@beartype
def test_main(shell: Subprocess) -> None:
    ret = run_ctt(shell, cwd=DEMO_DIR)

    assert ret.returncode == 0
    ret.stdout.matcher.fnmatch_lines(['*Creating:*copier_demo*no_all*', ''])
    # Check output from copier
    ret.stderr.matcher.fnmatch_lines_random([  # Order can vary on Windows
        '*Copying from template*',
        '* .copier-answers.yml*',
        '*identical* README.md*',
        '*identical* script.py*',
    ])


@beartype
def test_main_missing_config(shell: Subprocess) -> None:
    ret = run_ctt(shell, cwd=TEST_DATA_DIR)

    assert ret.returncode == 1
    ret.stderr.matcher.fnmatch_lines(['*No configuration file found. Expected: *ctt.toml*'])
