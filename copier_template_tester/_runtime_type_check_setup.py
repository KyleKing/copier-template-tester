"""Conditionally configure runtime typechecking."""

from contextlib import suppress
from datetime import datetime, timezone
from enum import Enum
from os import getenv
from warnings import filterwarnings

from typing_extensions import Self

NAME = 'copier_template_tester'.upper()
"""Package name to allow more targeted usage."""


class _RuntimeTypeCheckingModes(Enum):
    """Supported global runtime type checking modes."""

    ERROR = 'ERROR'
    WARNING = 'WARNING'
    OFF = None

    @classmethod
    def from_environment(cls) -> Self:  # pragma: no cover
        """Return the configured mode.

        Raises:
            ValueError: if environment variable is configured incorrectly

        """
        rtc_mode = getenv('RUNTIME_TYPE_CHECKING_MODE') or getenv(f'RUNTIME_TYPE_CHECKING_MODE_{NAME}') or None
        try:
            return cls(rtc_mode)
        except ValueError:
            modes = [_e.value for _e in cls]
            msg = f"'RUNTIME_TYPE_CHECKING_MODE={rtc_mode}' is not from {modes}"
            raise ValueError(msg) from None


def configure_runtime_type_checking_mode() -> None:  # pragma: no cover
    """Optionally configure runtime type checking mode globally."""
    rtc_mode = _RuntimeTypeCheckingModes.from_environment()

    if rtc_mode is not _RuntimeTypeCheckingModes.OFF:
        with suppress(ImportError, ModuleNotFoundError):
            # Requires beartype >=0.15.0 and Python >= 3.8
            from beartype import BeartypeConf  # noqa: PLC0415
            from beartype.claw import beartype_this_package  # noqa: PLC0415
            from beartype.roar import BeartypeClawDecorWarning  # noqa: PLC0415

            beartype_this_package(
                conf=BeartypeConf(
                    warning_cls_on_decorator_exception=(
                        None if rtc_mode is _RuntimeTypeCheckingModes.ERROR else BeartypeClawDecorWarning
                    ),
                ),
            )


_PEP585_DATE = 2025
if datetime.now(tz=timezone.utc).year <= _PEP585_DATE:  # pragma: no cover
    with suppress(ImportError, ModuleNotFoundError):
        from beartype.roar import BeartypeDecorHintPep585DeprecationWarning

        filterwarnings(
            'ignore',
            category=BeartypeDecorHintPep585DeprecationWarning,
        )
