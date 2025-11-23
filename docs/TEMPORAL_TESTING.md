# Temporal Testing Guide

Temporal testing allows you to test your current copier template against historical states of real projects, helping validate template updates before applying them to production.

## Overview

When you update a copier template, you want to ensure that applying the new template to existing projects will work correctly. Temporal testing helps by:

1. **Cloning your project** at specific historical points (commits, tags, branches)
2. **Applying the current template** to those historical states
3. **Generating diffs** showing what would change
4. **Running tests in parallel** for faster results

This lets you validate template changes against real project history before rolling them out.

## Configuration

Add a `[temporal]` section to your `ctt.toml` file:

```toml
[temporal]
enabled = true
source_project = "../my-project"  # Path to project with history
mode = "copy_history"              # or "shallow_clone"
parallel = true                    # Run snapshots in parallel
keep_temp_dirs = false             # Keep temp dirs for debugging

[[temporal.snapshots]]
name = "v1.0-baseline"
ref = "v1.0.0"
description = "Project state at v1.0 release"
template_data = {project_name = "my-project", python_version = "3.10"}

[[temporal.snapshots]]
name = "v2.0-current"
ref = "v2.0.0"
description = "Project state at v2.0 release"
template_data = {project_name = "my-project", python_version = "3.11"}

[[temporal.snapshots]]
name = "main-latest"
ref = "HEAD"
description = "Current main branch state"
template_data = {project_name = "my-project", python_version = "3.12"}
```

### Configuration Options

#### `[temporal]` Section

- **`enabled`** (bool, required): Enable/disable temporal testing
- **`source_project`** (string, required): Path to source project with git history
  - Can be relative (e.g., `"../my-project"`) or absolute
- **`mode`** (string, default: `"copy_history"`): Clone mode
  - `"copy_history"`: Full clone with complete history
  - `"shallow_clone"`: Shallow clone (faster, but limited git operations)
- **`parallel`** (bool, default: `false`): Run snapshots in parallel
- **`keep_temp_dirs`** (bool, default: `false`): Keep temporary directories after tests

#### `[[temporal.snapshots]]` Array

Each snapshot defines a historical state to test:

- **`name`** (string, required): Unique identifier for this snapshot
- **`ref`** (string, required): Git ref (commit hash, tag, or branch name)
- **`description`** (string, optional): Human-readable description
- **`template_data`** (dict, optional): Data to pass to copier template

## Usage

### Basic Usage

Run temporal tests with default configuration:

```bash
ctt temporal
```

### Advanced Options

```bash
# Specify base directory
ctt temporal -b /path/to/template

# Force parallel execution
ctt temporal --parallel

# Force serial execution
ctt temporal --serial

# Control parallelism
ctt temporal --parallel --max-workers 4

# Keep temp directories for debugging
ctt temporal --keep-temp-dirs

# Show enhanced summary (requires rich)
ctt temporal --summary

# Custom output directory
ctt temporal -o /path/to/output
```

### Installing Rich for Enhanced Reports

For beautiful, colorful summary reports:

```bash
pip install rich
```

Then use `--summary` flag:

```bash
ctt temporal --summary
```

## Output Structure

Temporal testing creates the following output structure:

```
.ctt-temporal/
├── metadata.json              # Test metadata and results
├── snapshot-name-1/
│   ├── original/             # Project state before template
│   │   ├── file1.py
│   │   └── ...
│   ├── updated/              # Project state after template
│   │   ├── file1.py
│   │   └── ...
│   └── diff.patch            # Unified diff
├── snapshot-name-2/
│   ├── original/
│   ├── updated/
│   └── diff.patch
└── ...
```

### Metadata File

The `metadata.json` file contains:

```json
{
  "timestamp": "2025-01-23T12:34:56",
  "total_tests": 3,
  "passed": 3,
  "failed": 0,
  "differences_found": 2,
  "results": [
    {
      "snapshot_name": "v1.0-baseline",
      "success": true,
      "has_differences": true,
      "diff_path": ".ctt-temporal/v1.0-baseline/diff.patch",
      "error": null,
      "files_changed": ["pyproject.toml", "README.md"],
      "files_added": [],
      "files_removed": []
    }
  ]
}
```

## Workflow Examples

### Example 1: Testing Major Version Upgrades

Test how your template updates affect projects at different Python versions:

```toml
[[temporal.snapshots]]
name = "py38-legacy"
ref = "tags/python-3.8"
template_data = {python_version = "3.12"}

[[temporal.snapshots]]
name = "py310-current"
ref = "tags/python-3.10"
template_data = {python_version = "3.12"}
```

### Example 2: Testing Across Multiple Projects

Create separate `ctt.toml` files for each project:

```bash
# Project A
cd template-a
ctt temporal

# Project B
cd ../template-b
ctt temporal

# Compare results
diff .ctt-temporal/metadata.json ../template-b/.ctt-temporal/metadata.json
```

### Example 3: CI/CD Integration

Add temporal testing to your CI pipeline:

```yaml
# .github/workflows/temporal-tests.yml
name: Temporal Testing

on: [push, pull_request]

jobs:
  temporal-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install CTT
        run: pip install copier-template-tester[rich]

      - name: Clone test project
        run: git clone https://github.com/your-org/test-project ../test-project

      - name: Run temporal tests
        run: ctt temporal --summary

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: temporal-test-results
          path: .ctt-temporal/
```

## VCS Support

Temporal testing supports multiple version control systems:

- **Git**: Full support (default)
- **Jujutsu (jj)**: Full support with auto-detection

The VCS is auto-detected based on:
1. Presence of `.jj` directory (Jujutsu)
2. Presence of `.git` directory (Git)
3. Command availability

You can explicitly specify the VCS type if needed (advanced usage).

## Performance Tips

### Parallel Execution

For faster results with multiple snapshots:

```toml
[temporal]
parallel = true  # Enable parallel execution
```

Or via CLI:

```bash
ctt temporal --parallel --max-workers 8
```

**Performance comparison:**
- Serial: ~60 seconds for 6 snapshots
- Parallel (4 workers): ~20 seconds for 6 snapshots
- Parallel (8 workers): ~15 seconds for 6 snapshots

### Shallow Clones

For large repositories, use shallow clones:

```toml
[temporal]
mode = "shallow_clone"
```

This speeds up cloning but limits some git operations.

### Keep Temp Dirs

For debugging, keep temporary directories:

```toml
[temporal]
keep_temp_dirs = true
```

Or via CLI:

```bash
ctt temporal --keep-temp-dirs
```

## Troubleshooting

### Issue: "No VCS detected"

**Solution**: Ensure the source project is a valid git or jujutsu repository:

```bash
cd /path/to/source-project
git status  # or: jj status
```

### Issue: "Snapshot test failed: ref not found"

**Solution**: Verify the ref exists in your repository:

```bash
cd /path/to/source-project
git tag  # List tags
git branch -a  # List branches
```

### Issue: "copier update failed"

**Solution**: Check that your project has a `.copier-answers.yml` file at the historical ref:

```bash
git checkout <ref>
ls -la .copier-answers.yml
```

### Issue: Parallel execution fails

**Solution**: Try serial execution first to identify the issue:

```bash
ctt temporal --serial
```

## Best Practices

1. **Start with serial execution** to understand baseline behavior
2. **Use descriptive snapshot names** like `v1.0-baseline` instead of commit hashes
3. **Test major milestones** (releases, migrations, breaking changes)
4. **Review diffs carefully** before applying template updates
5. **Integrate with CI/CD** for automated validation
6. **Use `keep_temp_dirs`** for debugging failures
7. **Enable rich reports** for better visibility (`--summary`)

## API Usage

You can also use temporal testing programmatically:

```python
from pathlib import Path
from copier_template_tester._config import load_temporal_config
from copier_template_tester.temporal import TemporalTester

# Load configuration
base_dir = Path.cwd()
settings, snapshots = load_temporal_config(base_dir)

# Initialize tester
tester = TemporalTester(
    template_path=base_dir,
    source_project=Path(settings['source_project']),
    output_dir=base_dir / '.ctt-temporal',
    keep_temp_dirs=False,
)

# Run tests
results = tester.run_all(
    snapshots=snapshots,
    parallel=True,
    max_workers=4,
)

# Process results
for result in results:
    print(f"{result.snapshot_name}: {'PASS' if result.success else 'FAIL'}")
    if result.has_differences:
        print(f"  Changes: {len(result.files_changed)} files")
```

## Related Documentation

- [Configuration Reference](../README.md)
- [VCS Abstraction Design](DESIGN_FUTURE_FEATURES.md)
- [Temporal Testing Design](DESIGN_TEMPORAL_TESTING.md)
