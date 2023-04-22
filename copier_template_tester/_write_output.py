"""Template Directory Writer."""

import re
import shutil
from pathlib import Path

import copier
import yaml
from beartype import beartype
from corallium.log import get_logger

logger = get_logger()

DEFAULT_TEMPLATE_FILE_NAME = 'copier.yaml'
"""Default answer file name. Alternative is copier.yml."""


DEFAULT_ANSWER_FILE_NAME = '.copier-answers.yml'
"""Default answer file name.

https://github.com/copier-org/copier/blob/7f05baf4f004a4876fb6158e1c532b28290146a4/copier/subproject.py#L39

"""


@beartype
def _read_copier_template(base_dir: Path) -> dict:  # type: ignore[type-arg]
    """Locate and read the copier configuration file."""
    copier_path = base_dir / DEFAULT_TEMPLATE_FILE_NAME
    if not copier_path.is_file():
        copier_path = copier_path.with_suffix('.yml')
    if not copier_path.is_file():
        msg = f"Can't find the copier template file. Expected: {copier_path} (or .yaml)"
        raise FileNotFoundError(msg)

    return yaml.safe_load(copier_path.read_text())  # type: ignore[no-any-return]


@beartype
def _find_answers_file(*, src_path: Path, dst_path: Path) -> Path:
    """Locate the copier answers file based on the copier template."""
    copier_config = _read_copier_template(src_path)
    answers_filename = copier_config.get('_answers_file') or DEFAULT_ANSWER_FILE_NAME
    if '{{' in answers_filename:
        # If the filename is created from the template, just grab the first match
        search_name = re.sub(r'{{[^}]+}}', '*', answers_filename)
        matches = [*dst_path.glob(search_name)]
        if len(matches) == 1:
            return matches[0]
        msg = f"Can't find just one copier answers file matching {dst_path / search_name}. Found: {matches}"
        raise ValueError(msg)
    return dst_path / answers_filename


@beartype
def _stabilize_commit_id(*, src_path: Path, dst_path: Path) -> None:
    """Replace part of the _commit for a less variable 'ctt' output."""
    answers_path = _find_answers_file(src_path=src_path, dst_path=dst_path)
    lines = (  # noqa: ECE001
        # Create a stable tag that copier will still utilize
        f'{line.split("-")[0]}-0' if line.startswith('_commit') else line
        for line in answers_path.read_text().split('\n')
    )
    answers_path.write_text('\n'.join(lines))


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

    # Reduce variability in the output
    try:
        _stabilize_commit_id(src_path=src_path, dst_path=dst_path)
    except FileNotFoundError as exc:
        logger.error(str(exc))  # noqa: TRY400
