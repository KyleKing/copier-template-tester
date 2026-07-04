"""Template Directory Writer."""

import os
import re
import shutil
import stat
import subprocess  # noqa: S404
import sys
import tarfile
import tempfile
from contextlib import contextmanager, suppress
from functools import lru_cache
from pathlib import Path
from typing import Any

# Copier 9.7.0 renamed internal modules with a `_` prefix and emits deprecation warnings
#   for non-public API imports. The public API (run_copy, run_recopy, run_update) doesn't
#   support task injection, so we continue using Worker directly.
# Alternative: replace load_template_config with pyyaml (loses !include support)
# References:
#   https://copier.readthedocs.io/en/stable/changelog/ (v9.7.0)
#   https://github.com/orgs/copier-org/discussions/1250
from copier._main import Worker  # noqa:  PLC2701
from copier._template import load_template_config  # noqa: PLC2701
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
def read_copier_template(base_dir: Path) -> dict[str, Any]:
    """Locate the copier file regardless of variation and return the content.

    https://github.com/copier-org/copier/blob/5827d6a6fc6592e64c983bc52a254471ecff7531/docs/creating.md?plain=1#L13-L14

    """
    copier_path = base_dir / DEFAULT_TEMPLATE_FILE_NAME
    if not copier_path.is_file():
        copier_path = copier_path.with_suffix('.yml')
    if not copier_path.is_file():  # pragma: no cover
        msg = f"Can't find the copier template file. Expected: {copier_path} (or .yaml)"
        raise FileNotFoundError(msg)

    return load_template_config(conf_path=copier_path)


@lru_cache(maxsize=1)
def _find_answers_file(*, src_path: Path, dst_path: Path) -> Path:
    """Locate the copier answers file based on the copier template."""
    copier_config = read_copier_template(src_path)
    answers_filename = copier_config.get('_answers_file') or DEFAULT_ANSWER_FILE_NAME
    if '{{' in answers_filename:
        # If the filename is created from the template, just grab the first match
        # Replace Jinja2 template variables (e.g., {{project_name}}) with glob wildcards
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


# git plumbing variables that pre-commit/prek export into the hook environment.
# Left set, they redirect the snapshot commands below to the hook-managed index or
# a linked worktree's `.git` file, so they are cleared before every git invocation.
_GIT_ENV_VARS = (
    'GIT_ALTERNATE_OBJECT_DIRECTORIES',
    'GIT_COMMON_DIR',
    'GIT_CONFIG_PARAMETERS',
    'GIT_DIR',
    'GIT_INDEX_FILE',
    'GIT_OBJECT_DIRECTORY',
    'GIT_PREFIX',
    'GIT_WORK_TREE',
)


def _clean_git_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _GIT_ENV_VARS}


def _run_git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ['git', *args],  # noqa: S607
        cwd=cwd,
        env=_clean_git_env(),
        capture_output=True,
        text=True,
        check=False,
    )


def _is_git_repo_root(base_dir: Path) -> bool:
    result = _run_git(['rev-parse', '--show-toplevel'], cwd=base_dir)
    if result.returncode != 0:
        return False
    top = result.stdout.strip()
    return bool(top) and Path(top).resolve() == base_dir.resolve()


@contextmanager
def _isolated_source(base_dir: Path):  # noqa: ANN202
    """Yield a git-free snapshot of the template so copier never runs its VCS clone.

    copier's `Worker(vcs_ref="HEAD")` clones a local git template; for a *dirty* repo it
    stages the live work tree (`--work-tree=<repo>`) into a throwaway git-dir and commits
    there (`copier._vcs.clone`). Run inside a pre-commit hook, while the index is mid-write,
    that has corrupted the repository index and object store. Rendering a plain, non-git
    copy avoids the code path entirely while still capturing the current tracked working
    tree (staged and unstaged) via `git stash create`.

    Untracked files are excluded; they are reported separately by `check_for_untracked`.
    A non-git `base_dir` is yielded unchanged (copier already renders it without VCS).
    """
    if not _is_git_repo_root(base_dir):
        yield base_dir
        return

    # `stash create` builds a commit of the staged+unstaged tree without touching the
    # index, work tree, or any ref, so it is safe to run mid-commit; it is empty when clean.
    ref = _run_git(['stash', 'create'], cwd=base_dir).stdout.strip() or 'HEAD'
    tmp_dir = Path(tempfile.mkdtemp(prefix='ctt-src-'))
    try:
        # `archive` materializes that snapshot as a plain tree (no `.git`), so copier sees a
        # non-git directory and skips its clone/dirty-staging entirely.
        with (
            subprocess.Popen(  # noqa: S603
                ['git', 'archive', '--format=tar', ref],  # noqa: S607
                cwd=base_dir,
                env=_clean_git_env(),
                stdout=subprocess.PIPE,
            ) as archive,
            tarfile.open(fileobj=archive.stdout, mode='r|') as tar,
        ):
            if sys.version_info >= (3, 12, 0):
                tar.extractall(tmp_dir, filter='data')  # pragma: no cover
            else:
                tar.extractall(tmp_dir)  # noqa: S202
        if archive.returncode != 0:  # pragma: no cover
            msg = f'Failed to snapshot the template source with `git archive {ref}`'
            raise RuntimeError(msg)
        yield tmp_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _relative_src_path(*, base_dir: Path, answers_path: Path) -> str:
    """Deterministic `_src_path` relative to the answers file, independent of absolute paths.

    ctt renders output into `<base_dir>/<key>`, so the source is always some number of
    parent directories above the answers file, named for `base_dir`.
    """
    count_rel = len(answers_path.parent.resolve().relative_to(base_dir.resolve()).parts)
    return '/'.join([*(['..'] * count_rel), base_dir.name])


