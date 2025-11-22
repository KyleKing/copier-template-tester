"""Template Directory Writer.

Main module for writing copier template output. Orchestrates template loading,
answers file stabilization, and output directory management.
"""

import shutil
import stat
import sys
from contextlib import contextmanager, suppress
from pathlib import Path

import copier
from corallium.log import get_logger

# Import from refactored modules
from ._answers_stabilizer import (
    DEFAULT_ANSWER_FILE_NAME,
    find_answers_file,
    stabilize_answers_file,
    stabilize_line as _stabilize,
)
from ._git_utils import resolve_git_root_dir as _resolve_git_root_dir
from ._template_config import DEFAULT_TEMPLATE_FILE_NAME, read_copier_template

# Re-export for backward compatibility with existing imports
__all__ = [
    'DEFAULT_ANSWER_FILE_NAME',
    'DEFAULT_TEMPLATE_FILE_NAME',
    'read_copier_template',
    'write_output',
    '_resolve_git_root_dir',
    '_stabilize',
]

logger = get_logger()


@contextmanager
# PLANNED: In python 3.10, there is a Beartype error for this return annotation:
#   -> Generator[None, None, None]
def _output_dir(*, src_path: Path, dst_path: Path):  # noqa: ANN202
    """Context manager to prepare output directory and handle copier answers file cleanup.

    This context manager ensures proper setup and teardown of the copier output directory:
    1. Pre-yield: Creates the destination directory if it doesn't exist
    2. Post-yield: Handles the copier answers file based on template configuration
       - If template has a custom answers file template, stabilizes it for deterministic output
       - If template has no custom answers template, removes the default answers file

    Templates with custom answer file templates (e.g., `{{ _copier_conf.answers_file }}.jinja`)
    need stabilization to ensure reproducible output across different environments.

    Args:
        src_path: Path to the source copier template directory
        dst_path: Path to the destination output directory

    Yields:
        None

    Raises:
        FileNotFoundError: If expected answers file cannot be found (re-raised after logging)

    Addresses: <https://github.com/KyleKing/copier-template-tester/issues/24>

    """
    template_name = '{{ _copier_conf.answers_file }}.jinja'
    has_answers_template = any(src_path.rglob(template_name))

    dst_path.mkdir(parents=True, exist_ok=True)
    yield

    if has_answers_template:
        # Reduce variability in the output
        try:
            stabilize_answers_file(src_path=src_path, dst_path=dst_path)
        except FileNotFoundError as exc:  # pragma: no cover
            logger.warning(str(exc))
            raise
    else:
        with suppress(FileNotFoundError):
            answers_path = find_answers_file(src_path=src_path, dst_path=dst_path)
            answers_path.unlink()


def _remove_readonly(func, path: str, _excinfo) -> None:  # noqa: ANN001
    """Clear the readonly bit for `shutil.rmtree(..., onexc=_remove_readonly)`.

    Adapted from: https://docs.python.org/3/library/shutil.html#rmtree-example

    Resolves: https://github.com/KyleKing/copier-template-tester/issues/34

    The first parameter, function, is the function which raised the exception; it depends on the platform and
    implementation. The second parameter, path, will be the path name passed to function. The third parameter,
    excinfo, is the exception that was raised. Exceptions raised by onexc will not be caught.

    """
    Path.chmod(Path(path), stat.S_IWRITE)
    func(path)


def write_output(
    *,
    src_path: Path,
    dst_path: Path,
    data: dict[str, bool | int | float | str | None],
    extra_tasks: list[str | list[str] | dict[str, str | list[str]]] | None = None,
    **kwargs,
) -> None:
    """Copy the specified directory to the target location with provided data.

    Orchestrates the complete copier template copying process including:
    1. Output directory preparation
    2. Template rendering with provided data
    3. Extra tasks execution
    4. Git directory cleanup
    5. Answers file stabilization

    Args:
        src_path: Path to the source copier template directory
        dst_path: Path to the destination output directory
        data: Template variable values to use during rendering
        extra_tasks: Additional tasks to run after template generation (appended to template's tasks)
        **kwargs: Additional arguments passed to copier.Worker

    Raises:
        FileNotFoundError: If template or required files are not found
        Various copier exceptions during template processing

    References:
        Copier Worker kwargs: https://github.com/copier-org/copier/blob/103828b59fd9eb671b5ffa909004d1577742300b/copier/main.py#L86-L173

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

        with copier.Worker(src_path=str(src_path), dst_path=Path(dst_path), **kwargs) as worker:
            worker.template.config_data['tasks'] = worker.template.config_data.get('tasks', []) + extra_tasks
            worker.run_copy()

        # Remove any .git directory created by copier script
        git_path = dst_path / '.git'
        if git_path.is_dir():  # pragma: no cover
            logger.info('Removing git created by copier', git_path=git_path)
            if sys.version_info >= (3, 12, 0):
                shutil.rmtree(git_path, onexc=_remove_readonly)  # type: ignore[call-arg]
            else:
                shutil.rmtree(git_path, onerror=_remove_readonly)
