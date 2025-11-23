"""Tests for VCS abstraction layer."""

import subprocess
from pathlib import Path

import pytest

from copier_template_tester._vcs_utils import (
    GitVCS,
    JujutsuVCS,
    VCSBackend,
    detect_vcs,
    get_vcs,
)

from .configuration import TEST_DATA_DIR


class TestGitVCS:
    """Test Git VCS backend implementation."""

    def test_git_vcs_implements_protocol(self) -> None:
        """Verify GitVCS implements VCSBackend protocol."""
        git = GitVCS()
        assert isinstance(git, VCSBackend)

    def test_get_root_dir(self) -> None:
        """Test getting git repository root directory."""
        git = GitVCS()
        # Use existing git repo (this test repo)
        root = git.get_root_dir(TEST_DATA_DIR)
        assert root == TEST_DATA_DIR.parents[1]
        assert (root / '.git').exists()

    def test_get_root_dir_invalid_path(self, tmp_path: Path) -> None:
        """Test get_root_dir raises error for non-git directory."""
        git = GitVCS()
        with pytest.raises(subprocess.CalledProcessError):
            git.get_root_dir(tmp_path)

    def test_get_untracked_files_clean_repo(self, tmp_path: Path) -> None:
        """Test getting untracked files in clean repo."""
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmp_path, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=tmp_path, check=True)

        git = GitVCS()
        untracked = git.get_untracked_files(tmp_path)
        assert untracked == []

    def test_get_untracked_files_with_untracked(self, tmp_path: Path) -> None:
        """Test getting untracked files when files exist."""
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmp_path, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=tmp_path, check=True)

        # Create untracked files
        (tmp_path / 'test1.txt').write_text('test1')
        (tmp_path / 'test2.txt').write_text('test2')
        subdir = tmp_path / 'subdir'
        subdir.mkdir()
        (subdir / 'test3.txt').write_text('test3')

        git = GitVCS()
        untracked = git.get_untracked_files(tmp_path)
        assert 'test1.txt' in untracked
        assert 'test2.txt' in untracked
        assert 'subdir/' in untracked

    def test_is_repository_true(self) -> None:
        """Test is_repository returns True for git repo."""
        git = GitVCS()
        # This test repo is a git repository
        assert git.is_repository(TEST_DATA_DIR.parents[1])

    def test_is_repository_false(self, tmp_path: Path) -> None:
        """Test is_repository returns False for non-git directory."""
        git = GitVCS()
        assert not git.is_repository(tmp_path)

    def test_is_repository_with_git_dir(self, tmp_path: Path) -> None:
        """Test is_repository returns True when .git directory exists."""
        (tmp_path / '.git').mkdir()
        git = GitVCS()
        assert git.is_repository(tmp_path)


class TestJujutsuVCS:
    """Test Jujutsu VCS backend implementation."""

    def test_jujutsu_vcs_implements_protocol(self) -> None:
        """Verify JujutsuVCS implements VCSBackend protocol."""
        jj = JujutsuVCS()
        assert isinstance(jj, VCSBackend)

    def test_get_root_dir_no_jj_installed(self, tmp_path: Path) -> None:
        """Test get_root_dir raises error when jj not installed."""
        jj = JujutsuVCS()
        # jj is likely not installed in test environment
        with pytest.raises(subprocess.CalledProcessError):
            jj.get_root_dir(tmp_path)

    def test_is_repository_false(self, tmp_path: Path) -> None:
        """Test is_repository returns False for non-jj directory."""
        jj = JujutsuVCS()
        assert not jj.is_repository(tmp_path)

    def test_is_repository_with_jj_dir(self, tmp_path: Path) -> None:
        """Test is_repository returns True when .jj directory exists."""
        (tmp_path / '.jj').mkdir()
        jj = JujutsuVCS()
        assert jj.is_repository(tmp_path)


class TestVCSDetection:
    """Test VCS auto-detection functionality."""

    def test_detect_vcs_git_directory(self, tmp_path: Path) -> None:
        """Test detect_vcs finds Git when .git exists."""
        (tmp_path / '.git').mkdir()
        vcs = detect_vcs(tmp_path)
        assert isinstance(vcs, GitVCS)

    def test_detect_vcs_jj_directory(self, tmp_path: Path) -> None:
        """Test detect_vcs finds Jujutsu when .jj exists."""
        (tmp_path / '.jj').mkdir()
        vcs = detect_vcs(tmp_path)
        assert isinstance(vcs, JujutsuVCS)

    def test_detect_vcs_jj_priority(self, tmp_path: Path) -> None:
        """Test detect_vcs prefers Jujutsu over Git when both exist."""
        (tmp_path / '.git').mkdir()
        (tmp_path / '.jj').mkdir()
        vcs = detect_vcs(tmp_path)
        # Jujutsu has priority
        assert isinstance(vcs, JujutsuVCS)

    def test_detect_vcs_git_command(self) -> None:
        """Test detect_vcs finds Git via command when in git repo."""
        # Use existing git repo (this test repo)
        vcs = detect_vcs(TEST_DATA_DIR)
        assert isinstance(vcs, GitVCS)

    def test_detect_vcs_no_vcs(self, tmp_path: Path) -> None:
        """Test detect_vcs raises error when no VCS found."""
        with pytest.raises(RuntimeError, match='No VCS detected'):
            detect_vcs(tmp_path)

    def test_detect_vcs_caching(self, tmp_path: Path) -> None:
        """Test detect_vcs uses LRU cache."""
        (tmp_path / '.git').mkdir()

        # Call twice with same path
        vcs1 = detect_vcs(tmp_path)
        vcs2 = detect_vcs(tmp_path)

        # Should return same instance due to caching
        assert vcs1 is vcs2


class TestGetVCS:
    """Test VCS factory function."""

    def test_get_vcs_auto_mode(self) -> None:
        """Test get_vcs with auto detection."""
        vcs = get_vcs(TEST_DATA_DIR, vcs_type='auto')
        assert isinstance(vcs, GitVCS)

    def test_get_vcs_explicit_git(self, tmp_path: Path) -> None:
        """Test get_vcs with explicit git type."""
        vcs = get_vcs(tmp_path, vcs_type='git')
        assert isinstance(vcs, GitVCS)

    def test_get_vcs_explicit_jj(self, tmp_path: Path) -> None:
        """Test get_vcs with explicit jj type."""
        vcs = get_vcs(tmp_path, vcs_type='jj')
        assert isinstance(vcs, JujutsuVCS)

    def test_get_vcs_explicit_jujutsu(self, tmp_path: Path) -> None:
        """Test get_vcs with explicit jujutsu type."""
        vcs = get_vcs(tmp_path, vcs_type='jujutsu')
        assert isinstance(vcs, JujutsuVCS)

    def test_get_vcs_invalid_type(self, tmp_path: Path) -> None:
        """Test get_vcs raises error for invalid type."""
        with pytest.raises(ValueError, match="Invalid vcs_type 'invalid'"):
            get_vcs(tmp_path, vcs_type='invalid')

    def test_get_vcs_default_auto(self) -> None:
        """Test get_vcs defaults to auto mode."""
        vcs = get_vcs(TEST_DATA_DIR)
        assert isinstance(vcs, GitVCS)
