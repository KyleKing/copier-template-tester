import sys
from pathlib import Path

import pytest
from beartype import beartype
from pytestshellutils.shell import Subprocess

from copier_template_tester._pre_commit_support import check_for_untracked  # noqa: PLC2701

from .configuration import TEST_DATA_DIR
from .helpers import DEMO_DIR, ExpectedError, add_commit, run_ctt, temporary_git_dir


@pytest.mark.parametrize(
    'paths',
    [
        ['.ctt'],
        ['out_2/.a'],
        ['out/a/b/c.txt'],
    ],
    ids=[
        'check a top-level directory',
        'check a dotfile',
        'check a nested file',
    ],
)
@beartype
def test_check_for_untracked(*, paths: list[str], shell: Subprocess, monkeypatch) -> None:
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

        with pytest.raises(ExpectedError, match=r'^arg=1$'):
            check_for_untracked(copier_dir)


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
    # Check output from ctt and copier (where order can vary on Windows)
    ret.stdout.matcher.fnmatch_lines([
        'Starting Copier Template Tester for *',
        '*Note: If files were modified, pre-commit will report a failure.',
        '',
        'Using `copier` to create: .ctt/no_all',
    ])
    ret.stderr.matcher.fnmatch_lines_random([
        '*Copying from template*',
        '*conflict* .copier-answers.testing_no_all.yml*',
        f'*create* {untracked_file.name}*',
    ])
    # Check created files:
    assert Path('.ctt/no_all/.copier-answers.testing_no_all.yml') in paths
    assert Path('.ctt/no_all/.copier-answers.yml') not in paths
    assert Path(f'.ctt/no_all/{untracked_file.name}') in paths
