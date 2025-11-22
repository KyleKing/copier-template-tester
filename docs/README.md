# copier-template-tester

![./ctt-logo.png](./ctt-logo.png)

Parametrize copier templates to test for syntax errors, check the expected output, and to check against copier versions.

Note that `ctt` only tests the `copier copy` operation and doesn't check the `update` behavior and any version-specific logic that your template may contain because of how quickly those tests become complex.

## Usage

### Configuration File

When creating a copier template repository, I recommend following the nested ["subdirectory" approach](https://copier.readthedocs.io/en/latest/configuring/#subdirectory) so that the directory looks like this:

```sh
└── template_dir
│   └── {{ _copier_conf.answers_file }}.jinja
├── README.md
├── copier.yml
└── ctt.toml
```

Create a new `ctt.toml` file in the top-level directory of your copier repository. Populate the file to look like the below example.

```toml
# Specify shared data across all 'output' destinations
# Note that the copier.yml defaults are used whenever the key is not set in this file
[defaults]
project_name = "placeholder"
copyright_year = 2022

# Parametrize each output with a relative path and optionally any values to override
[output.".ctt/defaults"]

[output.".ctt/no_all"]
package_name = "testing-no-all"
include_all = false
```

#### Extra tasks

> **Added in version 2.2.0**

The `_extra_tasks` key allows you to run additional commands after a copier template is generated. These tasks are appended to the template's existing tasks and executed in the generated project directory. This feature is particularly useful for:

- Running linters and formatters (e.g., `pre-commit`, `ruff`)
- Executing test suites to validate generated code
- Performing project initialization steps
- Verifying the generated output

**Task formats:**

CTT supports the same task formats as copier templates:

```toml
# String format: simple command
_extra_tasks = ["poetry run pytest"]

# List format: command with arguments
_extra_tasks = [["poetry", "run", "pytest", "-v"]]

# Dict format: command with conditions
_extra_tasks = [
  {cmd = "pre-commit run --all-files", when = "{{ python_version >= '3.10' }}"},
]

# Mixed formats
_extra_tasks = [
  "pre-commit run --all-files",
  ["poetry", "run", "pytest"],
  {cmd = "echo 'Done!'"},
]
```

**Merging behavior:**

Tasks defined in `[defaults]` are merged with output-specific `_extra_tasks`:

```toml
[defaults]
_extra_tasks = [
  "pre-commit run --all-files",  # Runs for all outputs
]

[output.".ctt/defaults"]
# Inherits default tasks only

[output.".ctt/with-tests"]
_extra_tasks = [
  "poetry run pytest",  # Runs AFTER pre-commit for this output only
]
```

**Example use case:**

```toml
[defaults]
project_name = "my-project"
_extra_tasks = [
  "pre-commit install",
  "pre-commit run --all-files",
]

[output.".ctt/python310"]
python_version = "3.10"

[output.".ctt/python312"]
python_version = "3.12"
_extra_tasks = [
  "poetry run pytest",  # Only runs for python312 output
]
```

In this example:
- Both outputs run `pre-commit install` and `pre-commit run --all-files`
- Only `.ctt/python312` additionally runs `poetry run pytest`

### Pre-Commit Hook

First, add this section to your `.pre-commit-config.yml` file:

```yaml
repos:
  - repo: https://github.com/KyleKing/copier-template-tester
    rev: main
    hooks:
      - id: copier-template-tester
```

Install and update to the latest revision:

```sh
pre-commit autoupdate
```

The run with `pre-commit`:

```sh
pre-commit run --all-files copier-template-tester
```

### pipx

You can also try `ctt` as a CLI tool by installing with `pipx`:

```sh
pipx install copier-template-tester

cd ~/your/copier/project
ctt
```

### More Examples

For more example code, see the [scripts] directory or the [tests].

## Project Status

See the `Open Issues` and/or the [CODE_TAG_SUMMARY]. For release history, see the [CHANGELOG].

## Contributing

We welcome pull requests! For your pull request to be accepted smoothly, we suggest that you first open a GitHub issue to discuss your idea. For resources on getting started with the code base, see the below documentation:

- [DEVELOPER_GUIDE]
- [STYLE_GUIDE]

## Code of Conduct

We follow the [Contributor Covenant Code of Conduct][contributor-covenant].

### Open Source Status

We try to reasonably meet most aspects of the "OpenSSF scorecard" from [Open Source Insights](https://deps.dev/pypi/copier-template-tester)

## Responsible Disclosure

If you have any security issue to report, please contact the project maintainers privately. You can reach us at [dev.act.kyle@gmail.com](mailto:dev.act.kyle@gmail.com).

## License

[LICENSE]

[changelog]: https://copier-template-tester.kyleking.me/docs/CHANGELOG
[code_tag_summary]: https://copier-template-tester.kyleking.me/docs/CODE_TAG_SUMMARY
[contributor-covenant]: https://www.contributor-covenant.org
[developer_guide]: https://copier-template-tester.kyleking.me/docs/DEVELOPER_GUIDE
[license]: https://github.com/kyleking/copier-template-tester/blob/main/LICENSE
[scripts]: https://github.com/kyleking/copier-template-tester/blob/main/scripts
[style_guide]: https://copier-template-tester.kyleking.me/docs/STYLE_GUIDE
[tests]: https://github.com/kyleking/copier-template-tester/blob/main/tests
