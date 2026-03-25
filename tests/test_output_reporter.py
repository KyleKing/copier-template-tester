import pytest

from copier_template_tester._output_reporter import RunReporter, group_context


def test_group_context_local_header(capsys) -> None:
    with group_context('my-test'):
        print('inner')  # noqa: T201

    out = capsys.readouterr().out
    assert '\n--- Test: my-test ---\n' in out
    assert 'inner' in out


def test_group_context_github_actions(monkeypatch, capsys) -> None:
    monkeypatch.setenv('GITHUB_ACTIONS', 'true')

    with group_context('my-test'):
        print('inner')  # noqa: T201

    out = capsys.readouterr().out
    assert '::group::my-test\n' in out
    assert '::endgroup::\n' in out
    assert 'inner' in out


def test_group_context_endgroup_on_exception_github_actions(monkeypatch, capsys) -> None:
    monkeypatch.setenv('GITHUB_ACTIONS', 'true')

    with pytest.raises(ValueError), group_context('fail-test'):  # noqa: PT011
        raise ValueError('boom')

    out = capsys.readouterr().out
    assert '::endgroup::\n' in out


def test_group_context_no_extra_output_on_exception_local(capsys) -> None:
    with pytest.raises(ValueError), group_context('fail-local'):  # noqa: PT011
        raise ValueError('boom')

    out = capsys.readouterr().out
    assert '--- Test: fail-local ---' in out


def test_run_reporter_no_failures(capsys) -> None:
    reporter = RunReporter()
    reporter.summary()
    out = capsys.readouterr().out
    assert '--- CTT Summary ---' in out
    assert 'PASS' not in out


def test_run_reporter_records_pass_and_fail(capsys) -> None:
    reporter = RunReporter()
    reporter.record_pass('test-a')
    reporter.record_failure('test-b', ValueError('bad thing'))
    reporter.summary()

    out = capsys.readouterr().out
    assert 'PASS  test-a' in out
    assert 'FAIL  test-b' in out
    assert 'bad thing' in out
    assert '1 failure(s)' in out


def test_run_reporter_all_pass_no_failure_line(capsys) -> None:
    reporter = RunReporter()
    reporter.record_pass('test-a')
    reporter.record_pass('test-b')
    reporter.summary()

    out = capsys.readouterr().out
    assert 'PASS  test-a' in out
    assert 'PASS  test-b' in out
    assert 'failure(s)' not in out


def test_run_reporter_github_actions_error_prefix(monkeypatch, capsys) -> None:
    monkeypatch.setenv('GITHUB_ACTIONS', 'true')
    reporter = RunReporter()
    reporter.record_failure('test-x', RuntimeError('oops'))
    reporter.summary()

    out = capsys.readouterr().out
    assert '::error::1 failure(s)' in out


def test_run_reporter_raise_if_any_failures() -> None:
    reporter = RunReporter()
    reporter.record_failure('bad', Exception('err'))

    with pytest.raises(SystemExit) as exc_info:
        reporter.raise_if_any_failures()

    assert exc_info.value.code == 1


def test_run_reporter_no_raise_when_no_failures() -> None:
    reporter = RunReporter()
    reporter.raise_if_any_failures()  # should not raise
