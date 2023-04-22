"""Global variables for testing."""

import logging
from functools import partial
from pathlib import Path

from corallium.file_helpers import delete_dir, ensure_dir
from corallium.log import configure_logger
from corallium.loggers.rich_printer import rich_printer
from corallium.loggers.styles import STYLES
from rich.console import Console

# Ensure a consistent line length
DEFAULT_LOGGER = partial(rich_printer, _console=Console(width=200), _styles=STYLES)
configure_logger(log_level=logging.DEBUG, logger=DEFAULT_LOGGER)

TEST_DIR = Path(__file__).resolve().parent
"""Path to the `test` directory that contains this file and all other tests."""

TEST_DATA_DIR = TEST_DIR / 'data'
"""Path to subdirectory with test data within the Test Directory."""

TEST_TMP_CACHE = TEST_DIR / '_tmp_cache'
"""Path to the temporary cache folder in the Test directory."""


def clear_test_cache() -> None:
    """Remove the test cache directory if present."""
    delete_dir(TEST_TMP_CACHE)
    ensure_dir(TEST_TMP_CACHE)
