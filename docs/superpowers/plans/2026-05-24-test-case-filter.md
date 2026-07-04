# Test Case Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `--test-case` / `-t` CLI flag that filters which CTT test cases run by case-sensitive substring match.

**Architecture:** The filter is applied after config is loaded in `run()`, replacing `config['output']` with only matching entries before the existing test loop executes. `run_cli()` passes the collected filter list through to `run()`. No other layers change.

**Tech Stack:** Python stdlib `argparse`, existing `load_config`, `pytest` + `pytestshellutils` for subprocess tests.

---

### Task 1: Add `test_case_filters` parameter to `run()` with filtering logic

**Files:**

- Modify: `copier_template_tester/main.py:42-91`

- [ ] **Step 1: Update the `run()` signature**

In `copier_template_tester/main.py`, change line 42 from:

```python
def run(*, base_dir: Path | None = None, check_untracked: bool = False, continue_on_error: bool = False) -> None:
```

to:

```python
def run(
    *,
    base_dir: Path | None = None,
    check_untracked: bool = False,
    continue_on_error: bool = False,
    test_case_filters: list[str] | None = None,
) -> None:
```

- [ ] **Step 2: Add filtering logic after `load_config`**

In `run()`, after the line `defaults = config.get('defaults', {})` (currently line 56), insert:

```python
    if test_case_filters:
        active_filters = [f for f in test_case_filters if f]
        matched = {key: data for key, data in config['output'].items() if any(f in key for f in active_filters)}
        if not matched:
            available = list(config['output'].keys())
            raise RuntimeError(
                f'No test cases matching filters: {test_case_filters}. '
                f'Available test cases: {available}'
            )
        config['output'] = matched
```

The full `run()` body from that point should look like:

```python
    config = load_config(base_dir)
    defaults = config.get('defaults', {})

    if test_case_filters:
        active_filters = [f for f in test_case_filters if f]
        matched = {key: data for key, data in config['output'].items() if any(f in key for f in active_filters)}
        if not matched:
            available = list(config['output'].keys())
            raise RuntimeError(
                f'No test cases matching filters: {test_case_filters}. '
                f'Available test cases: {available}'
            )
        config['output'] = matched

    input_path = base_dir
    # ... rest of loop unchanged
```

- [ ] **Step 3: Verify no tests are broken yet**

```bash
uv run pytest tests/test_main.py -x -q
```

Expected: all existing tests pass (the new parameter defaults to `None`, preserving existing behavior).

- [ ] **Step 4: Commit**

```bash
git add copier_template_tester/main.py
git commit -m "feat(#44): add test_case_filters parameter to run()"
```

---

### Task 2: Unit tests for filtering logic

**Files:**

- Modify: `tests/test_main.py`

The `DEMO_DIR` config (`tests/data/copier_demo/ctt.toml`) has three test cases:

- `.ctt/no_all`
- `.ctt/pre_tasks`
- `.ctt/skip_tasks`

These tests use `monkeypatch` to stub out `Worker.run_copy` so no actual files are generated.

- [ ] **Step 1: Write failing tests for filter behavior**

Add these test functions to `tests/test_main.py` (after `test_run_missing_copier_template`):

