"""Copier Template Tester.

Based on: https://github.com/copier-org/copier/blob/ccfbc9a923f4228af7ca2bf067493665aa15d07c/tests/helpers.py#L20-L81

"""

import logging
import os
import sys
from argparse import ArgumentParser, ArgumentTypeError
from functools import lru_cache
from pathlib import Path
from typing import Any

from corallium.log import configure_logger, get_logger
from corallium.loggers.plain_printer import plain_printer

from ._config import load_config
from ._output_reporter import RunReporter, group_context
from ._pre_commit_support import check_for_untracked
from ._write_output import (
    DEFAULT_TEMPLATE_FILE_NAME,
    _is_git_repo_root,
    _isolated_source,
    read_copier_template,
    write_output,
)

configure_logger(log_level=logging.INFO, logger=plain_printer)
logger = get_logger()


@lru_cache(maxsize=1)
def _log_extra_tasks_deprecation() -> None:
    logger.warning('_extra_tasks is deprecated; please use _post_tasks instead')


def _resolve_post_tasks(data: dict[str, Any]) -> list[Any]:
    """Resolve post_tasks with backward compatibility for _extra_tasks."""
    post_tasks = data.pop('_post_tasks', [])
    extra_tasks = data.pop('_extra_tasks', [])
    if extra_tasks:
        _log_extra_tasks_deprecation()
        if not post_tasks:
            return extra_tasks
    return post_tasks


def _filter_test_cases(output: dict[str, Any], test_case_filters: list[str]) -> dict[str, Any]:
    """Return the subset of output whose keys contain any non-empty filter substring."""
    active_filters = [tcf for tcf in test_case_filters if tcf]
    matched = {key: data for key, data in output.items() if any(tcf in key for tcf in active_filters)}
    if not matched:
        msg = f'No test cases matching filters: {test_case_filters}. Available test cases: {[*output]}'
        raise RuntimeError(msg)
    return matched


def run(
    *,
    base_dir: Path | None = None,
    check_untracked: bool = False,
    continue_on_error: bool = False,
    test_case_filters: list[str] | None = None,
) -> None:
    """Entry point."""
    base_dir = base_dir or Path.cwd()
    try:
        read_copier_template(base_dir=base_dir)
    except FileNotFoundError:
        message = f"Please add a '{DEFAULT_TEMPLATE_FILE_NAME}' file to '{base_dir}'"
        logger.warning(message)
        return

    logger.text(f'Starting Copier Template Tester for {base_dir}')
    logger.text('\tNote: If files were modified, pre-commit will report a failure.')
    logger.text('')
    config = load_config(base_dir)
    defaults = config.get('defaults', {})

    output = config['output']
    if test_case_filters:
        output = _filter_test_cases(output, test_case_filters)

    is_repo_root = _is_git_repo_root(base_dir)
    paths = set()
    reporter = RunReporter()
    with _isolated_source(base_dir) as input_path:
        for key, data in output.items():
            output_path = base_dir / key
            paths.add(output_path)
            with group_context(key):
                logger.text(f'Using `copier` to create: {key}')
                sys.stdout.flush()
                data_with_defaults = defaults | data
                post_tasks = _resolve_post_tasks(data_with_defaults)
                pre_tasks = data_with_defaults.pop('_pre_tasks', [])
                skip_tasks = data_with_defaults.pop('_skip_tasks', False)
                try:
                    write_output(
                        base_dir=base_dir,
                        src_path=input_path,
                        dst_path=base_dir / output_path,
                        data=data_with_defaults,
                        is_repo_root=is_repo_root,
                        post_tasks=post_tasks,
                        pre_tasks=pre_tasks,
                        skip_tasks=skip_tasks,
                    )
                    if continue_on_error:
                        reporter.record_pass(key)
                except Exception as err:
                    if not continue_on_error:
                        raise
                    reporter.record_failure(key, err)

    if continue_on_error:
        reporter.summary()
        reporter.raise_if_any_failures()

    if check_untracked:  # pragma: no cover
        check_for_untracked(base_dir)


def run_cli() -> None:  # pragma: no cover
    """Accept CLI configuration for running ctt."""

    def dir_path(pth: str | None) -> Path:
        if pth and Path(pth).is_dir():
            return Path(pth).resolve()
        msg = f'Expected a path to a directory. Received: `{pth}`'
        raise ArgumentTypeError(msg)

    cli = ArgumentParser()
    cli.add_argument(
        '-b', '--base-dir', help='Specify the path to the directory that contains the configuration file', type=dir_path
    )
    cli.add_argument('--check-untracked', help='Only used for pre-commit', action='store_true')
    cli.add_argument('--continue-on-error', help='Run all test cases and print a summary', action='store_true')

    args = cli.parse_args()
    continue_on_error = args.continue_on_error or os.environ.get('CTT_CONTINUE_ON_ERROR') == '1'
    run(base_dir=args.base_dir, check_untracked=args.check_untracked, continue_on_error=continue_on_error)
