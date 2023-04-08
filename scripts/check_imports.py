"""Check that all imports work as expected in the built package."""

from pprint import pprint

from copier_template_tester.main import run

pprint(f'run: {run}\n\n{locals()}')  # noqa: T203
