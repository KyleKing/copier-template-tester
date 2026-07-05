import os
import shutil
import subprocess  # noqa: S404
from pathlib import Path

import pytest
from copier._main import Worker
from pytestshellutils.shell import Subprocess
from pytestshellutils.utils.processes import MatchString

from copier_template_tester._write_output import read_copier_template
from copier_template_tester.main import _filter_test_cases, _resolve_post_tasks, list_test_cases, run

from .configuration import TEST_DATA_DIR
from .helpers import DEMO_DIR, NO_ANSWER_FILE_DIR, run_ctt

CI_USAGE_TEST_DIR = TEST_DATA_DIR / 'ci_usage_test'
FAILING_TASK_DIR = TEST_DATA_DIR / 'failing_task_demo'
EXPECTED_COPY_CALLS = 3
EXPECTED_FILTERED_COPY_CALLS = 2

WITH_INCLUDE_DIR = TEST_DATA_DIR / 'copier_include'


@pytest.mark.parametrize('base_dir', [DEMO_DIR, NO_ANSWER_FILE_DIR])
def test_main_with_copier_mock(monkeypatch, base_dir: Path) -> None:
    """Only necessary for coverage metrics, but the .ctt/* files must exist."""

    def _run_copy(worker) -> None:
        pass

    monkeypatch.setattr(Worker, 'run_copy', _run_copy)

    run(base_dir=base_dir)


def check_run_ctt(*, shell: Subprocess, cwd: Path, subdirname: str) -> tuple[set[Path], MatchString, MatchString]:
    ret = run_ctt(shell, cwd=cwd)

    assert ret.returncode == 0, ret.stderr
    # Check output from ctt and copier (where order can vary on Windows)
    ret.stdout.matcher.fnmatch_lines(
        [
            'Starting Copier Template Tester for *',
            '*Note: If files were modified, pre-commit will report a failure.',
            '',
            f'--- Test: .ctt/{subdirname} ---',
            f'Using `copier` to create: .ctt/{subdirname}',
        ],
    )
    ret.stderr.matcher.fnmatch_lines_random(
        [
            '*Copying from template*',
        ],
    )
    # Check a few of the created files:
    return {pth.relative_to(cwd) for pth in (cwd / '.ctt').rglob('*.*') if pth.is_file()}, ret.stdout, ret.stderr


def test_main(shell: Subprocess) -> None:
    paths, stdout, _stderr = check_run_ctt(shell=shell, cwd=DEMO_DIR, subdirname='no_all')

    assert Path('.ctt/no_all/README.md') in paths
    assert Path('.ctt/no_all/.copier-answers.testing_no_all.yml') in paths
    assert Path('.ctt/no_all/.copier-answers.yml') not in paths
    stdout.matcher.fnmatch_lines_random(
        [
            'task_string',
            'task_list',
            'task_dict',
        ],
    )


def test_no_answer_file_dir(shell: Subprocess) -> None:
    paths, _stdout, _stderr = check_run_ctt(shell=shell, cwd=NO_ANSWER_FILE_DIR, subdirname='no_answers_file')

    assert Path('.ctt/no_answers_file/README.md') in paths
    assert not [*Path('.ctt/no_answers_file').rglob('.copier-answers*')]


def test_with_include_dir(shell: Subprocess) -> None:
    paths, _stdout, _stderr = check_run_ctt(shell=shell, cwd=WITH_INCLUDE_DIR, subdirname='copier_include')

    assert Path('.ctt/copier_include/script.py') in paths


def test_missing_copier_config(shell: Subprocess) -> None:
    ret = run_ctt(shell, cwd=TEST_DATA_DIR / 'no_copier_config')

    assert ret.returncode == 0
    ret.stdout.matcher.fnmatch_lines(["Please add a 'copier.yaml' file to '*no_copier_config'*"])


def test_missing_ctt_config(shell: Subprocess) -> None:
    ret = run_ctt(shell, cwd=TEST_DATA_DIR / 'no_ctt_config')

    assert ret.returncode == 1
    ret.stderr.matcher.fnmatch_lines(['*No configuration file found. Expected: *ctt.toml*'])


def test_no_subdir(shell: Subprocess) -> None:
    ret = run_ctt(shell, cwd=TEST_DATA_DIR / 'no_subdir_nor_exclude')

    assert ret.returncode == 0
    ret.stdout.matcher.fnmatch_lines(
        [
            '--- Test: .ctt/no_subdir_nor_exclude ---',
            '*Using `copier` to create: .ctt/no_subdir_nor_exclude*',
        ]
    )


def test_skip_tasks(shell: Subprocess) -> None:
    paths, stdout, stderr = check_run_ctt(shell=shell, cwd=DEMO_DIR, subdirname='skip_tasks')

    assert Path('.ctt/skip_tasks/README.md') in paths
    stderr.matcher.fnmatch_lines_random(
        [' > Running task 1 of 3: *', ' > Running task 2 of 3: *', ' > Running task 3 of 3: *'],
    )
    stdout.matcher.fnmatch_lines_random(['task_string', 'task_list', 'task_dict'])


