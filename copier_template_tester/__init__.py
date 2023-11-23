"""copier_template_tester."""

from datetime import datetime, timezone
from enum import Enum
from os import getenv
from warnings import filterwarnings

from beartype import BeartypeConf
from beartype.claw import beartype_this_package
from beartype.roar import BeartypeDecorHintPep585DeprecationWarning
from typing_extensions import Self

__version__ = '2.1.1'
__pkg_name__ = 'copier_template_tester'


class _RuntimeTypeCheckingModes(Enum):
    """Supported global runtime type checking modes."""

    ERROR = 'ERROR'
    WARNING = 'WARNING'
    OFF = None

    @classmethod
    def from_environment(cls) -> Self:  # pragma: no cover
        """Return the configured mode."""
        rtc_mode = getenv('RUNTIME_TYPE_CHECKING_MODE') or None
        try:
            return cls(rtc_mode)
        except ValueError:
            modes = [_e.value for _e in cls]
            msg = f"'RUNTIME_TYPE_CHECKING_MODE={rtc_mode}' is not an allowed mode from {modes}"
            raise ValueError(msg) from None


def configure_runtime_type_checking_mode() -> None:  # pragma: no cover
    """Optionally configure runtime type checking mode globally."""
    rtc_mode = _RuntimeTypeCheckingModes.from_environment()

    if rtc_mode is not _RuntimeTypeCheckingModes.OFF:
        from beartype.roar import BeartypeClawDecorWarning  # noqa: PLC0415

        beartype_this_package(conf=BeartypeConf(
            warning_cls_on_decorator_exception=(
                None if rtc_mode is _RuntimeTypeCheckingModes.ERROR else BeartypeClawDecorWarning
            ),
        ))


_PEP585_DATE = 2025
if datetime.now(tz=timezone.utc).year <= _PEP585_DATE:  # pragma: no cover
    filterwarnings('ignore', category=BeartypeDecorHintPep585DeprecationWarning)
configure_runtime_type_checking_mode()

# ====== Above is the recommended code from calcipy_template and may be updated on new releases ======
