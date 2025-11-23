"""Temporal testing - test current templates against historical project states.

Temporal testing allows you to test the current version of your copier template
against historical states of real projects, helping validate template updates
before applying them to production.
"""

import shutil
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from corallium.log import get_logger

logger = get_logger()


@dataclass
class TemporalSnapshot:
    """Configuration for a temporal test snapshot.

    Attributes:
        name: Unique identifier for this snapshot
        ref: Git ref (commit hash, tag, or branch)
        description: Human-readable description of this snapshot
        template_data: Data to pass to copier template

    """

    name: str
    ref: str
    description: str = ''
    template_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class DiffResult:
    """Result of diffing two directories.

    Attributes:
        has_changes: Whether any differences were found
        patch_file: Path to unified diff patch file
        changed: List of changed file paths
        added: List of added file paths
        removed: List of removed file paths

    """

    has_changes: bool
    patch_file: Path | None
    changed: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


@dataclass
class TemporalTestResult:
    """Result of temporal testing.

    Attributes:
        snapshot_name: Name of the snapshot tested
        success: Whether the test completed successfully
        has_differences: Whether differences were found
        diff_path: Path to diff patch file if differences found
        error: Error message if test failed
        files_changed: List of changed files
        files_added: List of added files
        files_removed: List of removed files

    """

    snapshot_name: str
    success: bool
    has_differences: bool
    diff_path: Path | None
    error: str | None = None
    files_changed: list[str] = field(default_factory=list)
    files_added: list[str] = field(default_factory=list)
    files_removed: list[str] = field(default_factory=list)


