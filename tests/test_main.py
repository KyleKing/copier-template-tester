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
    # Check output from ctt and copier (where order can vary on Windows)
    ret.stdout.matcher.fnmatch_lines([
        'Starting Copier Template Tester for *',
        '*Note: If files were modified, pre-commit will report a failure.',
        '',
        'Using `copier` to create: .ctt/no_all',
    ])
    ret.stderr.matcher.fnmatch_lines_random([
        '*Copying from template*',
    ])
    # Check a few of the created files:
    paths = {pth.relative_to(DEMO_DIR) for pth in (DEMO_DIR / '.ctt').rglob('*.*') if pth.is_file()}
    assert Path('.ctt/no_all/README.md') in paths
    assert Path('.ctt/no_all/.copier-answers.testing_no_all.yml') in paths
    assert Path('.ctt/no_all/.copier-answers.yml') not in paths


@beartype
def test_main_missing_config(shell: Subprocess) -> None:
    ret = run_ctt(shell, cwd=TEST_DATA_DIR)

    assert ret.returncode == 1
    ret.stderr.matcher.fnmatch_lines(['*No configuration file found. Expected: *ctt.toml*'])