```python
def test_run_single_filter(monkeypatch) -> None:
    """Only the matching test case runs when a single filter is given."""
    run_keys: list[str] = []

    def _run_copy(worker) -> None:
        run_keys.append(str(worker.dst_path))

    monkeypatch.setattr(Worker, 'run_copy', _run_copy)

    run(base_dir=DEMO_DIR, test_case_filters=['no_all'])

    assert len(run_keys) == 1
    assert 'no_all' in run_keys[0]


def test_run_multiple_filters(monkeypatch) -> None:
    """All matching test cases run when multiple filters are given."""
    run_keys: list[str] = []

    def _run_copy(worker) -> None:
        run_keys.append(str(worker.dst_path))

    monkeypatch.setattr(Worker, 'run_copy', _run_copy)

    run(base_dir=DEMO_DIR, test_case_filters=['no_all', 'pre_tasks'])

    assert len(run_keys) == 2
    assert any('no_all' in k for k in run_keys)
    assert any('pre_tasks' in k for k in run_keys)


def test_run_no_filter_runs_all(monkeypatch) -> None:
    """Backward compatibility: no filter means all test cases run."""
    run_keys: list[str] = []

    def _run_copy(worker) -> None:
        run_keys.append(str(worker.dst_path))

    monkeypatch.setattr(Worker, 'run_copy', _run_copy)

    run(base_dir=DEMO_DIR)

    assert len(run_keys) == EXPECTED_COPY_CALLS  # 3


def test_run_partial_substring_filter(monkeypatch) -> None:
    """Substring match works — 'task' matches 'pre_tasks' and 'skip_tasks'."""
    run_keys: list[str] = []

    def _run_copy(worker) -> None:
        run_keys.append(str(worker.dst_path))

    monkeypatch.setattr(Worker, 'run_copy', _run_copy)

    run(base_dir=DEMO_DIR, test_case_filters=['tasks'])

    assert len(run_keys) == 2
    assert any('pre_tasks' in k for k in run_keys)
    assert any('skip_tasks' in k for k in run_keys)


def test_run_no_matching_filter_raises(monkeypatch) -> None:
    """RuntimeError is raised when no test cases match the filter."""

    def _run_copy(worker) -> None:
        pass

    monkeypatch.setattr(Worker, 'run_copy', _run_copy)

    with pytest.raises(RuntimeError, match='No test cases matching filters'):
        run(base_dir=DEMO_DIR, test_case_filters=['nonexistent_filter'])


def test_run_filter_error_lists_available(monkeypatch) -> None:
    """The RuntimeError message includes the list of available test cases."""

    def _run_copy(worker) -> None:
        pass

    monkeypatch.setattr(Worker, 'run_copy', _run_copy)

    with pytest.raises(RuntimeError, match=r'Available test cases: \['):
        run(base_dir=DEMO_DIR, test_case_filters=['nonexistent_filter'])


def test_run_empty_string_filter_ignored(monkeypatch) -> None:
    """An empty string in the filter list does not match all cases; it is skipped."""
    run_keys: list[str] = []

    def _run_copy(worker) -> None:
        run_keys.append(str(worker.dst_path))

    monkeypatch.setattr(Worker, 'run_copy', _run_copy)

    with pytest.raises(RuntimeError, match='No test cases matching filters'):
        run(base_dir=DEMO_DIR, test_case_filters=[''])


def test_run_filter_with_continue_on_error(monkeypatch, capsys) -> None:
    """Filtering and --continue-on-error work together; only matching cases are attempted."""
    attempted_keys: list[str] = []
    call_count = 0

    def _run_copy(worker) -> None:
        nonlocal call_count
        attempted_keys.append(str(worker.dst_path))
        call_count += 1
        if call_count == 1:
            raise RuntimeError('first filtered case failed')

    monkeypatch.setattr(Worker, 'run_copy', _run_copy)

    with pytest.raises(SystemExit) as exc_info:
        run(base_dir=DEMO_DIR, test_case_filters=['no_all', 'pre_tasks'], continue_on_error=True)

    assert exc_info.value.code == 1
    assert call_count == 2
    out = capsys.readouterr().out
    assert 'CTT Summary' in out
```

- [ ] **Step 2: Run tests to verify they fail (Task 1 must be complete first)**

```bash
uv run pytest tests/test_main.py::test_run_single_filter tests/test_main.py::test_run_multiple_filters tests/test_main.py::test_run_no_filter_runs_all tests/test_main.py::test_run_partial_substring_filter tests/test_main.py::test_run_no_matching_filter_raises tests/test_main.py::test_run_filter_error_lists_available tests/test_main.py::test_run_empty_string_filter_ignored tests/test_main.py::test_run_filter_with_continue_on_error -v
```

Expected: all 8 pass (Task 1 must be complete first).

- [ ] **Step 3: Run full test suite to check for regressions**

```bash
uv run pytest tests/test_main.py -x -q
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/test_main.py
git commit -m "test(#44): add unit tests for test_case_filters in run()"
```

---

### Task 3: Wire `--test-case` / `-t` flag into `run_cli()`

**Files:**

- Modify: `copier_template_tester/main.py:94-112`

- [ ] **Step 1: Add the argument to `ArgumentParser`**