class TemporalTester:
    """Execute temporal tests in isolated environments.

    This class orchestrates temporal testing by:
    1. Creating isolated temporary directories
    2. Cloning project history at specific refs
    3. Applying current template to historical states
    4. Capturing before/after snapshots
    5. Generating diffs for manual review
    """

    def __init__(
        self,
        template_path: Path,
        source_project: Path,
        output_dir: Path,
        keep_temp_dirs: bool = False,
    ):
        """Initialize temporal tester.

        Args:
            template_path: Path to copier template
            source_project: Path to source project with git history
            output_dir: Directory for test results (.ctt-temporal/)
            keep_temp_dirs: Keep temporary directories for debugging

        """
        self.template_path = template_path
        self.source_project = source_project
        self.output_dir = output_dir
        self.keep_temp_dirs = keep_temp_dirs
        self.temp_base = Path(tempfile.gettempdir()) / 'ctt-temporal'

    def run_snapshot(self, snapshot: TemporalSnapshot) -> TemporalTestResult:
        """Test a single temporal snapshot in isolation.

        Args:
            snapshot: Snapshot configuration to test

        Returns:
            Result of temporal test including success status and diffs

        """
        logger.text('Testing snapshot', snapshot_name=snapshot.name, ref=snapshot.ref)

        # Create isolated temporary directory
        temp_dir = self.temp_base / f'snapshot-{snapshot.name}'
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Clone/copy project history
            project_dir = self._prepare_project(temp_dir, snapshot.ref)

            # Capture original state
            original_dir = self.output_dir / snapshot.name / 'original'
            self._snapshot_state(project_dir, original_dir)

            # Apply current template
            self._apply_template(project_dir, snapshot.template_data)

            # Capture updated state
            updated_dir = self.output_dir / snapshot.name / 'updated'
            self._snapshot_state(project_dir, updated_dir)

            # Generate diff
            diff_result = self._generate_diff(
                original_dir,
                updated_dir,
                self.output_dir / snapshot.name / 'diff.patch',
            )

            return TemporalTestResult(
                snapshot_name=snapshot.name,
                success=True,
                has_differences=diff_result.has_changes,
                diff_path=diff_result.patch_file,
                error=None,
                files_changed=diff_result.changed,
                files_added=diff_result.added,
                files_removed=diff_result.removed,
            )

        except Exception as e:
            logger.error('Snapshot test failed', snapshot_name=snapshot.name, error=str(e))
            return TemporalTestResult(
                snapshot_name=snapshot.name,
                success=False,
                has_differences=False,
                diff_path=None,
                error=str(e),
                files_changed=[],
                files_added=[],
                files_removed=[],
            )

        finally:
            # Cleanup temp directory (unless keep_temp_dirs=true)
            if not self.keep_temp_dirs and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _prepare_project(self, temp_dir: Path, ref: str) -> Path:
        """Clone project and checkout specific ref.

        Args:
            temp_dir: Temporary directory for cloning
            ref: Git ref to checkout

        Returns:
            Path to cloned project directory

        """
        project_dir = temp_dir / 'project'

        logger.debug('Cloning project', source=self.source_project, dest=project_dir)

        # Clone with full history
        subprocess.run(
            ['git', 'clone', str(self.source_project), str(project_dir)],
            check=True,
            capture_output=True,
        )

        # Checkout specific ref
        subprocess.run(
            ['git', 'checkout', ref],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )

        return project_dir

    def _snapshot_state(self, source: Path, destination: Path) -> None:
        """Capture current project state (excluding .git).

        Args:
            source: Source directory to snapshot
            destination: Destination directory for snapshot

        """
        destination.mkdir(parents=True, exist_ok=True)

        logger.debug('Snapshotting state', source=source, destination=destination)

        # Copy all files except .git
        for item in source.iterdir():
            if item.name == '.git':
                continue
            if item.is_dir():
                shutil.copytree(item, destination / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(item, destination / item.name)

    def _apply_template(self, project_dir: Path, template_data: dict[str, Any]) -> None:
        """Apply copier template to project.

        Args:
            project_dir: Project directory to apply template to
            template_data: Data to pass to copier

        """
        logger.debug('Applying template', project_dir=project_dir, template_data=template_data)

        # Build copier command
        cmd = [
            'copier',
            'update',
            '--answers-file',
            str(project_dir / '.copier-answers.yml'),
        ]

        # Add data flags
        for key, value in template_data.items():
            cmd.extend(['--data', f'{key}={value}'])

        # Run copier update
        subprocess.run(
            cmd,
            cwd=project_dir,
            check=True,
            capture_output=True,
        )

    def _generate_diff(
        self,
        original: Path,
        updated: Path,
        output_file: Path,
    ) -> DiffResult:
        """Generate unified diff between original and updated.

        Args:
            original: Original directory
            updated: Updated directory
            output_file: Output file for diff patch

        Returns:
            DiffResult with details about changes

        """
        logger.debug('Generating diff', original=original, updated=updated)

        # Use git diff for nice formatting
        # Note: git diff returns 1 if differences found (not an error)
        result = subprocess.run(
            ['git', 'diff', '--no-index', str(original), str(updated)],
            capture_output=True,
            text=True,
        )

        # Write diff to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(result.stdout)

        # Parse diff to extract changed files
        has_changes = bool(result.stdout.strip())
        changed: list[str] = []
        added: list[str] = []
        removed: list[str] = []

        if has_changes:
            for line in result.stdout.split('\n'):
                if line.startswith('diff --git'):
                    # Extract filename from diff header
                    parts = line.split()
                    if len(parts) >= 4:
                        filename = parts[2].replace('a/', '')
                        changed.append(filename)

        return DiffResult(
            has_changes=has_changes,
            patch_file=output_file if has_changes else None,
            changed=changed,
            added=added,
            removed=removed,
        )

    def run_all(
        self,
        snapshots: list[TemporalSnapshot],
        parallel: bool = False,
        max_workers: int | None = None,
    ) -> list[TemporalTestResult]:
        """Run all temporal tests.

        Args:
            snapshots: List of snapshots to test
            parallel: Run tests in parallel using ProcessPoolExecutor
            max_workers: Maximum number of parallel workers (defaults to CPU count)

        Returns:
            List of test results in the same order as snapshots

        """
        if not snapshots:
            return []

        logger.text(
            'Running temporal tests',
            count=len(snapshots),
            mode='parallel' if parallel else 'serial',
            max_workers=max_workers if parallel else 1,
        )

        if not parallel:
            # Serial execution
            results = []
            for snapshot in snapshots:
                result = self.run_snapshot(snapshot)
                results.append(result)
            return results

        # Parallel execution
        return self._run_parallel(snapshots, max_workers)

    def _run_parallel(
        self,
        snapshots: list[TemporalSnapshot],
        max_workers: int | None = None,
    ) -> list[TemporalTestResult]:
        """Run temporal tests in parallel.

        Args:
            snapshots: List of snapshots to test
            max_workers: Maximum number of parallel workers

        Returns:
            List of test results in the same order as snapshots

        """
        # Use ProcessPoolExecutor for true parallelism
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_snapshot = {
                executor.submit(self.run_snapshot, snapshot): snapshot
                for snapshot in snapshots
            }

            # Collect results in original order
            results_dict: dict[str, TemporalTestResult] = {}
            for future in as_completed(future_to_snapshot):
                snapshot = future_to_snapshot[future]
                try:
                    result = future.result()
                    results_dict[snapshot.name] = result
                    logger.text(
                        'Snapshot completed',
                        name=snapshot.name,
                        success=result.success,
                        has_differences=result.has_differences,
                    )
                except Exception as e:
                    logger.error('Snapshot failed with exception', name=snapshot.name, error=str(e))
                    # Create error result
                    results_dict[snapshot.name] = TemporalTestResult(
                        snapshot_name=snapshot.name,
                        success=False,
                        has_differences=False,
                        diff_path=None,
                        error=str(e),
                        files_changed=[],
                        files_added=[],
                        files_removed=[],
                    )

            # Return results in original order
            return [results_dict[snapshot.name] for snapshot in snapshots]
