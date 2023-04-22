"""Template Directory Writer."""

import shutil
from pathlib import Path

import copier
import yaml
from beartype import beartype
from corallium.log import get_logger

logger = get_logger()


@beartype
def _read_copier_template(base_dir: Path) -> dict:
    """Locate and read the copier configuration file."""
    copier_path = base_dir / 'copier.yaml'
    if not copier_path.is_file():
        copier_path = copier_path.with_suffix('.yml')
    if not copier_path.is_file():
        msg = f"Can't find the copier answer file. Expected: {copier_path} (or .yaml)"
        raise FileNotFoundError(msg)

    return yaml.safe_load(copier_path.read_text())


@beartype
def _remove_unique_values(*, src_path: Path, dst_path: Path) -> None:
    """Remove unique values for deterministic 'ctt' output."""
    copier_config = _read_copier_template(src_path)
    # https://github.com/copier-org/copier/blob/7f05baf4f004a4876fb6158e1c532b28290146a4/copier/subproject.py#L39
    answers_filename = copier_config.get('_answers_file') or '.copier-answers.yml'
    answers_path = dst_path / answers_filename
    removed_prefix = '_commit'
    answers_path.write_text(
        '\n'.join(
            line
            for line in answers_path.read_text().split('\n')
            if not line.startswith(removed_prefix)
        ),
    )


@beartype
def write_output(  # type: ignore[no-untyped-def]
    *,
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
    # Ensure deterministic output
    _remove_unique_values(src_path=src_path, dst_path=dst_path)
