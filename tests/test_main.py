from contextlib import nullcontext as does_not_raise
from pathlib import Path

import copier
import pytest
from beartype import beartype
from corallium.log import get_logger

from copier_template_tester.main import _validate_config, run

from .configuration import TEST_DATA_DIR
from .helpers import DEMO_DIR, add_commit, run_ctt, temporary_git_dir

logger = get_logger()


@pytest.mark.parametrize(
    ('config', 'expectation'),
    [
        (
            {},
            pytest.raises(
                RuntimeError,
                match=r'CTT expected headers like: \[output."<something>"\]',
            ),
        ),
        (
            {'output': {'something': True}},
            does_not_raise(),
        ),
    ],
)
def test_validate_config(config, expectation):
    with expectation:
        _validate_config(config)


def test_main_with_copier_mock(monkeypatch):
    """Only necessary for coverage metrics."""
    @beartype
    def _run_auto(src_path: str, dst_path: Path, **kwargs) -> None:  # noqa: ARG001
        pass

    monkeypatch.setattr(copier, 'run_auto', _run_auto)

    run(base_dir=DEMO_DIR)


def test_main(shell):
    ret = run_ctt(shell, cwd=DEMO_DIR)

    assert ret.returncode == 0
    ret.stdout.matcher.fnmatch_lines(['*Creating:*copier_demo*no_all*', ''])
    # Check output from copier
    ret.stderr.matcher.fnmatch_lines([
        '*Copying from template*',
        '* .copier-answers.yml*',
        '*identical* README.md*',
        '*identical* script.py*',
    ])


def test_untracked_files(shell):
    untracked_file = Path('template_dir/untracked_file.txt')
    with temporary_git_dir(shell, DEMO_DIR) as copier_dir:
        first_pass = run_ctt(shell, cwd=TEST_DATA_DIR, args=[f'--base-dir={copier_dir}'])
        assert first_pass.returncode == 0

        (copier_dir / untracked_file).write_text('Placeholder\n')
        add_commit(shell, cwd=copier_dir)
        ret = run_ctt(shell, cwd=TEST_DATA_DIR, args=[f'--base-dir={copier_dir}', '--check-untracked'])

    assert ret.returncode == 1
    ret.stdout.matcher.fnmatch_lines(['*Creating:*copier_demo*no_all*', ''])
    # Check output from copier
    ret.stderr.matcher.fnmatch_lines([
        '*Copying from template*',
        '*conflict* .copier-answers.yml*',
        f'*create* {untracked_file.name}*',
    ])


def test_main_missing_config(shell):
    ret = run_ctt(shell, cwd=TEST_DATA_DIR)

    assert ret.returncode == 1
    ret.stderr.matcher.fnmatch_lines(['*No configuration file found. Expected: *ctt.toml*'])
