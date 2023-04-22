
import sys
from contextlib import nullcontext as does_not_raise
from pathlib import Path

import pytest
from beartype import beartype
from pytestshellutils.shell import Subprocess

from copier_template_tester._pre_commit_support import check_for_untracked

from .configuration import TEST_DATA_DIR
from .helpers import DEMO_DIR, ExpectedError, add_commit, run_ctt, temporary_git_dir


@pytest.mark.parametrize(
    ('expect_untracked', 'paths'),
    [
        (True, ['out_2/.a']),
        (True, ['out/a/b/c.txt']),
        (False, ['a/not-in-out.txt']),
    ],
    ids=[
        'check a dotfile',
        'check a nested file',
        'check file outside of output path',
    ],
)
@beartype
def test_check_for_untracked(*, expect_untracked: bool, paths: list[str], shell: Subprocess, monkeypatch) -> None:
    @beartype
    def raise_int(arg: int) -> None:
        msg = f'arg={arg}'
        raise ExpectedError(msg)

    monkeypatch.setattr(sys, 'exit', raise_int)
    with temporary_git_dir(shell) as copier_dir:
        (copier_dir / 'init.txt').write_text('')
        add_commit(shell, cwd=copier_dir)
        for pth in paths:
            new_file = copier_dir / pth
            new_file.parent.mkdir(exist_ok=True, parents=True)
            new_file.write_text(pth)

        output_paths = {copier_dir / 'out', copier_dir / 'out_2'}
        with pytest.raises(ExpectedError, match=r'^arg=1$') if expect_untracked else does_not_raise():
            check_for_untracked(output_paths, copier_dir)


@beartype
def test_ctt_with_untracked_files(shell: Subprocess) -> None:
    untracked_file = Path('template_dir/untracked_file.txt')
    with temporary_git_dir(shell, source_dir=DEMO_DIR) as copier_dir:
        first_pass = run_ctt(shell, cwd=TEST_DATA_DIR, args=[f'--base-dir={copier_dir}'])
        assert first_pass.returncode == 0

        (copier_dir / untracked_file).write_text('Placeholder\n')
        add_commit(shell, cwd=copier_dir)
        ret = run_ctt(shell, cwd=TEST_DATA_DIR, args=[f'--base-dir={copier_dir}', '--check-untracked'])
        # Store paths to check later
        paths = {pth.relative_to(copier_dir) for pth in (copier_dir / '.ctt').rglob('*.*') if pth.is_file()}

    assert ret.returncode == 1
    ret.stdout.matcher.fnmatch_lines(['*Creating:*copier_demo*no_all*', ''])
    # Check output from copier
    ret.stderr.matcher.fnmatch_lines_random([  # Order can vary on Windows
        '*Copying from template*',
        '*conflict* .copier-answers.testing_no_all.yml*',
        f'*create* {untracked_file.name}*',
    ])
    # Check created files:
    assert Path(f'.ctt/no_all/{untracked_file.name}') in paths
