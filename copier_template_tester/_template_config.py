"""Copier template configuration loading utilities."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from copier.template import load_template_config

DEFAULT_TEMPLATE_FILE_NAME = 'copier.yaml'
"""Default template file name; however, `copier.yml` is also supported through `read_copier_template`."""


@lru_cache(maxsize=1)
def read_copier_template(base_dir: Path) -> dict[str, Any]:
    """Locate the copier file regardless of variation and return the content.

    Supports both `copier.yaml` and `copier.yml` file names. Caches result for performance.

    Args:
        base_dir: Directory containing the copier template file

    Returns:
        Dictionary containing the parsed copier template configuration

    Raises:
        FileNotFoundError: If neither copier.yaml nor copier.yml exists

    References:
        https://github.com/copier-org/copier/blob/5827d6a6fc6592e64c983bc52a254471ecff7531/docs/creating.md?plain=1#L13-L14

    """
    copier_path = base_dir / DEFAULT_TEMPLATE_FILE_NAME
    if not copier_path.is_file():
        copier_path = copier_path.with_suffix('.yml')
    if not copier_path.is_file():  # pragma: no cover
        msg = f"Can't find the copier template file. Expected: {copier_path} (or .yaml)"
        raise FileNotFoundError(msg)

    return load_template_config(conf_path=copier_path)
