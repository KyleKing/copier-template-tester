# Test Case Filter Implementation Plan (#44)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `-t` / `--test-case` CLI flag that filters which CTT test cases run, plus a `--list` flag that prints the matching test-case keys without running copier. Resolves [#44](https://github.com/KyleKing/copier-template-tester/issues/44).

**Supersedes:** `docs/superpowers/specs/2026-05-06-test-case-filter-design.md` and `docs/superpowers/plans/2026-05-24-test-case-filter.md` (both deleted in favor of this single plan).

## Decisions

- Matching is a case-sensitive substring test (`filter in key`) against the full config key (e.g. `.ctt/no_all`). The issue only asked for exact match, but substring is a strict superset in the spirit of pytest `-k`, and config keys are conventionally lowercase directory names so case-sensitivity is correct
- The flag is repeatable (`action='append'`); a test case runs if any filter matches
- Empty-string filters are skipped rather than matching everything
- When no test case matches, raise `RuntimeError` listing both the provided filters and the available keys. This exits 1 with a traceback, consistent with how a missing `[output]` section already fails (`_validate_config`)
- `--list` prints the test-case keys (respecting `-t` if also given) and exits without reading the copier template or running copier. A non-matching `-t` combined with `--list` raises the same no-match error so the available keys are always surfaced
- Fully backward compatible: no flag means all test cases run exactly as before

## Architecture

All changes live in `copier_template_tester/main.py` and `tests/test_main.py`, plus a usage note in `docs/README.md`.

- A new `_filter_test_cases(output, test_case_filters)` helper returns the matching subset of `config['output']` or raises on no match
- `run()` gains a `test_case_filters: list[str] | None = None` keyword and applies the helper between `load_config()` and the copier loop. Filtering happens before `_isolated_source()`, so filtered-out cases cost nothing
- A new `list_test_cases()` function loads the config, applies the same helper, and prints each key via `logger.text`
- `run_cli()` wires both flags; `--list` short-circuits before `run()`

`load_config()` is not cached, so reassigning the local `output` mapping has no cross-call effects. `--check-untracked` and `--continue-on-error` interact with the filter only in that they operate on the filtered subset.

______________________________________________________________________

### Task 1: Filter logic in `run()` with unit tests

**Files:**

- Modify: `copier_template_tester/main.py`

- Modify: `tests/test_main.py`

- [ ] **Step 1: Add the `_filter_test_cases` helper**

Insert after `_resolve_post_tasks` in `main.py`:

```python
def _filter_test_cases(output: dict[str, Any], test_case_filters: list[str]) -> dict[str, Any]:
    """Return the subset of output whose keys contain any non-empty filter substring."""
    active_filters = [tcf for tcf in test_case_filters if tcf]
    matched = {key: data for key, data in output.items() if any(tcf in key for tcf in active_filters)}
    if not matched:
        msg = f'No test cases matching filters: {test_case_filters}. Available test cases: {[*output]}'
        raise RuntimeError(msg)
    return matched
```

- [ ] **Step 2: Thread `test_case_filters` through `run()`**

Change the signature:

```python
def run(
    *,
    base_dir: Path | None = None,
    check_untracked: bool = False,
    continue_on_error: bool = False,
    test_case_filters: list[str] | None = None,
) -> None:
```

After `defaults = config.get('defaults', {})`, replace direct use of `config['output']` with a filtered local:

```python
    output = config['output']
    if test_case_filters:
        output = _filter_test_cases(output, test_case_filters)
```

and change the loop to `for key, data in output.items():`.

- [ ] **Step 3: Add unit tests to `tests/test_main.py`**

All use the existing `monkeypatch` pattern that stubs `Worker.run_copy` (see `test_main_with_copier_mock`) against `DEMO_DIR`, whose `ctt.toml` defines `.ctt/no_all`, `.ctt/pre_tasks`, and `.ctt/skip_tasks`. Capture `str(worker.dst_path)` in the stub to observe which cases ran.

1. Single filter `['no_all']` runs exactly one case
1. Multiple filters `['no_all', 'pre_tasks']` run both matching cases
1. Partial substring `['tasks']` matches both `pre_tasks` and `skip_tasks`
1. No filter (omitted) still runs all `EXPECTED_COPY_CALLS` cases
1. Non-matching filter raises `RuntimeError` matching `'No test cases matching filters'` and the message includes `Available test cases: [`
1. `['']` is skipped, yielding the same no-match `RuntimeError` (not match-all)
1. Filters combine with `continue_on_error=True`: with `['no_all', 'pre_tasks']` and the first copy raising, expect `SystemExit` code 1, two attempts, and `CTT Summary` in captured stdout (mirror `test_run_continue_on_error_collects_failures`)

