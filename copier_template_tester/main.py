"""Copier Template Tester.

Based on: https://github.com/copier-org/copier/blob/ccfbc9a923f4228af7ca2bf067493665aa15d07c/tests/helpers.py#L20-L81

"""

import logging
import shlex
import shutil
import subprocess
import sys
from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path

import copier
from beartype import beartype
from corallium.log import configure_logger, get_logger
from corallium.loggers.plain_printer import plain_printer
from corallium.tomllib import tomllib

configure_logger(log_level=logging.INFO, logger=plain_printer)
logger = get_logger()


@beartype
def _validate_config(config: dict) -> None:  # type: ignore[type-arg]
    if 'defaults' not in config:
        logger.text('Warning: You probably want a section: [defaults]')
    if not config.get('output'):
        raise RuntimeError('CTT expected headers like: [output."<something>"]')


@beartype
def _load_config(base_dir: Path) -> dict:  # type: ignore[type-arg]
    """Read the ctt config from `CWD`."""
    cfg_path = base_dir / 'ctt.toml'
    if cfg_path.is_file():
        config: dict = tomllib.loads(cfg_path.read_text())  # type: ignore[type-arg]
        _validate_config(config)
        return config
    raise ValueError(f'No configuration file found. Expected: {cfg_path.absolute()}')  # pragma: no cover # noqa: EM102


@beartype
def _render(  # type: ignore[no-untyped-def]
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


@beartype
def _ls_untracked_dir(base_dir: Path) -> set[Path]:
    """Use git to list all untracked files."""
    cmd = 'git ls-files --directory --exclude-standard --no-empty-dir --others'
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, cwd=base_dir)  # noqa: S603
    stdout, _stderr = process.communicate()
    return {base_dir / _d.strip() for _d in stdout.decode().split('\n') if _d}


@beartype
def _is_relative(file_path: Path, directories: set[Path]) -> bool:
    """Returns True if the file_path is relative to any of the directories."""
    return any(file_path.is_relative_to(directory) for directory in directories)


@beartype
def _check_for_untracked(output_paths: set[Path], base_dir: Path) -> None:
    """Resolves the edge case in #3 by raising when pre-commit won't error."""
    if untracked_paths := {
        untracked for untracked in _ls_untracked_dir(base_dir)
        if _is_relative(untracked, output_paths)
    }:
        logger.text('pre-commit error: untracked files must be added', untracked_paths=untracked_paths)
        sys.exit(1)


@beartype
def run(*, base_dir: Path | None = None, check_untracked: bool = False) -> None:
    """Main class to run ctt."""
    base_dir = base_dir or Path.cwd()
    config = _load_config(base_dir)
    defaults = config.get('defaults', {})

    input_path = base_dir
    paths = set()
    for key, data in config['output'].items():
        output_path = base_dir / key
        output_path.mkdir(parents=True, exist_ok=True)
        paths.add(output_path)
        logger.text(f'Creating: {output_path}')
        _render(input_path, base_dir / output_path, data=defaults | data)

    if check_untracked:
        _check_for_untracked(paths, base_dir)


@beartype
def run_cli() -> None:  # pragma: no cover
    """Accept CLI configuration for running ctt."""
    @beartype
    def dir_path(pth: str | None) -> Path:
        if pth and Path(pth).is_dir():
            return Path(pth).resolve()
        msg = f'Expected a path to a directory. Received: `{pth}`'
        raise ArgumentTypeError(msg)

    cli = ArgumentParser()
    cli.add_argument(
        '-b',
        '--base-dir',
        help='Specify the path to the directory that contains the configuration file',
        type=dir_path)
    cli.add_argument('--check-untracked', help='Only used for pre-commit', action='store_true')

    args = cli.parse_args()
    run(base_dir=args.base_dir, check_untracked=args.check_untracked)
