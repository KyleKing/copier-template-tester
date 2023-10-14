"""Copier Template Tester.

Based on: https://github.com/copier-org/copier/blob/ccfbc9a923f4228af7ca2bf067493665aa15d07c/tests/helpers.py#L20-L81

"""

import logging
import shutil
from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path

from beartype import beartype
from corallium.log import configure_logger, get_logger
from corallium.loggers.plain_printer import plain_printer

from ._config import load_config
from ._pre_commit_support import check_for_untracked
from ._write_output import write_output

configure_logger(log_level=logging.INFO, logger=plain_printer)
logger = get_logger()


@beartype
def is_updateable(base_dir: Path) -> bool:
    """Check if the copier template is updateable or not.

    Addresses: https://github.com/KyleKing/copier-template-tester/issues/24

    """
    return any(base_dir.rglob('{{ _copier_conf.answers_file }}.jinja'))


@beartype
def run(*, base_dir: Path | None = None, check_untracked: bool = False) -> None:
    """Main class to run ctt."""
    base_dir = base_dir or Path.cwd()
    logger.text(f'Starting Copier Template Tester for {base_dir}')
    logger.text('\tNote: If files were modified, pre-commit will report a failure.')
    logger.text('')
    config = load_config(base_dir)
    defaults = config.get('defaults', {})

    input_path = base_dir
    paths = set()
    for key, data in config['output'].items():
        output_path = base_dir / key
        if not is_updateable(base_dir):
            shutil.rmtree(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        paths.add(output_path)
        logger.text(f'Using `copier` to create: {key}')
        write_output(src_path=input_path, dst_path=base_dir / output_path, data=defaults | data)

    if check_untracked:  # pragma: no cover
        check_for_untracked(paths, base_dir)


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
