from pathlib import Path

import pytest

from copier_template_tester._write_output import (
    DEFAULT_ANSWER_FILE_NAME,
    _find_answers_file,
    _is_git_repo_root,
    _isolated_source,
    _relative_src_path,
    _resolve_git_root_dir,
    _run_git,
    _stabilize_answers_file,
    read_copier_template,
)

from .configuration import TEST_DATA_DIR


def _init_repo(root: Path) -> None:
    _run_git(['init'], cwd=root)
    _run_git(['config', 'user.email', 'ctt@ctt.ctt'], cwd=root)
    _run_git(['config', 'user.name', 'Carl The Template'], cwd=root)


def test_resolve_git_root_dir() -> None:
    assert _resolve_git_root_dir(TEST_DATA_DIR) == TEST_DATA_DIR.parents[1]


def test_is_git_repo_root(tmp_path: Path) -> None:
    assert not _is_git_repo_root(tmp_path)  # not a git repo at all
    assert not _is_git_repo_root(TEST_DATA_DIR)  # tracked, but not the repo root
    assert _is_git_repo_root(_resolve_git_root_dir(TEST_DATA_DIR))


def test_relative_src_path(tmp_path: Path) -> None:
    base_dir = tmp_path / 'my_template'
    answers_path = base_dir / '.ctt' / 'default' / DEFAULT_ANSWER_FILE_NAME
    answers_path.parent.mkdir(parents=True)

    assert _relative_src_path(base_dir=base_dir, answers_path=answers_path) == '../../my_template'


@pytest.mark.parametrize('is_repo_root', [True, False])
def test_stabilize_answers_file(tmp_path: Path, is_repo_root: bool) -> None:  # noqa: FBT001
    read_copier_template.cache_clear()
    _find_answers_file.cache_clear()

    base_dir = tmp_path / 'tmpl'
    base_dir.mkdir()
    (base_dir / 'copier.yaml').write_text('_answers_file: .copier-answers.yml\n')
    dst_path = base_dir / '.ctt' / 'out'
    dst_path.mkdir(parents=True)
    answers_path = dst_path / DEFAULT_ANSWER_FILE_NAME
    answers_path.write_text('# header\n_commit: abc123\n\n_src_path: /abs/leaked/temp\nkey: value\n')

    _stabilize_answers_file(base_dir=base_dir, src_path=base_dir, dst_path=dst_path, is_repo_root=is_repo_root)

    content = answers_path.read_text()
    assert '_src_path: ../../tmpl' in content
    assert '/abs/leaked/temp' not in content
    assert 'abc123' not in content
    assert ('_commit: HEAD' in content) is is_repo_root


def test_isolated_source_non_git_passthrough(tmp_path: Path) -> None:
    with _isolated_source(tmp_path) as snapshot:
        assert snapshot == tmp_path


def test_isolated_source_snapshots_working_tree(tmp_path: Path) -> None:
    repo = tmp_path / 'repo'
    repo.mkdir()
    _init_repo(repo)
    (repo / 'tracked.txt').write_text('committed\n')
    _run_git(['add', '.'], cwd=repo)
    _run_git(['commit', '-m', 'init'], cwd=repo)
    # An unstaged edit plus a newly staged file: `git stash create` must capture both.
    (repo / 'tracked.txt').write_text('modified\n')
    (repo / 'staged.txt').write_text('staged\n')
    _run_git(['add', 'staged.txt'], cwd=repo)

    with _isolated_source(repo) as snapshot:
        assert snapshot != repo
        assert not (snapshot / '.git').exists()
        assert (snapshot / 'tracked.txt').read_text() == 'modified\n'
        assert (snapshot / 'staged.txt').read_text() == 'staged\n'
        held = snapshot

    assert not held.exists()  # cleaned up on context exit