def test_pre_tasks(shell: Subprocess) -> None:
    paths, stdout, stderr = check_run_ctt(shell=shell, cwd=DEMO_DIR, subdirname='pre_tasks')

    assert Path('.ctt/pre_tasks/README.md') in paths
    stderr.matcher.fnmatch_lines_random(
        [' > Running task 1 of 5: *', ' > Running task 2 of 5: *', ' > Running task 5 of 5: *'],
    )
    stdout.matcher.fnmatch_lines_random(
        [
            'pre_first',
            'template_task_from_copier_yml',
            'task_string',
        ],
    )


def test_run_continue_on_error_collects_failures(monkeypatch, capsys) -> None:
    """With continue_on_error, all keys are attempted and a summary is printed."""
    call_count = 0

    def _run_copy(worker) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError('first case failed')

    monkeypatch.setattr(Worker, 'run_copy', _run_copy)

    with pytest.raises(SystemExit) as exc_info:
        run(base_dir=DEMO_DIR, continue_on_error=True)

    assert exc_info.value.code == 1
    assert call_count == EXPECTED_COPY_CALLS
    out = capsys.readouterr().out
    assert '--- CTT Summary ---' in out
    assert 'FAIL' in out
    assert 'PASS' in out


def _stub_run_copy(monkeypatch, ran_paths: list[str]) -> None:
    def _run_copy(worker) -> None:
        ran_paths.append(str(worker.dst_path))

    monkeypatch.setattr(Worker, 'run_copy', _run_copy)


def test_run_test_case_filters_single_match(monkeypatch) -> None:
    ran_paths: list[str] = []
    _stub_run_copy(monkeypatch, ran_paths)

    run(base_dir=DEMO_DIR, test_case_filters=['no_all'])

    assert len(ran_paths) == 1
    assert any('no_all' in pth for pth in ran_paths)


def test_run_test_case_filters_multiple_match(monkeypatch) -> None:
    ran_paths: list[str] = []
    _stub_run_copy(monkeypatch, ran_paths)

    run(base_dir=DEMO_DIR, test_case_filters=['no_all', 'pre_tasks'])

    assert len(ran_paths) == EXPECTED_FILTERED_COPY_CALLS
    assert any('no_all' in pth for pth in ran_paths)
    assert any('pre_tasks' in pth for pth in ran_paths)


def test_run_test_case_filters_partial_substring(monkeypatch) -> None:
    ran_paths: list[str] = []
    _stub_run_copy(monkeypatch, ran_paths)

    run(base_dir=DEMO_DIR, test_case_filters=['tasks'])

    assert len(ran_paths) == EXPECTED_FILTERED_COPY_CALLS
    assert any('pre_tasks' in pth for pth in ran_paths)
    assert any('skip_tasks' in pth for pth in ran_paths)


def test_run_no_filter_runs_all(monkeypatch) -> None:
    ran_paths: list[str] = []
    _stub_run_copy(monkeypatch, ran_paths)

    run(base_dir=DEMO_DIR)

    assert len(ran_paths) == EXPECTED_COPY_CALLS


def test_run_test_case_filters_no_match_raises(monkeypatch) -> None:
    ran_paths: list[str] = []
    _stub_run_copy(monkeypatch, ran_paths)

    with pytest.raises(RuntimeError, match='No test cases matching filters') as exc_info:
        run(base_dir=DEMO_DIR, test_case_filters=['nonexistent_filter'])

    assert 'Available test cases: [' in str(exc_info.value)


def test_run_test_case_filters_empty_string_no_match(monkeypatch) -> None:
    ran_paths: list[str] = []
    _stub_run_copy(monkeypatch, ran_paths)

    with pytest.raises(RuntimeError, match='No test cases matching filters'):
        run(base_dir=DEMO_DIR, test_case_filters=[''])


def test_run_test_case_filters_with_continue_on_error(monkeypatch, capsys) -> None:
    call_count = 0

    def _run_copy(worker) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError('first case failed')

    monkeypatch.setattr(Worker, 'run_copy', _run_copy)

    with pytest.raises(SystemExit) as exc_info:
        run(base_dir=DEMO_DIR, continue_on_error=True, test_case_filters=['no_all', 'pre_tasks'])

    assert exc_info.value.code == 1
    assert call_count == EXPECTED_FILTERED_COPY_CALLS
    out = capsys.readouterr().out
    assert '--- CTT Summary ---' in out


def test_filter_test_cases_no_match_raises() -> None:
    with pytest.raises(RuntimeError, match='No test cases matching filters'):
        _filter_test_cases({'a': {}, 'b': {}}, ['nonexistent'])


