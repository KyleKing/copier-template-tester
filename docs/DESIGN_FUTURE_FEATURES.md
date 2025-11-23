"""Design document: Regression Testing & JJ-VCS Support for CTT.

## 1. REGRESSION TESTING WITH CHECKPOINTING

### Use Case
Test template updates across versions (e.g., v1.0 → v2.0) to ensure:
- Migrations work correctly
- Files are updated/added/removed as expected
- No data loss during template updates
- Breaking changes are detected

### Design Approach

#### Option A: Git-based Checkpointing (Simpler)
Store template outputs at specific git tags for comparison.

Pros:
- Leverages existing git infrastructure
- Simple to implement
- Easy to understand

Cons:
- Requires git repository
- Limited to what's committed
- Can't easily test partial states

#### Option B: Snapshot-based Checkpointing (More Flexible)
Store serialized snapshots of template states.

Pros:
- VCS-agnostic
- Can test intermediate states
- Granular control

Cons:
- More complex implementation
- Storage overhead
- Requires careful state management

#### Recommended: Hybrid Approach

```toml
# ctt.toml
[regression]
enabled = true
checkpoint_strategy = "git-tags"  # or "snapshots"

[[regression.update_tests]]
name = "test-upgrade-major-version"
from_version = "v1.5.0"
to_version = "v2.0.0"
expect_changes = [
    "pyproject.toml",
    ".github/workflows/*",
]
expect_migrations = [
    "Rename old_config.yml to new_config.yaml",
    "Add new dependency: ruff",
]
```

### Implementation Phases

**Phase 1: Basic Update Testing**
1. Add `update` mode to CTT (currently only supports `copy`)
2. Test that `copier update` runs without errors
3. Verify expected files exist after update

**Phase 2: Checkpoint System**
1. Create checkpoint snapshots at git tags
2. Store file hashes and metadata
3. Compare before/after states

**Phase 3: Migration Validation**
1. Define expected changes per version transition
2. Validate actual changes match expectations
3. Report differences

### Key Challenges

1. **State Explosion**: Many versions × many configurations = combinatorial explosion
   - Solution: Test only critical upgrade paths (e.g., N → N+1, N → latest)

2. **Non-deterministic Templates**: Templates with timestamps, UUIDs, etc.
   - Solution: Extend stabilization logic from _answers_stabilizer.py

3. **Conflict Resolution**: What if update creates conflicts?
   - Solution: Test both automatic resolution and manual conflict scenarios

4. **Performance**: Running multiple copier updates can be slow
   - Solution: Parallel test execution, caching

### Minimum Viable Product (MVP)

```python
# copier_template_tester/regression.py
def test_template_update(
    *,
    template_path: Path,
    from_version: str,
    to_version: str,
    output_dir: Path,
) -> UpdateResult:
    \"\"\"Test template update from one version to another.\"\"\"
    # 1. Generate template at from_version
    # 2. Update to to_version
    # 3. Verify no errors
    # 4. Compare against expected changes
    ...
```

---

## 2. JJ-VCS (JUJUTSU) SUPPORT

### Current Git Dependencies

CTT currently uses git in two places:

1. **_git_utils.py**: `resolve_git_root_dir()`
   ```python
   cmd = 'git rev-parse --show-toplevel'
   ```

2. **_pre_commit_support.py**: `check_for_untracked()`
   ```python
   cmd = 'git status --porcelain'
   ```

3. **_write_output.py**: Removes `.git` directory created by copier

### JJ-VCS Compatibility

Jujutsu (jj) is Git-compatible but uses different commands:
- `git rev-parse --show-toplevel` → `jj workspace root`
- `git status --porcelain` → `jj status`

### Design Approach: VCS Abstraction Layer

```python
# copier_template_tester/_vcs_utils.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

class VCS(Protocol):
    \"\"\"Version control system abstraction.\"\"\"

    @abstractmethod
    def get_root_dir(self, cwd: Path) -> Path:
        \"\"\"Get repository root directory.\"\"\"
        ...

    @abstractmethod
    def get_untracked_files(self, cwd: Path) -> list[Path]:
        \"\"\"Get list of untracked files.\"\"\"
        ...


class GitVCS:
    \"\"\"Git version control implementation.\"\"\"

    def get_root_dir(self, cwd: Path) -> Path:
        cmd = 'git rev-parse --show-toplevel'
        return Path(capture_shell(cmd=cmd, cwd=cwd).strip())

    def get_untracked_files(self, cwd: Path) -> list[Path]:
        cmd = 'git status --porcelain'
        output = capture_shell(cmd=cmd, cwd=cwd)
        # Parse git status output
        ...


class JujutsuVCS:
    \"\"\"Jujutsu version control implementation.\"\"\"

    def get_root_dir(self, cwd: Path) -> Path:
        cmd = 'jj workspace root'
        return Path(capture_shell(cmd=cmd, cwd=cwd).strip())

    def get_untracked_files(self, cwd: Path) -> list[Path]:
        cmd = 'jj status'
        output = capture_shell(cmd=cmd, cwd=cwd)
        # Parse jj status output
        ...


def detect_vcs(cwd: Path) -> VCS:
    \"\"\"Auto-detect which VCS is in use.\"\"\"
    # Check for .jj directory (jj workspace)
    if (cwd / '.jj').exists():
        return JujutsuVCS()
    # Check for .git directory (git repo)
    if (cwd / '.git').exists():
        return GitVCS()
    # Try running commands
    try:
        capture_shell('jj workspace root', cwd=cwd)
        return JujutsuVCS()
    except RuntimeError:
        pass
    try:
        capture_shell('git rev-parse --show-toplevel', cwd=cwd)
        return GitVCS()
    except RuntimeError:
        pass
    raise RuntimeError('No VCS detected (tried: git, jj)')
```

### Migration Path

**Phase 1: Abstraction Layer**
1. Create `_vcs_utils.py` with VCS abstraction
2. Implement `GitVCS` with current logic
3. Update `_git_utils.py` to use abstraction

**Phase 2: JJ Support**
1. Implement `JujutsuVCS`
2. Add auto-detection logic
3. Test with jj repositories

**Phase 3: Configuration**
```toml
# ctt.toml
[vcs]
type = "auto"  # or "git", "jj", "none"
```

### JJ-Specific Considerations

1. **Working Copy Model**: JJ has different working copy semantics
   - Git: Single working copy per repo
   - JJ: Multiple working copies (workspaces)
   - Impact: May need to specify which workspace to use

2. **Change Model**: JJ uses changes instead of commits
   - Need to adapt "untracked files" logic
   - JJ's `jj status` output format differs

3. **Compatibility**: JJ can coexist with Git
   - Could support both simultaneously
   - Let user choose which to use for CTT operations

### Testing Strategy

```python
# tests/test_vcs_utils.py
@pytest.mark.parametrize('vcs_type', ['git', 'jj'])
def test_vcs_abstraction(vcs_type: str, tmp_path: Path):
    \"\"\"Test VCS abstraction works for both git and jj.\"\"\"
    if vcs_type == 'git':
        subprocess.run(['git', 'init'], cwd=tmp_path)
        vcs = GitVCS()
    else:
        subprocess.run(['jj', 'init', '--git'], cwd=tmp_path)
        vcs = JujutsuVCS()

    root = vcs.get_root_dir(tmp_path)
    assert root == tmp_path

    # Create untracked file
    (tmp_path / 'test.txt').write_text('test')
    untracked = vcs.get_untracked_files(tmp_path)
    assert Path('test.txt') in untracked
```

---

## 3. IMPLEMENTATION PRIORITY

### Immediate (Current PRs)
- ✅ Complete current refactoring and improvements

### Short-term (Next 1-2 months)
1. **VCS Abstraction** (Lower risk, high value)
   - Implement abstraction layer
   - Maintain Git support
   - Add JJ detection
   - Est: 1-2 weeks

### Medium-term (Next 3-6 months)
2. **Basic JJ Support** (Once abstraction is stable)
   - Implement JujutsuVCS class
   - Test with real jj repositories
   - Document JJ-specific behavior
   - Est: 2-3 weeks

### Long-term (6+ months)
3. **Regression Testing** (High complexity, significant scope)
   - Design checkpoint system
   - Implement basic update testing
   - Add migration validation
   - Est: 1-2 months

---

## 4. RECOMMENDATION

**Start with VCS abstraction:**
- Lower risk than regression testing
- Immediate value for JJ users
- Lays groundwork for future features
- Doesn't complicate existing functionality

**Defer regression testing until:**
- VCS abstraction is proven stable
- Clear user demand emerges
- Design is validated through prototyping
- Edge cases are well-understood

**Incremental approach:**
1. VCS abstraction layer (backward compatible)
2. JJ support (opt-in)
3. Basic update testing (simple cases)
4. Full regression testing (after validation)

This avoids scope creep while providing concrete value at each step.
"""
