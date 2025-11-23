"""Copier Template Tester.

Based on: https://github.com/copier-org/copier/blob/ccfbc9a923f4228af7ca2bf067493665aa15d07c/tests/helpers.py#L20-L81

"""

import logging
from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path

from corallium.log import configure_logger, get_logger
from corallium.loggers.plain_printer import plain_printer

from ._config import load_config, load_temporal_config
from ._pre_commit_support import check_for_untracked
from ._write_output import DEFAULT_TEMPLATE_FILE_NAME, read_copier_template, write_output
from .temporal import TemporalTester

configure_logger(log_level=logging.INFO, logger=plain_printer)
logger = get_logger()


def run(*, base_dir: Path | None = None, check_untracked: bool = False) -> None:
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

    input_path = base_dir
    paths = set()
    for key, data in config['output'].items():
        output_path = base_dir / key
        paths.add(output_path)
        logger.text(f'Using `copier` to create: {key}')
        data_with_defaults = defaults | data
        extra_tasks = data_with_defaults.pop('_extra_tasks', [])
        write_output(
            src_path=input_path, dst_path=base_dir / output_path, data=data_with_defaults, extra_tasks=extra_tasks,
        )

    if check_untracked:  # pragma: no cover
        check_for_untracked(base_dir)


def run_temporal(
    *,
    base_dir: Path | None = None,
    output_dir: Path | None = None,
    parallel: bool | None = None,
    max_workers: int | None = None,
    keep_temp_dirs: bool = False,
    summary: bool = False,
) -> None:
    """Run temporal testing for copier templates.

    Args:
        base_dir: Base directory containing ctt.toml
        output_dir: Output directory for temporal test results
        parallel: Override config parallel setting
        max_workers: Maximum parallel workers
        keep_temp_dirs: Keep temporary directories for debugging
        summary: Show summary report after tests complete

    """
    base_dir = base_dir or Path.cwd()

    # Load temporal configuration
    logger.text(f'Loading temporal configuration from {base_dir}')
    try:
        settings, snapshots = load_temporal_config(base_dir)
    except ValueError as e:
        logger.error('Configuration error', error=str(e))
        return

    if not settings:
        logger.warning('Temporal testing not enabled in ctt.toml')
        return

    if not snapshots:
        logger.warning('No temporal snapshots configured')
        return

    # Resolve paths
    source_project = Path(settings['source_project'])
    if not source_project.is_absolute():
        source_project = (base_dir / source_project).resolve()

    template_path = base_dir
    temporal_output_dir = output_dir or (base_dir / '.ctt-temporal')

    # Override parallel setting if specified
    use_parallel = parallel if parallel is not None else settings['parallel']
    use_keep_temp_dirs = keep_temp_dirs or settings['keep_temp_dirs']

    logger.text('')
    logger.text('Temporal Testing Configuration:')
    logger.text(f'  Template: {template_path}')
    logger.text(f'  Source Project: {source_project}')
    logger.text(f'  Output Directory: {temporal_output_dir}')
    logger.text(f'  Snapshots: {len(snapshots)}')
    logger.text(f'  Mode: {"parallel" if use_parallel else "serial"}')
    if use_parallel:
        logger.text(f'  Max Workers: {max_workers or "auto"}')
    logger.text(f'  Keep Temp Dirs: {use_keep_temp_dirs}')
    logger.text('')

    # Initialize tester
    tester = TemporalTester(
        template_path=template_path,
        source_project=source_project,
        output_dir=temporal_output_dir,
        keep_temp_dirs=use_keep_temp_dirs,
    )

    # Run temporal tests
    results = tester.run_all(
        snapshots=snapshots,
        parallel=use_parallel,
        max_workers=max_workers,
    )

    # Display results
    logger.text('')
    logger.text('=' * 70)
    logger.text('Temporal Test Results')
    logger.text('=' * 70)
    logger.text('')

    success_count = sum(1 for r in results if r.success)
    differences_count = sum(1 for r in results if r.has_differences)

    for result in results:
        status_icon = '✓' if result.success else '✗'
        diff_icon = '!' if result.has_differences else ' '

        logger.text(f'{status_icon} {diff_icon} {result.snapshot_name}')

        if not result.success:
            logger.text(f'    Error: {result.error}')
        elif result.has_differences:
            logger.text(f'    Changes detected: {len(result.files_changed)} files')
            logger.text(f'    Diff: {result.diff_path}')

    logger.text('')
    logger.text(f'Summary: {success_count}/{len(results)} tests passed')
    logger.text(f'         {differences_count}/{len(results)} snapshots have differences')
    logger.text('')

    if summary:
        # Generate summary report with rich (optional)
        try:
            from ._temporal_summary import generate_summary_report
            generate_summary_report(results, temporal_output_dir)
        except ImportError:
            logger.warning('Install rich for enhanced summary reports: pip install rich')