In `run_cli()`, after the `--continue-on-error` argument (line 108), add:

```python
    cli.add_argument(
        '-t', '--test-case',
        help='Run only test cases matching this substring (can be specified multiple times)',
        action='append',
        dest='test_case_filters',
    )
```

- [ ] **Step 2: Pass `test_case_filters` through to `run()`**

Change the final `run(...)` call at the bottom of `run_cli()` from:

```python
    run(base_dir=args.base_dir, check_untracked=args.check_untracked, continue_on_error=continue_on_error)
```

to:

```python
    run(
        base_dir=args.base_dir,
        check_untracked=args.check_untracked,
        continue_on_error=continue_on_error,
        test_case_filters=args.test_case_filters,
    )
```

The complete updated `run_cli()` should look like:

```python
def run_cli() -> None:  # pragma: no cover
    """Accept CLI configuration for running ctt."""

    def dir_path(pth: str | None) -> Path:
        if pth and Path(pth).is_dir():
            return Path(pth).resolve()
        msg = f'Expected a path to a directory. Received: `{pth}`'
        raise ArgumentTypeError(msg)

    cli = ArgumentParser()
    cli.add_argument(
        '-b', '--base-dir', help='Specify the path to the directory that contains the configuration file', type=dir_path
    )
    cli.add_argument('--check-untracked', help='Only used for pre-commit', action='store_true')
    cli.add_argument('--continue-on-error', help='Run all test cases and print a summary', action='store_true')
    cli.add_argument(
        '-t',
        '--test-case',
        help='Run only test cases matching this substring (can be specified multiple times)',
        action='append',
        dest='test_case_filters',
    )

    args = cli.parse_args()
    continue_on_error = args.continue_on_error or os.environ.get('CTT_CONTINUE_ON_ERROR') == '1'
    run(
        base_dir=args.base_dir,
        check_untracked=args.check_untracked,
        continue_on_error=continue_on_error,
        test_case_filters=args.test_case_filters,
    )
```

- [ ] **Step 3: Commit**

```bash
git add copier_template_tester/main.py
git commit -m "feat(#44): wire --test-case/-t flag into run_cli()"
```

---

### Task 4: Subprocess (CLI) test for `-t` flag end-to-end

**Files:**

- Modify: `tests/test_main.py`

Since `run_cli()` is `# pragma: no cover`, only a subprocess invocation proves the flag is correctly wired. The `DEMO_DIR` has three test cases; passing `-t no_all` should output a group only for `.ctt/no_all`.

- [ ] **Step 1: Write the failing subprocess test**

Add after the `test_run_filter_with_continue_on_error` test:

```python
def test_cli_test_case_filter_single(shell: Subprocess) -> None:
    """The -t flag passed via CLI runs only the matching test case."""
    ret = run_ctt(shell, cwd=DEMO_DIR, args=['-t', 'no_all'])

    assert ret.returncode == 0, ret.stderr
    ret.stdout.matcher.fnmatch_lines(
        [
            '--- Test: .ctt/no_all ---',
            'Using `copier` to create: .ctt/no_all',
        ]
    )
    assert '.ctt/pre_tasks' not in ret.stdout.str()
    assert '.ctt/skip_tasks' not in ret.stdout.str()


def test_cli_test_case_filter_no_match(shell: Subprocess) -> None:
    """The -t flag with no matching case exits non-zero with an error message."""
    ret = run_ctt(shell, cwd=DEMO_DIR, args=['-t', 'nonexistent_filter'])

    assert ret.returncode != 0
    combined = ret.stdout.str() + ret.stderr.str()
    assert 'No test cases matching filters' in combined
```

- [ ] **Step 2: Run subprocess tests**

```bash
uv run pytest tests/test_main.py::test_cli_test_case_filter_single tests/test_main.py::test_cli_test_case_filter_no_match -v
```

Expected: both pass. If `test_cli_test_case_filter_no_match` fails because the error goes to stderr only, adjust the assertion to check `ret.stderr.str()`.

- [ ] **Step 3: Run full test suite**

```bash
uv run pytest tests/ -x -q
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/test_main.py
git commit -m "test(#44): add subprocess tests for -t/--test-case CLI flag"
```