- [ ] **Step 4: Verify**

```bash
uv run pytest tests/test_main.py -x -q
```

Expected: all tests pass, including the seven new ones.

- [ ] **Step 5: Commit**

```
feat(#44): filter test cases in run() via test_case_filters
```

______________________________________________________________________

### Task 2: Wire `-t` / `--test-case` into the CLI with subprocess tests and docs

**Files:**

- Modify: `copier_template_tester/main.py` (`run_cli`)

- Modify: `tests/test_main.py`

- Modify: `docs/README.md`

- [ ] **Step 1: Add the argument in `run_cli()`**

After the `--continue-on-error` argument:

```python
    cli.add_argument(
        '-t',
        '--test-case',
        action='append',
        dest='test_case_filters',
        help='Run only test cases whose key contains this substring (repeatable)',
    )
```

and pass it through:

```python
    run(
        base_dir=args.base_dir,
        check_untracked=args.check_untracked,
        continue_on_error=continue_on_error,
        test_case_filters=args.test_case_filters,
    )
```

- [ ] **Step 2: Add subprocess tests**

`run_cli()` is `# pragma: no cover`, so only a subprocess invocation proves the wiring. Use the existing `run_ctt(shell, cwd=DEMO_DIR, args=[...])` helper:

1. `args=['-t', 'no_all']`: returncode 0, stdout fnmatch includes `--- Test: .ctt/no_all ---` and `Using \`copier\` to create: .ctt/no_all`; `.ctt/pre_tasks`and`.ctt/skip_tasks\` absent from stdout
1. `args=['-t', 'nonexistent_filter']`: returncode != 0 and `'No test cases matching filters'` in stdout+stderr combined

- [ ] **Step 3: Document the flag in `docs/README.md`**

In the `pipx` section (or a new `### CLI Flags` subsection beside it), show:

```sh
# Run only test cases whose key contains a substring (repeatable)
ctt -t no_all
ctt --test-case no_all --test-case pre_tasks
```

- [ ] **Step 4: Verify**

```bash
uv run pytest tests/ -x -q
```

- [ ] **Step 5: Commit**

```
feat(#44): add -t/--test-case CLI flag
```

______________________________________________________________________

### Task 3: `--list` flag

**Files:**

- Modify: `copier_template_tester/main.py`

- Modify: `tests/test_main.py`

- Modify: `docs/README.md`

- [ ] **Step 1: Add `list_test_cases()`**

Insert after `run()`:

```python
def list_test_cases(*, base_dir: Path | None = None, test_case_filters: list[str] | None = None) -> None:
    """Print the test-case keys from ctt.toml, optionally filtered."""
    base_dir = base_dir or Path.cwd()
    output = load_config(base_dir)['output']
    if test_case_filters:
        output = _filter_test_cases(output, test_case_filters)
    for key in output:
        logger.text(key)
```

Intentionally no `read_copier_template` check: listing only needs `ctt.toml`.

- [ ] **Step 2: Wire `--list` in `run_cli()`**

Insert the argument alphabetically (after `--continue-on-error`, before `-t/--test-case`):

```python
    cli.add_argument(
        '--list',
        action='store_true',
        dest='list_test_cases',
        help='List matching test case keys and exit without running copier',
    )
```

Short-circuit before calling `run()`:

```python
    if args.list_test_cases:
        list_test_cases(base_dir=args.base_dir, test_case_filters=args.test_case_filters)
        return
```

- [ ] **Step 3: Add tests**

Unit tests (direct calls with `capsys`):

1. `list_test_cases(base_dir=DEMO_DIR)` prints all three keys, one per line, and copier never runs (no `Worker.run_copy` stub needed since nothing should invoke it)
1. `list_test_cases(base_dir=DEMO_DIR, test_case_filters=['tasks'])` prints only the two `tasks` keys
1. A non-matching filter raises the shared no-match `RuntimeError`

Subprocess test:

1. `args=['--list']`: returncode 0, stdout contains all three keys, and `'Using `copier` to create'` absent

- [ ] **Step 4: Document `--list` in `docs/README.md`**

Extend the CLI flags snippet from Task 2:

```sh
# Discover available test case keys
ctt --list
ctt --list -t tasks
```

- [ ] **Step 5: Verify**

```bash
uv run pytest tests/ -x -q
pre-commit run --all-files
```

- [ ] **Step 6: Commit**

```
feat(#44): add --list flag to print test case keys
```
