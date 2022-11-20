from contextlib import nullcontext as does_not_raise
from pathlib import Path

import copier
import pytest
from beartype import beartype

from copier_template_tester.main import _validate_config, run

from .configuration import TEST_DATA_DIR

CTT_CMD = ['poetry', 'run', 'ctt']


@pytest.mark.parametrize(
    ('config', 'expectation'),
    [
        (
            {},
            pytest.raises(
                RuntimeError,
                match=r'CTT expected:\n\[ctt\]\nsource_directory="\.\.\."',
            ),
        ),
        (
            {'ctt': {'source_directory': 'something'}},
            pytest.raises(
                RuntimeError,
                match=r'CTT expected headers like: \[output."<something>"\]',
            ),
        ),
        (
            {'ctt': {'source_directory': 'something'}, 'output': {'something': True}},
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
    def _run_auto(src_path: str, dst_path: Path, **kwargs) -> None:
        pass

    monkeypatch.setattr(copier, 'run_auto', _run_auto)

    run(base_dir=TEST_DATA_DIR / 'copier_demo')


def test_main(shell):
    ret = shell.run(*CTT_CMD, cwd=TEST_DATA_DIR / 'copier_demo')

    assert ret.returncode == 0
    ret.stdout.matcher.fnmatch_lines_random(['*Creating:*copier_demo*no_all*'])
    ret.stderr.matcher.fnmatch_lines_random([
        '*Copying from template*',
        '*.copier-answers.yml*',
    ])


def test_main_missing_config(shell):
    ret = shell.run(*CTT_CMD, cwd=TEST_DATA_DIR)

    assert ret.returncode == 1
    ret.stderr.matcher.fnmatch_lines_random(['*No configuration file found. Expected: *ctt.toml*'])
