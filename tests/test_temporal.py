"""Tests for temporal testing module."""

import subprocess
from pathlib import Path

import pytest

from copier_template_tester.temporal import (
    DiffResult,
    TemporalSnapshot,
    TemporalTestResult,
    TemporalTester,
)


class TestTemporalSnapshot:
    """Test TemporalSnapshot dataclass."""

    def test_create_minimal_snapshot(self) -> None:
        """Test creating snapshot with minimal required fields."""
        snapshot = TemporalSnapshot(
            name='test',
            ref='v1.0.0',
        )
        assert snapshot.name == 'test'
        assert snapshot.ref == 'v1.0.0'
        assert snapshot.description == ''
        assert snapshot.template_data == {}

    def test_create_full_snapshot(self) -> None:
        """Test creating snapshot with all fields."""
        snapshot = TemporalSnapshot(
            name='test',
            ref='abc123',
            description='Test snapshot',
            template_data={'project_name': 'test', 'python_version': '3.11'},
        )
        assert snapshot.name == 'test'
        assert snapshot.ref == 'abc123'
        assert snapshot.description == 'Test snapshot'
        assert snapshot.template_data == {'project_name': 'test', 'python_version': '3.11'}


class TestDiffResult:
    """Test DiffResult dataclass."""

    def test_create_diff_result_no_changes(self) -> None:
        """Test creating diff result with no changes."""
        result = DiffResult(
            has_changes=False,
            patch_file=None,
        )
        assert not result.has_changes
        assert result.patch_file is None
        assert result.changed == []
        assert result.added == []
        assert result.removed == []

    def test_create_diff_result_with_changes(self, tmp_path: Path) -> None:
        """Test creating diff result with changes."""
        patch_file = tmp_path / 'diff.patch'
        patch_file.write_text('diff content')

        result = DiffResult(
            has_changes=True,
            patch_file=patch_file,
            changed=['file1.py', 'file2.py'],
            added=['file3.py'],
            removed=['file4.py'],
        )
        assert result.has_changes
        assert result.patch_file == patch_file
        assert result.changed == ['file1.py', 'file2.py']
        assert result.added == ['file3.py']
        assert result.removed == ['file4.py']


class TestTemporalTestResult:
    """Test TemporalTestResult dataclass."""

    def test_create_successful_result(self, tmp_path: Path) -> None:
        """Test creating successful test result."""
        diff_path = tmp_path / 'diff.patch'

        result = TemporalTestResult(
            snapshot_name='test',
            success=True,
            has_differences=True,
            diff_path=diff_path,
            files_changed=['file1.py'],
        )
        assert result.snapshot_name == 'test'
        assert result.success
        assert result.has_differences
        assert result.diff_path == diff_path
        assert result.error is None
        assert result.files_changed == ['file1.py']

    def test_create_failed_result(self) -> None:
        """Test creating failed test result."""
        result = TemporalTestResult(
            snapshot_name='test',
            success=False,
            has_differences=False,
            diff_path=None,
            error='Test error message',
        )
        assert result.snapshot_name == 'test'
        assert not result.success
        assert not result.has_differences
        assert result.diff_path is None
        assert result.error == 'Test error message'