def _stabilize_answers_file(*, base_dir: Path, src_path: Path, dst_path: Path, is_repo_root: bool) -> None:
    """Rewrite the answers file with deterministic `_src_path` (and `_commit` for git sources).

    Isolation renders every git template as a non-git copy, so copier writes an absolute
    temp `_src_path` and omits `_commit`. Both are normalized here to the reproducible values
    copier historically produced for a git source: a relative `_src_path` and `_commit: HEAD`.
    """
    answers_path = _find_answers_file(src_path=src_path, dst_path=dst_path)
    rel_src_path = _relative_src_path(base_dir=base_dir, answers_path=answers_path)
    logger.info('Replacing with deterministic value', src_path=rel_src_path)

    out: list[str] = []
    commit_written = False
    for line in read_lines(answers_path):
        if not line.strip() or line.startswith('_commit'):
            continue
        if line.startswith('_src_path'):
            if is_repo_root and not commit_written:
                out.append('_commit: HEAD')
                commit_written = True
            out.append(f'_src_path: {rel_src_path}')
            continue
        out.append(line)
    answers_path.write_text('\n'.join(out) + '\n')


@contextmanager
# PLANNED: In python 3.10, there is a Beartype error for this return annotation:
#   -> Generator[None, None, None]
def _output_dir(*, base_dir: Path, src_path: Path, dst_path: Path, is_repo_root: bool):  # noqa: ANN202
    """Context manager to prepare output directory and handle copier answers file cleanup.

    This context manager ensures proper setup and teardown of the copier output directory:
    1. Pre-yield: Creates the destination directory if it doesn't exist
    2. Post-yield: Handles the copier answers file based on template configuration
       - If template has a custom answers file template, stabilizes it for deterministic output
       - If template has no custom answers template, removes the default answers file

    Templates with custom answer file templates (e.g., `{{ _copier_conf.answers_file }}.jinja`)
    need stabilization to ensure reproducible output across different environments.

    Addresses: <https://github.com/KyleKing/copier-template-tester/issues/24>

    Args:
        base_dir: Path to the logical template root, used to stabilize the answers `_src_path`
        src_path: Path to the source copier template directory (isolated snapshot when git-backed)
        dst_path: Path to the destination output directory
        is_repo_root: Whether base_dir is a git repository root (adds a stable `_commit: HEAD`)

    Yields:
        None

    Raises:
        FileNotFoundError: If expected answers file cannot be found (re-raised after logging)

    """
    template_name = '{{ _copier_conf.answers_file }}.jinja'
    has_answers_template = any(src_path.rglob(template_name))

    dst_path.mkdir(parents=True, exist_ok=True)
    # A failed render should leave the output untouched, so the answers-file handling runs only
    # when the yielded block completes without raising (the `render_ok` guard in `finally`).
    render_ok = False
    try:
        yield
        render_ok = True
    finally:
        if render_ok and has_answers_template:
            # Reduce variability in the output
            try:
                _stabilize_answers_file(
                    base_dir=base_dir, src_path=src_path, dst_path=dst_path, is_repo_root=is_repo_root
                )
            except FileNotFoundError as exc:  # pragma: no cover
                logger.warning(str(exc))
                raise
        elif render_ok:
            with suppress(FileNotFoundError):
                answers_path = _find_answers_file(src_path=src_path, dst_path=dst_path)
                answers_path.unlink()


def _remove_readonly(func, path: str, _excinfo) -> None:  # pragma: no cover  # noqa: ANN001
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
    base_dir: Path,
    src_path: Path,
    dst_path: Path,
    data: dict[str, Any],
    is_repo_root: bool = False,
    post_tasks: list[str | list[str] | dict[str, str | list[str]]] | None = None,
    pre_tasks: list[str | list[str] | dict[str, str | list[str]]] | None = None,
    skip_tasks: bool = False,
    **kwargs,
) -> None:
    """Copy the specified directory to the target location with provided data.

    `src_path` is the (possibly isolated) directory copier renders from; `base_dir` is the
    logical template root used to keep the answers file's `_src_path` deterministic.

    kwargs documentation: https://github.com/copier-org/copier/blob/103828b59fd9eb671b5ffa909004d1577742300b/copier/main.py#L86-L173

    """
    with _output_dir(base_dir=base_dir, src_path=src_path, dst_path=dst_path, is_repo_root=is_repo_root):
        kwargs.setdefault('cleanup_on_error', False)
        kwargs.setdefault('data', data or {})
        kwargs.setdefault('defaults', True)
        kwargs.setdefault('exclude', ['.ctt', 'ctt.toml'])
        kwargs.setdefault('overwrite', True)
        kwargs.setdefault('quiet', False)
        kwargs.setdefault('unsafe', True)
        kwargs.setdefault('vcs_ref', 'HEAD')

        with Worker(src_path=str(src_path), dst_path=dst_path, **kwargs) as worker:
            if skip_tasks:
                worker.template.config_data['tasks'] = (pre_tasks or []) + (post_tasks or [])
            else:
                template_tasks = worker.template.config_data.get('tasks', [])
                worker.template.config_data['tasks'] = (pre_tasks or []) + template_tasks + (post_tasks or [])
            worker.run_copy()

        # Remove any .git directory created by copier script
        git_path = dst_path / '.git'
        if git_path.is_dir():  # pragma: no cover
            logger.info('Removing git created by copier', git_path=git_path)
            if sys.version_info >= (3, 12, 0):
                shutil.rmtree(git_path, onexc=_remove_readonly)  # type: ignore[call-arg]
            else:
                shutil.rmtree(git_path, onerror=_remove_readonly)
