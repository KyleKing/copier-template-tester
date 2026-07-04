"""Output reporter for grouped test-case output and failure collection."""

import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field

from corallium.log import get_logger

logger = get_logger()


def _is_github_actions() -> bool:
    return os.environ.get('GITHUB_ACTIONS') == 'true'


@contextmanager
def group_context(name: str):  # noqa: ANN202
    """Context manager that wraps one test case's output in a named group."""
    if _is_github_actions():
        logger.text(f'::group::{name}')
        sys.stdout.flush()
        try:
            yield
        finally:
            sys.stdout.flush()
            logger.text('::endgroup::')
            sys.stdout.flush()
    else:
        logger.text('')
        logger.text(f'--- Test: {name} ---')
        yield


@dataclass
class RunReporter:
    """Collects pass/fail results across test cases."""

    _results: list[tuple[str, Exception | None]] = field(default_factory=list, init=False)

    def record_pass(self, name: str) -> None:
        self._results.append((name, None))

    def record_failure(self, name: str, exc: Exception) -> None:
        self._results.append((name, exc))

    def summary(self) -> None:
        """Print a pass/fail table to stdout."""
        sys.stdout.write('\n--- CTT Summary ---\n')
        failures = 0
        for name, exc in self._results:
            if exc is None:
                sys.stdout.write(f'  PASS  {name}\n')
            else:
                sys.stdout.write(f'  FAIL  {name} — {type(exc).__name__}: {exc}\n')
                failures += 1
        if failures:
            line = f'{failures} failure(s). See output above for details.'
            prefix = '::error::' if _is_github_actions() else ''
            sys.stdout.write(f'\n{prefix}{line}\n')

    def raise_if_any_failures(self) -> None:
        """Raise SystemExit(1) if any failures were recorded."""
        if any(exc is not None for _, exc in self._results):
            raise SystemExit(1)
