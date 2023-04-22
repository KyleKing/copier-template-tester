"""Template Directory Writer."""

import shutil
from pathlib import Path

import copier
from beartype import beartype
from corallium.log import get_logger

logger = get_logger()


@beartype
def write_output(  # type: ignore[no-untyped-def]
    src_path: Path,
    dst_path: Path,
    data: dict[str, bool | int | float | str | None],
    **kwargs,
) -> None:
    """Copy the specified directory to the target location with provided data.

    kwargs documentation: https://github.com/copier-org/copier/blob/103828b59fd9eb671b5ffa909004d1577742300b/copier/main.py#L86-L173

    """
    kwargs.setdefault('cleanup_on_error', False)
    kwargs.setdefault('data', data or {})
    kwargs.setdefault('defaults', True)
    kwargs.setdefault('overwrite', True)
    kwargs.setdefault('quiet', False)
    kwargs.setdefault('vcs_ref', 'HEAD')
    copier.run_auto(str(src_path), dst_path, **kwargs)
    git_path = dst_path / '.git'
    if git_path.is_dir():  # pragma: no cover
        shutil.rmtree(git_path)
