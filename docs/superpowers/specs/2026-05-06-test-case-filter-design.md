# Test Case Filter Design

**Date:** 2026-05-06 **Status:** Approved **Approach:** Direct filter in `run()` function

## Overview

Add a CLI flag `--test-case` (or `-t`) that allows users to selectively run specific test cases by substring matching, similar to pytest's `-k` but with simpler substring matching.

## Requirements

1. Support filtering test cases by substring match
1. Support multiple filter values (any match runs the test)
1. Exit with error when no test cases match
1. Preserve existing behavior when no filter is specified
1. Display available test cases when no match is found

## CLI Interface

Add `--test-case` argument to `ArgumentParser` in `run_cli()`:

```python
cli.add_argument(
    '-t',
    '--test-case',
    help='Run only test cases matching this substring (can be specified multiple times)',
    action='append',
    dest='test_case_filters',
)
```

**Usage examples:**

```bash
# Single filter
ctt --test-case no_all
ctt -t no_all

# Multiple filters
ctt --test-case no_all --test-case pre_tasks
ctt -t no_all -t pre_tasks

# No filter (all test cases run)
ctt
```

## Filtering Logic

Substring matching is **case-sensitive** — config keys are directory names and are conventionally lowercase (e.g. `no_all`, `pre_tasks`), so case-sensitive `in` is the correct default.

Modify `run()` function to accept optional filter parameter:

```python
def run(
    *,
    base_dir: Path | None = None,
    check_untracked: bool = False,
    continue_on_error: bool = False,
    test_case_filters: list[str] | None = None,
) -> None:
```

**Filter implementation in test loop:**

```python
# After loading config
config = load_config(base_dir)
defaults = config.get('defaults', {})

# Filter test cases if requested
matched_test_cases = {}
if test_case_filters:
    for key, data in config['output'].items():
        if any(filter_str in key for filter_str in test_case_filters):
            matched_test_cases[key] = data

    if not matched_test_cases:
        available = list(config['output'].keys())
        raise RuntimeError(f'No test cases matching filters: {test_case_filters}. Available test cases: {available}')
    config['output'] = matched_test_cases

# Continue with existing loop using filtered config
```

## Error Handling

**No test cases match:**

- Raise `RuntimeError` with descriptive message
- Display the filters that were provided
- Display list of available test cases
- Exit with non-zero status code

**Invalid/empty filter values:**

- Empty strings in filter list are skipped
- No other validation needed — any substring is valid

**Integration with existing flags:**

- Works with `--continue-on-error`: filtered test cases run with continue-on-error behavior
- Works with `--check-untracked`: checked only after filtered test cases complete
- If no test cases match, the no-match error takes precedence over other flags

## Testing Strategy

Add tests to `tests/test_main.py`:

1. **Single filter**: Verify only matching test case runs
1. **Multiple filters**: Verify all matching test cases run
1. **No matches**: Verify error message and exit code
1. **No filter**: Verify all test cases run (backward compatibility)
1. **Partial substring match**: Verify substring matching works correctly
1. **Empty filter**: Verify empty strings are handled gracefully
1. **Integration with --continue-on-error**: Verify both flags work together
1. **CLI subprocess test**: Verify `-t` flag is wired through `run_cli()` end-to-end using `run_ctt(shell, args=['-t', 'no_all'])` — since `run_cli()` is `# pragma: no cover`, only a subprocess test confirms the flag is plumbed correctly

## Implementation Changes

### Files to modify:

1. **`copier_template_tester/main.py`**

    - Add `--test-case` argument to `run_cli()`
    - Add `test_case_filters` parameter to `run()`
    - Implement filtering logic in `run()`
    - Add no-match error handling

1. **`tests/test_main.py`**

    - Add new test functions for filter behavior
    - Use existing test fixtures and helpers

### Changes are minimal and localized:

- No changes to config loading
- No changes to test execution logic
- No changes to output reporter
- Only filtering before the existing test loop

## Backward Compatibility

- **Fully backward compatible**: When no `--test-case` flag is provided, all test cases run as before
- **No breaking changes**: Existing behavior is preserved
- **Opt-in feature**: Only affects behavior when explicitly used