class TestTemporalTester:
    """Test TemporalTester class."""

    def test_init_temporal_tester(self, tmp_path: Path) -> None:
        """Test initializing TemporalTester."""
        template_path = tmp_path / 'template'
        source_project = tmp_path / 'project'
        output_dir = tmp_path / 'output'

        tester = TemporalTester(
            template_path=template_path,
            source_project=source_project,
            output_dir=output_dir,
        )

        assert tester.template_path == template_path
        assert tester.source_project == source_project
        assert tester.output_dir == output_dir
        assert not tester.keep_temp_dirs
        assert 'ctt-temporal' in str(tester.temp_base)

    def test_snapshot_state(self, tmp_path: Path) -> None:
        """Test _snapshot_state method."""
        template_path = tmp_path / 'template'
        source_project = tmp_path / 'project'
        output_dir = tmp_path / 'output'

        tester = TemporalTester(
            template_path=template_path,
            source_project=source_project,
            output_dir=output_dir,
        )

        # Create source directory with files
        source = tmp_path / 'source'
        source.mkdir()
        (source / 'file1.txt').write_text('content1')
        (source / 'file2.txt').write_text('content2')
        subdir = source / 'subdir'
        subdir.mkdir()
        (subdir / 'file3.txt').write_text('content3')

        # Create .git directory (should be excluded)
        (source / '.git').mkdir()
        (source / '.git' / 'config').write_text('git config')

        # Snapshot state
        destination = tmp_path / 'destination'
        tester._snapshot_state(source, destination)

        # Verify files copied (excluding .git)
        assert (destination / 'file1.txt').read_text() == 'content1'
        assert (destination / 'file2.txt').read_text() == 'content2'
        assert (destination / 'subdir' / 'file3.txt').read_text() == 'content3'
        assert not (destination / '.git').exists()

    def test_generate_diff_no_changes(self, tmp_path: Path) -> None:
        """Test _generate_diff with no changes."""
        template_path = tmp_path / 'template'
        source_project = tmp_path / 'project'
        output_dir = tmp_path / 'output'

        tester = TemporalTester(
            template_path=template_path,
            source_project=source_project,
            output_dir=output_dir,
        )

        # Create identical directories
        original = tmp_path / 'original'
        original.mkdir()
        (original / 'file.txt').write_text('content')

        updated = tmp_path / 'updated'
        updated.mkdir()
        (updated / 'file.txt').write_text('content')

        # Generate diff
        output_file = tmp_path / 'diff.patch'
        result = tester._generate_diff(original, updated, output_file)

        # Verify no changes detected
        assert not result.has_changes
        assert result.patch_file is None
        assert result.changed == []

    def test_generate_diff_with_changes(self, tmp_path: Path) -> None:
        """Test _generate_diff with changes."""
        template_path = tmp_path / 'template'
        source_project = tmp_path / 'project'
        output_dir = tmp_path / 'output'

        tester = TemporalTester(
            template_path=template_path,
            source_project=source_project,
            output_dir=output_dir,
        )

        # Create different directories
        original = tmp_path / 'original'
        original.mkdir()
        (original / 'file.txt').write_text('original content')

        updated = tmp_path / 'updated'
        updated.mkdir()
        (updated / 'file.txt').write_text('updated content')

        # Generate diff
        output_file = tmp_path / 'diff.patch'
        result = tester._generate_diff(original, updated, output_file)

        # Verify changes detected
        assert result.has_changes
        assert result.patch_file == output_file
        assert output_file.exists()
        assert len(result.changed) > 0

    def test_run_all_empty_list(self, tmp_path: Path) -> None:
        """Test run_all with empty snapshot list."""
        template_path = tmp_path / 'template'
        source_project = tmp_path / 'project'
        output_dir = tmp_path / 'output'

        tester = TemporalTester(
            template_path=template_path,
            source_project=source_project,
            output_dir=output_dir,
        )

        results = tester.run_all([])
        assert results == []

    @pytest.fixture
    def git_test_repo(self, tmp_path: Path) -> Path:
        """Create a git test repository."""
        repo_path = tmp_path / 'test_repo'
        repo_path.mkdir()

        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=repo_path, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_path, check=True)
        subprocess.run(['git', 'config', 'commit.gpgsign', 'false'], cwd=repo_path, check=True)

        # Create initial commit
        (repo_path / 'README.md').write_text('# Test Project')
        subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_path, check=True, capture_output=True)

        # Create v1.0 tag
        subprocess.run(['git', 'tag', 'v1.0'], cwd=repo_path, check=True, capture_output=True)

        # Make another commit
        (repo_path / 'file.txt').write_text('version 2')
        subprocess.run(['git', 'add', '.'], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Add file'], cwd=repo_path, check=True, capture_output=True)

        # Create v2.0 tag
        subprocess.run(['git', 'tag', 'v2.0'], cwd=repo_path, check=True, capture_output=True)

        return repo_path

    def test_prepare_project(self, tmp_path: Path, git_test_repo: Path) -> None:
        """Test _prepare_project method."""
        template_path = tmp_path / 'template'
        output_dir = tmp_path / 'output'

        tester = TemporalTester(
            template_path=template_path,
            source_project=git_test_repo,
            output_dir=output_dir,
        )

        # Prepare project at v1.0
        temp_dir = tmp_path / 'temp'
        temp_dir.mkdir()
        project_dir = tester._prepare_project(temp_dir, 'v1.0')

        # Verify project was cloned
        assert project_dir.exists()
        assert (project_dir / '.git').exists()
        assert (project_dir / 'README.md').exists()
        # file.txt should not exist at v1.0
        assert not (project_dir / 'file.txt').exists()

    def test_prepare_project_at_different_ref(self, tmp_path: Path, git_test_repo: Path) -> None:
        """Test _prepare_project at different git ref."""
        template_path = tmp_path / 'template'
        output_dir = tmp_path / 'output'

        tester = TemporalTester(
            template_path=template_path,
            source_project=git_test_repo,
            output_dir=output_dir,
        )

        # Prepare project at v2.0
        temp_dir = tmp_path / 'temp'
        temp_dir.mkdir()
        project_dir = tester._prepare_project(temp_dir, 'v2.0')

        # Verify project was cloned at correct ref
        assert project_dir.exists()
        assert (project_dir / 'README.md').exists()
        # file.txt should exist at v2.0
        assert (project_dir / 'file.txt').exists()
        assert (project_dir / 'file.txt').read_text() == 'version 2'
