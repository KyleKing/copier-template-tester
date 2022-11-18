"""Final test alphabetically (zz) to catch general integration cases."""

from pathlib import Path

import tomli

from copier_template_tester import __version__


def test_version():
    """Check that PyProject and __version__ are equivalent."""
    data = Path('pyproject.toml').read_text()

    result = tomli.loads(data)['tool']['poetry']['version']

    assert result == __version__
