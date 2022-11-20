"""nox-poetry configuration file."""

from calcipy.dev.noxfile import build_check, build_dist, coverage, pin_dev_dependencies, tests  # noqa: F401

# Ensure that non-calcipy dev-dependencies are available in Nox environments
pin_dev_dependencies([
    'pytest-shell-utilities>=1.7.0"',
])
