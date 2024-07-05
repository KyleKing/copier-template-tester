from contextlib import nullcontext as does_not_raise

import pytest
from corallium.log import get_logger

from copier_template_tester._config import _validate_config

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
    ids=[
        'Check an incomplete config',
        'Check a normal config',
    ],
)
def test_validate_config(config: dict, expectation) -> None:  # type: ignore[type-arg]
    with expectation:
        _validate_config(config)
