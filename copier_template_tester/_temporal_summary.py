"""Temporal testing summary report generator with rich support."""

import json
from datetime import datetime
from pathlib import Path

from .temporal import TemporalTestResult


def generate_summary_report(results: list[TemporalTestResult], output_dir: Path) -> None:
    """Generate enhanced summary report using rich.

    Args:
        results: List of temporal test results
        output_dir: Output directory for reports

    """
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        from rich import box

        console = Console()

        # Create summary table
        table = Table(
            title='Temporal Test Results',
            box=box.ROUNDED,
            show_header=True,
            header_style='bold magenta',
        )

        table.add_column('Status', style='bold', width=8)
        table.add_column('Snapshot', style='cyan', width=30)
        table.add_column('Changes', justify='center', width=10)
        table.add_column('Files', justify='right', width=8)
        table.add_column('Details', width=40)

        success_count = 0
        failure_count = 0
        differences_count = 0

        for result in results:
            if result.success:
                success_count += 1
                status = '[green]✓ PASS[/green]'
            else:
                failure_count += 1
                status = '[red]✗ FAIL[/red]'

            if result.has_differences:
                differences_count += 1
                changes = '[yellow]YES[/yellow]'
                file_count = str(len(result.files_changed))
                details_str: str | Text = f'Diff: {result.diff_path.name if result.diff_path else "N/A"}'
            else:
                changes = '[green]NO[/green]'
                file_count = '0'
                details_str = 'No changes detected'

            if not result.success and result.error:
                details_str = Text(result.error, style='red')

            table.add_row(
                status,
                result.snapshot_name,
                changes,
                file_count,
                details_str,
            )

        # Print table
        console.print()
        console.print(table)
        console.print()

        # Summary panel
        summary_text = Text()
        summary_text.append(f'Total Tests: {len(results)}\n', style='bold')
        summary_text.append(f'Passed: {success_count} ', style='green')
        summary_text.append(f'Failed: {failure_count}\n', style='red' if failure_count > 0 else 'green')
        summary_text.append(f'Snapshots with Differences: {differences_count}\n', style='yellow' if differences_count > 0 else 'green')

        panel = Panel(
            summary_text,
            title='Summary',
            border_style='blue',
            box=box.DOUBLE,
        )
        console.print(panel)
        console.print()

        # Save metadata report
        metadata_file = output_dir / 'metadata.json'
        save_metadata_report(results, metadata_file)
        console.print(f'[dim]Metadata saved to: {metadata_file}[/dim]')
        console.print()

    except ImportError:
        # Fallback if rich not installed
        print('\nNote: Install rich for enhanced summary reports: pip install rich\n')


def save_metadata_report(results: list[TemporalTestResult], output_file: Path) -> None:
    """Save temporal test metadata to JSON file.

    Args:
        results: List of temporal test results
        output_file: Path to output JSON file

    """
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': len(results),
        'passed': sum(1 for r in results if r.success),
        'failed': sum(1 for r in results if not r.success),
        'differences_found': sum(1 for r in results if r.has_differences),
        'results': [
            {
                'snapshot_name': r.snapshot_name,
                'success': r.success,
                'has_differences': r.has_differences,
                'diff_path': str(r.diff_path) if r.diff_path else None,
                'error': r.error,
                'files_changed': r.files_changed,
                'files_added': r.files_added,
                'files_removed': r.files_removed,
            }
            for r in results
        ],
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(metadata, indent=2))