def test_list_test_cases_prints_all(capsys) -> None:
    list_test_cases(base_dir=DEMO_DIR)

    out = capsys.readouterr().out
    assert '.ctt/no_all' in out
    assert '.ctt/pre_tasks' in out
    assert '.ctt/skip_tasks' in out


def test_list_test_cases_with_filter(capsys) -> None:
    list_test_cases(base_dir=DEMO_DIR, test_case_filters=['tasks'])

    out = capsys.readouterr().out
    assert '.ctt/no_all' not in out
    assert '.ctt/pre_tasks' in out
    assert '.ctt/skip_tasks' in out


def test_list_test_cases_no_match_raises() -> None:
    with pytest.raises(RuntimeError, match='No test cases matching filters'):
        list_test_cases(base_dir=DEMO_DIR, test_case_filters=['nonexistent_filter'])


def test_cli_list_test_cases(shell: Subprocess) -> None:
    ret = run_ctt(shell, cwd=DEMO_DIR, args=['--list'])

    assert ret.returncode == 0, ret.stderr
    out = str(ret.stdout)
    assert '.ctt/no_all' in out
    assert '.ctt/pre_tasks' in out
    assert '.ctt/skip_tasks' in out
    assert 'Using `copier` to create' not in out


@pytest.mark.parametrize(
    ('data', 'expected'),
    [
        ({'_extra_tasks': ['et1']}, ['et1']),
        ({'_extra_tasks': ['et1'], '_post_tasks': ['pt1']}, ['pt1']),
    ],
    ids=[
        'extra_tasks_only returns extra_tasks',
        'both present prefers post_tasks',
    ],
)
def test_resolve_post_tasks_with_extra_tasks(data, expected) -> None:
    assert _resolve_post_tasks(data) == expected


def test_cli_test_case_filter(shell: Subprocess) -> None:
    ret = run_ctt(shell, cwd=DEMO_DIR, args=['-t', 'no_all'])

    assert ret.returncode == 0, ret.stderr
    ret.stdout.matcher.fnmatch_lines(
        [
            '--- Test: .ctt/no_all ---',
            'Using `copier` to create: .ctt/no_all',
        ],
    )
    combined = str(ret.stdout) + str(ret.stderr)
    assert '.ctt/pre_tasks' not in combined
    assert '.ctt/skip_tasks' not in combined


def test_cli_test_case_filter_no_match(shell: Subprocess) -> None:
    ret = run_ctt(shell, cwd=DEMO_DIR, args=['-t', 'nonexistent_filter'])

    assert ret.returncode != 0
    combined = str(ret.stdout) + str(ret.stderr)
    assert 'No test cases matching filters' in combined


def test_run_missing_copier_template(tmp_path) -> None:
    read_copier_template.cache_clear()

    run(base_dir=tmp_path)


def _run_ctt_merged(cwd: Path, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run ctt as a subprocess with stderr merged into stdout, simulating GHA log stream."""
    return subprocess.run(  # noqa: S603
        ['uv', 'run', 'ctt', *(extra_args or [])],  # noqa: S607
        cwd=cwd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={**os.environ, 'GITHUB_ACTIONS': 'true'},
    )


def test_github_actions_group_ordering_on_success(tmp_path) -> None:
    """In the merged stdout+stderr log, ::group:: must precede copier output and ::endgroup:: must follow it."""
    cwd = tmp_path / 'ci_usage_test'
    shutil.copytree(CI_USAGE_TEST_DIR, cwd)

    result = _run_ctt_merged(cwd)

    lines = result.stdout.splitlines()
    group_idx = next((i for i, ln in enumerate(lines) if ln.startswith('::group::')), None)
    copier_idx = next((i for i, ln in enumerate(lines) if 'Copying from template' in ln), None)
    endgroup_idx = next((i for i, ln in enumerate(lines) if ln == '::endgroup::'), None)

    assert group_idx is not None, f'Missing ::group:: in:\n{result.stdout}'
    assert copier_idx is not None, f'Missing copier output in:\n{result.stdout}'
    assert endgroup_idx is not None, f'Missing ::endgroup:: in:\n{result.stdout}'
    assert group_idx < copier_idx, f'::group:: (line {group_idx}) must precede copier output (line {copier_idx})'
    assert copier_idx < endgroup_idx, (
        f'copier output (line {copier_idx}) must precede ::endgroup:: (line {endgroup_idx})'
    )


def test_github_actions_endgroup_emitted_on_task_failure(tmp_path) -> None:
    """::endgroup:: is emitted even when a copier task fails."""
    cwd = tmp_path / 'failing_task_demo'
    shutil.copytree(FAILING_TASK_DIR, cwd)

    result = _run_ctt_merged(cwd, extra_args=['--continue-on-error'])

    lines = result.stdout.splitlines()
    assert any(ln.startswith('::group::') for ln in lines), f'Missing ::group:: in:\n{result.stdout}'
    assert any(ln == '::endgroup::' for ln in lines), f'Missing ::endgroup:: in:\n{result.stdout}'
    assert result.returncode == 1