def run_cli() -> None:  # pragma: no cover
    """Accept CLI configuration for running ctt."""
    def dir_path(pth: str | None) -> Path:
        if pth and Path(pth).is_dir():
            return Path(pth).resolve()
        msg = f'Expected a path to a directory. Received: `{pth}`'
        raise ArgumentTypeError(msg)

    # Check if using legacy CLI (no subcommand or unrecognized first arg)
    import sys
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] not in ('test', 'temporal', '-h', '--help')):
        # Legacy mode - parse old-style arguments
        parser = ArgumentParser()
        parser.add_argument(
            '-b',
            '--base-dir',
            help='Specify the path to the directory that contains the configuration file',
            type=dir_path,
        )
        parser.add_argument(
            '--check-untracked',
            help='Only used for pre-commit',
            action='store_true',
        )
        args = parser.parse_args()
        run(base_dir=args.base_dir if hasattr(args, 'base_dir') else None,
            check_untracked=args.check_untracked if hasattr(args, 'check_untracked') else False)
        return

    # Main parser
    parser = ArgumentParser(
        prog='ctt',
        description='Copier Template Tester - Test copier templates with multiple configurations',
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Default/test command (backward compatible)
    test_parser = subparsers.add_parser(
        'test',
        help='Run standard copier template tests (default)',
    )
    test_parser.add_argument(
        '-b',
        '--base-dir',
        help='Specify the path to the directory that contains the configuration file',
        type=dir_path,
    )
    test_parser.add_argument(
        '--check-untracked',
        help='Only used for pre-commit',
        action='store_true',
    )

    # Temporal testing command
    temporal_parser = subparsers.add_parser(
        'temporal',
        help='Run temporal testing against historical project states',
    )
    temporal_parser.add_argument(
        '-b',
        '--base-dir',
        help='Specify the path to the directory that contains the configuration file',
        type=dir_path,
    )
    temporal_parser.add_argument(
        '-o',
        '--output-dir',
        help='Output directory for temporal test results (default: .ctt-temporal)',
        type=Path,
    )
    temporal_parser.add_argument(
        '--parallel',
        help='Enable parallel execution (overrides config)',
        action='store_true',
    )
    temporal_parser.add_argument(
        '--serial',
        help='Disable parallel execution (overrides config)',
        action='store_true',
    )
    temporal_parser.add_argument(
        '--max-workers',
        help='Maximum number of parallel workers',
        type=int,
    )
    temporal_parser.add_argument(
        '--keep-temp-dirs',
        help='Keep temporary directories for debugging',
        action='store_true',
    )
    temporal_parser.add_argument(
        '--summary',
        help='Show enhanced summary report (requires rich)',
        action='store_true',
    )

    args = parser.parse_args()

    # Handle commands
    if args.command == 'temporal':
        # Determine parallel setting
        parallel = None
        if args.parallel:
            parallel = True
        elif args.serial:
            parallel = False

        run_temporal(
            base_dir=args.base_dir,
            output_dir=args.output_dir,
            parallel=parallel,
            max_workers=args.max_workers,
            keep_temp_dirs=args.keep_temp_dirs,
            summary=args.summary,
        )
    elif args.command == 'test':
        run(base_dir=args.base_dir, check_untracked=args.check_untracked)
    elif args.command is None:
        # No subcommand - show help
        parser.print_help()
    else:
        parser.print_help()
