"""Template Directory Writer."""

import re
import shutil
from contextlib import contextmanager, suppress
from functools import lru_cache
from pathlib import Path

import copier
import yaml
from corallium.file_helpers import read_lines
from corallium.log import get_logger
from corallium.shell import capture_shell

logger = get_logger()

DEFAULT_TEMPLATE_FILE_NAME = 'copier.yaml'
"""Default answer file name; however, `copier.yml` is also supported through `read_copier_template`."""


DEFAULT_ANSWER_FILE_NAME = '.copier-answers.yml'
"""Default answer file name.

https://github.com/copier-org/copier/blob/7f05baf4f004a4876fb6158e1c532b28290146a4/copier/subproject.py#L39

"""


@lru_cache(maxsize=1)
def read_copier_template(base_dir: Path) -> dict:  # type: ignore[type-arg]
    """Locate the copier file regardless of variation and return the content.

    https://github.com/copier-org/copier/blob/5827d6a6fc6592e64c983bc52a254471ecff7531/docs/creating.md?plain=1#L13-L14

    """
    copier_path = base_dir / DEFAULT_TEMPLATE_FILE_NAME
    if not copier_path.is_file():
        copier_path = copier_path.with_suffix('.yml')
    if not copier_path.is_file():  # pragma: no cover
        msg = f"Can't find the copier template file. Expected: {copier_path} (or .yaml)"
        raise FileNotFoundError(msg)

    return yaml.safe_load(copier_path.read_text())  # type: ignore[no-any-return]


@lru_cache(maxsize=1)
def _find_answers_file(*, src_path: Path, dst_path: Path) -> Path:
    """Locate the copier answers file based on the copier template."""
    copier_config = read_copier_template(src_path)
    answers_filename = copier_config.get('_answers_file') or DEFAULT_ANSWER_FILE_NAME
    if '{{' in answers_filename:
        # If the filename is created from the template, just grab the first match
        search_name = re.sub(r'{{[^}]+}}', '*', answers_filename)
        matches = [*dst_path.glob(search_name)]
        if len(matches) != 1:  # pragma: no cover
            msg = f"Can't find just one copier answers file matching {dst_path / search_name}. Found: {matches}"
            raise ValueError(msg)
        return matches[0]
    return dst_path / answers_filename  # pragma: no cover


@lru_cache(maxsize=3)
def _resolve_git_root_dir(base_dir: Path) -> Path:
    """Use git to list all untracked files."""
    cmd = 'git rev-parse --show-toplevel'
    output = capture_shell(cmd=cmd, cwd=base_dir)
    return Path(output.strip())


def _stabilize(line: str, answers_path: Path) -> str:
    # Convert _src_path to a deterministic relative path
    if line.startswith('_src_path'):
        logger.info('Replacing with deterministic value', line=line)
        raw_path = Path(line.split('_src_path:')[-1].strip())
        ans_dir = answers_path.parent
        if ans_dir.is_relative_to(raw_path):
            count_rel = len(ans_dir.relative_to(raw_path).parts)
            rel_path = '/'.join([*(['..'] * count_rel), raw_path.name])
            return f'_src_path: {rel_path}'
        return line
    # Create a stable tag for '_commit' that copier will still utilize
    if line.startswith('_commit'):
        logger.info('Replacing with deterministic value', line=line)
        return '_commit: HEAD'
    return line


def _stabilize_answers_file(*, src_path: Path, dst_path: Path) -> None:
    """Ensure that the answers file is deterministic."""
    answers_path = _find_answers_file(src_path=src_path, dst_path=dst_path)
    lines = (_stabilize(_l, answers_path) for _l in read_lines(answers_path) if _l.strip())
    answers_path.write_text('\n'.join(lines) + '\n')


@contextmanager
# PLANNED: In python 3.10, there is a Beartype error for this return annotation:
#   -> Generator[None, None, None]
def _output_dir(*, src_path: Path, dst_path: Path):  # type: ignore[no-untyped-def]  # noqa: ANN202
    """Manage the output directory and handle templates that cannot be updated (i.e. not answers file).

    Addresses: <https://github.com/KyleKing/copier-template-tester/issues/24>

    """
    template_name = '{{ _copier_conf.answers_file }}.jinja'
    has_answers_template = any(src_path.rglob(template_name))

    dst_path.mkdir(parents=True, exist_ok=True)
    yield

    if has_answers_template:
        # Reduce variability in the output
        try:
            _stabilize_answers_file(src_path=src_path, dst_path=dst_path)
        except FileNotFoundError as exc:  # pragma: no cover
            logger.warning(str(exc))
            raise
    else:
        with suppress(FileNotFoundError):
            answers_path = _find_answers_file(src_path=src_path, dst_path=dst_path)
            answers_path.unlink()


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
    with _output_dir(src_path=src_path, dst_path=dst_path):
        kwargs.setdefault('cleanup_on_error', False)
        kwargs.setdefault('data', data or {})
        kwargs.setdefault('defaults', True)
        kwargs.setdefault('exclude', ['.ctt', 'ctt.toml'])
        kwargs.setdefault('overwrite', True)
        kwargs.setdefault('quiet', False)
        kwargs.setdefault('unsafe', True)
        kwargs.setdefault('vcs_ref', 'HEAD')
        copier.run_copy(str(src_path), dst_path, **kwargs)

        # Remove any .git directory created by copier script
        git_path = dst_path / '.git'
        if git_path.is_dir():  # pragma: no cover
            logger.info('Removing git created by copier', git_path=git_path)
            shutil.rmtree(git_path)
