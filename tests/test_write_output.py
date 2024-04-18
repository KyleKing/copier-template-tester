from pathlib import Path

import pytest
from beartype import beartype

from copier_template_tester._write_output import (
    DEFAULT_ANSWER_FILE_NAME,  # noqa: PLC2701
    _resolve_git_root_dir,  # noqa: PLC2701
    _stabilize,  # noqa: PLC2701
)

from .helpers import TEST_DATA_DIR

_ANSWERS_PATH = Path('project-subdir').absolute() / DEFAULT_ANSWER_FILE_NAME


@pytest.mark.parametrize(
    ('line', 'expected'),
    [
        (
            # https://github.com/KyleKing/copier-template-tester/issues/16
            f'_src_path: {_ANSWERS_PATH.parent.as_posix()}',
            '_src_path: project-subdir',
        ),
        (
            # https://github.com/KyleKing/copier-template-tester/issues/20
            '_commit: v6.4.0-0',
            '_commit: HEAD',
        ),

    ],
)
@beartype
def test_stabilize(line: str, expected: str) -> None:
    assert _stabilize(line, _ANSWERS_PATH) == expected


@beartype
def test_resolve_git_root_dir() -> None:
    assert _resolve_git_root_dir(TEST_DATA_DIR) == TEST_DATA_DIR.parents[1]
