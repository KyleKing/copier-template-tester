# Developer Notes

## Local Development

```sh
git clone https://github.com/kyleking/copier-template-tester.git
cd copier-template-tester
uv sync --all-extras

# See the available tasks
uv run calcipy
# Or use a local 'run' file (so that 'calcipy' can be extended)
./run

# Run the default task list (lint, auto-format, test coverage, etc.)
./run main

# Make code changes and run specific tasks as needed:
./run lint.fix test
```

### Maintenance

Dependency upgrades can be accomplished with:

```sh
uv lock --upgrade
uv sync --all-extras
```

## Publishing

Publishing is automated via GitHub Actions using PyPI Trusted Publishing. Tag creation triggers automated publishing.

```sh
./run release              # Bumps version, creates tag, pushes → triggers publish
./run release --suffix=rc  # For pre-releases
```

### Initial Setup

One-time setup to enable PyPI Trusted Publishing:

**Configure GitHub Environments**

Repository Settings → Environments:
- Create `testpypi` environment (no protection rules)
- Create `pypi` environment with "Required reviewers" enabled

**Register Trusted Publishers**

PyPI: https://pypi.org/manage/project/copier_template_tester/settings/publishing/
- Owner: `kyleking`
- Repository: `copier_template_tester`
- Workflow: `publish.yml`
- Environment: `pypi`
    - Or environment `testpypi` (for [TestPyPI](https://test.pypi.org/manage/account/publishing))

### Manual Publishing

For emergency manual publish:

```sh
export UV_PUBLISH_TOKEN=pypi-...
uv build
uv publish
```

## Current Status

<!-- {cts} COVERAGE -->
| File                                                  | Statements | Missing | Excluded | Coverage |
|-------------------------------------------------------|-----------:|--------:|---------:|---------:|
| `copier_template_tester/__init__.py`                  | 4          | 0       | 0        | 100.0%   |
| `copier_template_tester/_config.py`                   | 15         | 0       | 3        | 100.0%   |
| `copier_template_tester/_pre_commit_support.py`       | 13         | 0       | 0        | 93.3%    |
| `copier_template_tester/_runtime_type_check_setup.py` | 13         | 0       | 37       | 100.0%   |
| `copier_template_tester/_write_output.py`             | 87         | 1       | 16       | 99.0%    |
| `copier_template_tester/main.py`                      | 47         | 7       | 20       | 80.4%    |
| **Totals**                                            | 179        | 8       | 76       | 94.0%    |

Generated on: 2026-01-28
<!-- {cte} -->
