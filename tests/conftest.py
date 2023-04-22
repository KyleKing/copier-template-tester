"""PyTest configuration."""

import logging
from functools import partial
from pathlib import Path

import pytest
from beartype import beartype
from corallium.log import configure_logger
from corallium.loggers.rich_printer import rich_printer
from corallium.loggers.styles import STYLES
from rich.console import Console

from .configuration import TEST_TMP_CACHE, clear_test_cache

configure_logger(
    log_level=logging.DEBUG,
    # Ensure that the log output isn't wrapped
    logger=partial(rich_printer, _console=Console(width=200), _styles=STYLES),
)


@pytest.fixture()
@beartype
def fix_test_cache() -> Path:
    """Fixture to clear and return the test cache directory for use.

    Returns:
        Path: Path to the test cache directory

    """
    clear_test_cache()
    return TEST_TMP_CACHE
