from pathlib import Path

import pytest

from copier_template_tester._write_output import (
    DEFAULT_ANSWER_FILE_NAME,
    _clear_output_dir,
    _find_answers_file,
    _is_git_repo_root,
    _isolated_source,
    _relative_src_path,
    _resolve_git_root_dir,
    _run_git,
    _stabilize_answers_file,
    read_copier_template,
    write_output,
)

from .configuration import TEST_DATA_DIR


def _make_template(base_dir: Path, *, config: str, files: dict[str, str]) -> Path:
    read_copier_template.cache_clear()
    _find_answers_file.cache_clear()
    base_dir.mkdir(parents=True)
    (base_dir / 'copier.yaml').write_text(config)
    for name, content in files.items():
        (base_dir / name).write_text(content)
    dst_path = base_dir / '.ctt' / 'out'
    dst_path.mkdir(parents=True)
    return dst_path


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


def test_write_output_refreshes_skip_if_exists_files(tmp_path: Path) -> None:
    """`_skip_if_exists` outranks `overwrite` in copier, so only clearing keeps the render honest."""
    base_dir = tmp_path / 'tmpl'
    dst_path = _make_template(
        base_dir,
        config='_skip_if_exists:\n  - keeper.txt\n',
        files={'keeper.txt': 'fresh keeper\n', 'other.txt': 'fresh other\n'},
    )
    (dst_path / 'keeper.txt').write_text('stale keeper\n')
    (dst_path / 'other.txt').write_text('stale other\n')

    write_output(base_dir=base_dir, src_path=base_dir, dst_path=dst_path, data={})

    assert (dst_path / 'keeper.txt').read_text() == 'fresh keeper\n'
    assert (dst_path / 'other.txt').read_text() == 'fresh other\n'


def test_write_output_removes_files_no_longer_generated(tmp_path: Path) -> None:
    base_dir = tmp_path / 'tmpl'
    dst_path = _make_template(base_dir, config='{}\n', files={'kept.txt': 'generated\n'})
    (dst_path / 'obsolete.txt').write_text('from an older template\n')
    (dst_path / 'obsolete_dir').mkdir()
    (dst_path / 'obsolete_dir' / 'nested.txt').write_text('also stale\n')

    write_output(base_dir=base_dir, src_path=base_dir, dst_path=dst_path, data={})

    assert (dst_path / 'kept.txt').is_file()
    assert not (dst_path / 'obsolete.txt').exists()
    assert not (dst_path / 'obsolete_dir').exists()


def test_write_output_keep_output_preserves_extra_files(tmp_path: Path) -> None:
    base_dir = tmp_path / 'tmpl'
    dst_path = _make_template(base_dir, config='{}\n', files={'kept.txt': 'generated\n'})
    (dst_path / 'external.txt').write_text('written by something other than the template\n')

    write_output(base_dir=base_dir, src_path=base_dir, dst_path=dst_path, data={}, keep_output=True)

    assert (dst_path / 'external.txt').is_file()


def test_clear_output_dir_rejects_paths_outside_the_template(tmp_path: Path) -> None:
    base_dir = tmp_path / 'tmpl'
    real_project = tmp_path / 'real_project'
    for pth in (base_dir, real_project):
        pth.mkdir()
    (real_project / 'precious.txt').write_text('do not delete\n')

    # `base_dir / key` yields `key` itself when the ctt.toml key is absolute
    for dst_path in (base_dir / real_project, base_dir / '..' / 'real_project', base_dir):
        with pytest.raises(ValueError, match='outside the template'):
            _clear_output_dir(base_dir=base_dir, dst_path=dst_path)

    assert (real_project / 'precious.txt').is_file()


def test_clear_output_dir_rejects_a_git_repository(tmp_path: Path) -> None:
    base_dir = tmp_path / 'tmpl'
    dst_path = base_dir / '.ctt' / 'out'
    (dst_path / '.git').mkdir(parents=True)

    with pytest.raises(ValueError, match='looks like a git repository'):
        _clear_output_dir(base_dir=base_dir, dst_path=dst_path)
