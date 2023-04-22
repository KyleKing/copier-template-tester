"""Template Directory Writer."""

import shutil
from hashlib import sha256
from pathlib import Path

import copier
from beartype import beartype
from corallium.log import get_logger
from corallium.shell import run_shell
from platformdirs import user_cache_dir

logger = get_logger()


@beartype
def _shadow_source(src_path: Path) -> Path:
    """Support freezing the git commit by using a cached directory."""
    checkout_id = sha256(str(src_path).encode(errors='ignore')).hexdigest()
    ctt_cache = Path(user_cache_dir()) / 'copier-template-tester' / src_path.name / checkout_id

    cmd = f'git clone {src_path} {ctt_cache}' if ctt_cache.is_dir() else 'git pull'
    run_shell(cmd=cmd)

    return ctt_cache


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
