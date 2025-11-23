"""Design: Temporal Testing - Test Current Templates Against Historical Project States.

## CONCEPT: TEMPORAL TESTING

### What is Temporal Testing?
Test the **current** version of your copier template against **historical** states of real projects.

**Different from regression testing:**
- Regression: Test old template → new template (template evolution)
- Temporal: Test current template → old project states (project evolution)

### Use Cases

1. **Template Update Validation**
   - "What would happen if I updated my 2-year-old project with today's template?"
   - Identify breaking changes before applying to real projects

2. **Migration Testing**
   - Test template changes against known project states
   - Validate that template updates work on legacy code

3. **Integration Testing**
   - Test template with real project history, not just synthetic examples
   - Catch real-world edge cases

4. **Before/After Comparison**
   - See exactly what files would change
   - Manual review of diffs before committing

---

## DESIGN: ISOLATED TEMPORAL TESTING

### Architecture

```
copier-template-tester/
├── .ctt/                          # Normal CTT output
│   ├── defaults/
│   └── no_all/
├── .ctt-temporal/                 # NEW: Temporal testing output
│   ├── v1.0-baseline/
│   │   ├── original/              # Project at commit abc123
│   │   ├── updated/               # After applying current template
│   │   └── diff.patch             # Differences
│   ├── v2.0-after-migration/
│   │   ├── original/
│   │   ├── updated/
│   │   └── diff.patch
│   └── metadata.json              # Test run metadata
└── /tmp/ctt-temporal-<uuid>/      # Isolated git directories (auto-cleaned)
    ├── snapshot-v1.0-baseline/
    └── snapshot-v2.0-after-migration/
```

### Configuration

```toml
# ctt.toml
[temporal]
enabled = true
mode = "copy_history"  # or "fresh_project", "shallow_clone"
source_project = "../my-real-project"  # Path to real project
parallel = true  # Run tests in parallel
keep_temp_dirs = false  # Auto-clean temp directories

# Define historical snapshots to test
[[temporal.snapshots]]
name = "v1.0-baseline"
ref = "v1.0.0"  # Git ref: commit hash, tag, or branch
description = "Project state at v1.0 release"
template_data = {project_name = "my-project", python_version = "3.10"}

[[temporal.snapshots]]
name = "v2.0-after-migration"
ref = "abc123def"
description = "After major refactoring"
template_data = {project_name = "my-project", python_version = "3.11"}

[[temporal.snapshots]]
name = "current-main"
ref = "HEAD"
description = "Current main branch"
template_data = {project_name = "my-project", python_version = "3.12"}
```

---

## IMPLEMENTATION

### Core Workflow

```python
# copier_template_tester/temporal.py

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor

@dataclass
class TemporalSnapshot:
    \"\"\"Configuration for a temporal test snapshot.\"\"\"
    name: str
    ref: str  # Git ref (commit, tag, branch)
    description: str
    template_data: dict[str, Any]

@dataclass
class TemporalTestResult:
    \"\"\"Result of temporal testing.\"\"\"
    snapshot_name: str
    success: bool
    has_differences: bool
    diff_path: Path | None
    error: str | None
    files_changed: list[str]
    files_added: list[str]
    files_removed: list[str]


class TemporalTester:
    \"\"\"Execute temporal tests in isolated environments.\"\"\"

    def __init__(
        self,
        template_path: Path,
        source_project: Path,
        output_dir: Path,
    ):
        self.template_path = template_path
        self.source_project = source_project
        self.output_dir = output_dir
        self.temp_base = Path(tempfile.gettempdir()) / 'ctt-temporal'

    def run_snapshot(self, snapshot: TemporalSnapshot) -> TemporalTestResult:
        \"\"\"Test a single temporal snapshot in isolation.\"\"\"

        # 1. Create isolated temporary directory
        temp_dir = self.temp_base / f'snapshot-{snapshot.name}'
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 2. Clone/copy project history
            project_dir = self._prepare_project(temp_dir, snapshot.ref)

            # 3. Capture original state
            original_dir = self.output_dir / snapshot.name / 'original'
            self._snapshot_state(project_dir, original_dir)

            # 4. Apply current template
            self._apply_template(project_dir, snapshot.template_data)

            # 5. Capture updated state
            updated_dir = self.output_dir / snapshot.name / 'updated'
            self._snapshot_state(project_dir, updated_dir)

            # 6. Generate diff
            diff_result = self._generate_diff(
                original_dir,
                updated_dir,
                self.output_dir / snapshot.name / 'diff.patch',
            )

            return TemporalTestResult(
                snapshot_name=snapshot.name,
                success=True,
                has_differences=diff_result.has_changes,
                diff_path=diff_result.patch_file,
                error=None,
                files_changed=diff_result.changed,
                files_added=diff_result.added,
                files_removed=diff_result.removed,
            )

        except Exception as e:
            return TemporalTestResult(
                snapshot_name=snapshot.name,
                success=False,
                has_differences=False,
                diff_path=None,
                error=str(e),
                files_changed=[],
                files_added=[],
                files_removed=[],
            )

        finally:
            # 7. Cleanup temp directory (unless keep_temp_dirs=true)
            if not self.keep_temp_dirs:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _prepare_project(self, temp_dir: Path, ref: str) -> Path:
        \"\"\"Clone project and checkout specific ref.\"\"\"
        project_dir = temp_dir / 'project'

        # Clone with full history
        subprocess.run(
            ['git', 'clone', str(self.source_project), str(project_dir)],
            check=True,
        )

        # Checkout specific ref
        subprocess.run(
            ['git', 'checkout', ref],
            cwd=project_dir,
            check=True,
        )

        return project_dir

    def _snapshot_state(self, source: Path, destination: Path) -> None:
        \"\"\"Capture current project state (excluding .git).\"\"\"
        destination.mkdir(parents=True, exist_ok=True)

        # Copy all files except .git
        for item in source.iterdir():
            if item.name == '.git':
                continue
            if item.is_dir():
                shutil.copytree(item, destination / item.name)
            else:
                shutil.copy2(item, destination / item.name)

    def _apply_template(self, project_dir: Path, template_data: dict) -> None:
        \"\"\"Apply copier template to project.\"\"\"
        # Use copier's update mode
        subprocess.run(
            [
                'copier',
                'update',
                '--answers-file', project_dir / '.copier-answers.yml',
                '--data', str(template_data),
            ],
            cwd=project_dir,
            check=True,
        )

    def _generate_diff(
        self,
        original: Path,
        updated: Path,
        output_file: Path,
    ) -> DiffResult:
        \"\"\"Generate unified diff between original and updated.\"\"\"
        # Use git diff for nice formatting
        subprocess.run(
            ['git', 'diff', '--no-index', str(original), str(updated)],
            stdout=output_file.open('w'),
            # Note: git diff returns 1 if differences found (not an error)
        )

        # Parse diff to extract changed files
        return self._parse_diff(output_file)

    def run_all(
        self,
        snapshots: list[TemporalSnapshot],
        parallel: bool = True,
    ) -> list[TemporalTestResult]:
        \"\"\"Run all temporal tests.\"\"\"
        if parallel:
            with ProcessPoolExecutor() as executor:
                results = list(executor.map(self.run_snapshot, snapshots))
        else:
            results = [self.run_snapshot(s) for s in snapshots]

        return results
```

---

## MODES OF OPERATION

### Mode 1: Copy History (Default)
**Best for:** Real integration testing with full git history

```toml
[temporal]
mode = "copy_history"
source_project = "../my-real-project"
```

**Pros:**
- Tests with real project history
- Can checkout any commit/tag/branch
- Most realistic testing

**Cons:**
- Slower (full clone)
- Requires existing project

### Mode 2: Shallow Clone
**Best for:** Faster testing when full history not needed

```toml
[temporal]
mode = "shallow_clone"
source_project = "../my-real-project"
depth = 1  # Only fetch specified commit
```

**Pros:**
- Faster than full clone
- Less disk space

**Cons:**
- Can't navigate history
- Must know exact commits

### Mode 3: Fresh Project
**Best for:** Testing template from scratch at different config points

```toml
[temporal]
mode = "fresh_project"
# No source_project needed
```

**Pros:**
- No existing project required
- Fast
- Tests template in isolation

**Cons:**
- No real project history
- Less realistic

---

## PARALLEL EXECUTION

### Isolation Strategy

Each snapshot runs in **completely isolated** temporary directory:

```
/tmp/ctt-temporal-<session-uuid>/
├── snapshot-v1.0-baseline/
│   ├── project/              # Cloned project at v1.0
│   └── .git/                 # Full git history
├── snapshot-v2.0/
│   ├── project/
│   └── .git/
└── snapshot-current/
    ├── project/
    └── .git/
```

**Benefits:**
1. No interference between tests
2. Safe parallel execution
3. Can manipulate git state freely
4. Auto-cleanup after tests

### Parallelization

```python
# Run all snapshots in parallel
with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(run_snapshot, snapshot)
        for snapshot in snapshots
    ]
    results = [f.result() for f in futures]
```

---

## OUTPUT & REPORTING

### Directory Structure

```
.ctt-temporal/
├── metadata.json                   # Test run metadata
├── v1.0-baseline/
│   ├── original/                   # Project before template
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   └── tests/
│   ├── updated/                    # Project after template
│   │   ├── pyproject.toml         # (potentially modified)
│   │   ├── src/
│   │   └── tests/
│   └── diff.patch                  # Unified diff
├── v2.0-after-migration/
│   ├── original/
│   ├── updated/
│   └── diff.patch
└── summary.md                      # Human-readable summary
```

### Metadata

```json
// .ctt-temporal/metadata.json
{
  "run_timestamp": "2025-01-23T10:30:00Z",
  "template_path": "/path/to/template",
  "source_project": "/path/to/project",
  "snapshots": [
    {
      "name": "v1.0-baseline",
      "ref": "v1.0.0",
      "success": true,
      "has_differences": true,
      "files_changed": 5,
      "files_added": 2,
      "files_removed": 1
    }
  ]
}
```

### Summary Report

```markdown
# Temporal Test Summary

Run Date: 2025-01-23 10:30:00

## Snapshots Tested: 3

### ✅ v1.0-baseline (v1.0.0)
- **Status**: Success
- **Differences**: Yes
- **Files Changed**: 5
  - pyproject.toml
  - .github/workflows/ci.yml
  - README.md
  - src/config.py
  - tests/test_config.py
- **Files Added**: 2
  - .pre-commit-config.yaml
  - .ruff.toml
- **Files Removed**: 1
  - setup.py
- **Review**: See `.ctt-temporal/v1.0-baseline/diff.patch`

### ✅ v2.0-after-migration (abc123def)
- **Status**: Success
- **Differences**: No
- **Note**: Template already up-to-date

### ❌ current-main (HEAD)
- **Status**: Failed
- **Error**: Merge conflict in pyproject.toml
```

---

## CLI INTEGRATION

### New Command

```bash
# Run temporal tests
ctt temporal

# Run specific snapshot
ctt temporal --snapshot v1.0-baseline

# Parallel execution
ctt temporal --parallel --workers 4

# Keep temp directories for debugging
ctt temporal --keep-temp

# Custom config file
ctt temporal --config ctt-temporal.toml
```

### Integration with Existing CTT

```bash
# Run both standard and temporal tests
ctt --all

# Run only standard tests
ctt

# Run only temporal tests
ctt --temporal-only
```

---

## CONFLICT HANDLING

### Automatic Conflict Detection

```python
def _apply_template(self, project_dir: Path, template_data: dict) -> ApplyResult:
    \"\"\"Apply template and detect conflicts.\"\"\"
    try:
        result = subprocess.run(
            ['copier', 'update', ...],
            capture_output=True,
        )

        if 'CONFLICT' in result.stderr.decode():
            return ApplyResult(
                success=False,
                has_conflicts=True,
                conflict_files=self._parse_conflicts(result.stderr),
            )

        return ApplyResult(success=True, has_conflicts=False)

    except subprocess.CalledProcessError as e:
        # Handle copier errors
        ...
```

### Conflict Resolution Strategies

```toml
[[temporal.snapshots]]
name = "v1.0-baseline"
ref = "v1.0.0"
conflict_strategy = "abort"  # or "theirs", "ours", "manual"
```

Options:
- `abort`: Stop on conflict (default)
- `theirs`: Accept template changes
- `ours`: Keep project changes
- `manual`: Save conflict markers for review

---

## ADVANCED FEATURES

### Pre/Post Hooks

```toml
[[temporal.snapshots]]
name = "v1.0-baseline"
ref = "v1.0.0"
pre_apply_hook = "pip install -r requirements.txt"
post_apply_hook = "pytest tests/"
```

### Selective File Testing

```toml
[[temporal.snapshots]]
name = "v1.0-baseline"
ref = "v1.0.0"
include_patterns = ["*.py", "*.toml", ".github/**"]
exclude_patterns = ["tests/**", "docs/**"]
```

### Environment Variables

```toml
[[temporal.snapshots]]
name = "v1.0-baseline"
ref = "v1.0.0"
env = {PYTHONPATH = "src", DEBUG = "true"}
```

---

## IMPLEMENTATION PHASES

### Phase 1: Basic Temporal Testing (MVP)
- Create isolated temp directories
- Clone project at specific ref
- Apply template
- Capture before/after snapshots
- Generate diff
- Serial execution only

### Phase 2: Parallel Execution
- Process pool for parallel tests
- Proper isolation
- Progress reporting

### Phase 3: Conflict Handling
- Detect merge conflicts
- Resolution strategies
- Conflict reporting

### Phase 4: Advanced Features
- Pre/post hooks
- Selective file testing
- Custom environments
- VCS abstraction (git/jj support)

---

## EXAMPLE WORKFLOW

### 1. Configure Temporal Tests

```toml
# ctt.toml
[temporal]
enabled = true
mode = "copy_history"
source_project = "../my-django-project"
parallel = true

[[temporal.snapshots]]
name = "before-django4-upgrade"
ref = "v3.2-stable"
description = "Test template with Django 3.2"
template_data = {project_name = "myapp", django_version = "4.2"}

[[temporal.snapshots]]
name = "current-main"
ref = "HEAD"
description = "Test template with current main"
template_data = {project_name = "myapp", django_version = "5.0"}
```

### 2. Run Tests

```bash
$ ctt temporal

Creating temporal snapshots...
✓ before-django4-upgrade: Cloned at v3.2-stable
✓ current-main: Cloned at HEAD

Running temporal tests in parallel (2 workers)...
✓ before-django4-upgrade: Applied template (5 files changed)
✓ current-main: Applied template (0 files changed)

Results saved to .ctt-temporal/
```

### 3. Review Results

```bash
$ tree .ctt-temporal/
.ctt-temporal/
├── before-django4-upgrade/
│   ├── original/
│   ├── updated/
│   └── diff.patch
├── current-main/
│   ├── original/
│   ├── updated/
│   └── diff.patch  (empty - no changes)
├── metadata.json
└── summary.md

$ cat .ctt-temporal/before-django4-upgrade/diff.patch
# Review what would change...
```

### 4. Apply Changes (Manual)

If satisfied with temporal test results, apply to real project:

```bash
cd ../my-django-project
git checkout v3.2-stable
copier update --answers-file .copier-answers.yml
```

---

## BENEFITS

1. **Risk Mitigation**: See changes before applying to production
2. **Integration Testing**: Test with real project history
3. **Parallel Efficiency**: Test multiple states simultaneously
4. **Isolation**: No risk to source project
5. **Manual Review**: Diff patches for careful inspection
6. **Automation**: CI/CD integration for continuous validation

---

## RECOMMENDATION

**Implement in phases:**

1. **Phase 1 (MVP)**: Basic serial temporal testing
   - Proves concept
   - Delivers immediate value
   - ~1-2 weeks

2. **Phase 2**: Parallel execution
   - Performance improvement
   - ~1 week

3. **Phase 3**: Conflict handling
   - Production-ready
   - ~1-2 weeks

**Total estimate: 3-5 weeks for full implementation**

This feature complements (not replaces) the VCS abstraction and regression testing designs.
"""
