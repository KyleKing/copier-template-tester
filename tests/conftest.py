"""PyTest configuration."""

from pathlib import Path

import pytest
from beartype import beartype

from .configuration import TEST_TMP_CACHE, clear_test_cache


@pytest.fixture()
@beartype
def fix_test_cache() -> Path:
    """Fixture to clear and return the test cache directory for use.

    Returns:
        Path: Path to the test cache directory

    """
    clear_test_cache()
    return TEST_TMP_CACHE
