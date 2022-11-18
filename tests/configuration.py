"""Global variables for testing."""

from pathlib import Path

from calcipy.file_helpers import delete_dir, ensure_dir
from calcipy.log_helpers import activate_debug_logging

from copier_template_tester import __pkg_name__

activate_debug_logging(pkg_names=[__pkg_name__], clear_log=True)

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
