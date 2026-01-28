# Developer Notes

## Local Development

```sh
git clone https://github.com/kyleking/copier-template-tester.git
cd copier-template-tester
poetry install --sync
poetry run calcipy-pack pack.install-extras

# See the available tasks
poetry run calcipy
# Or use a local 'run' file (so that 'calcipy' can be extended)
./run

# Run the default task list (lint, auto-format, test coverage, etc.)
./run main

# Make code changes and run specific tasks as needed:
./run lint.fix test
```

## Publishing

For testing, create an account on [TestPyPi](https://test.pypi.org/legacy/). Replace `...` with the API token generated on TestPyPi or PyPi respectively

```sh
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config pypi-token.testpypi ...

./run main pack.publish --to-test-pypi
# If you didn't configure a token, you will need to provide your username and password to publish
```

To publish to the real PyPi

```sh
poetry config pypi-token.pypi ...
./run release

# Or for a pre-release
./run release --suffix=rc
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
| `copier_template_tester/main.py`                      | 34         | 4       | 20       | 88.2%    |
| **Totals**                                            | 166        | 5       | 76       | 96.7%    |

Generated on: 2026-01-27
<!-- {cte} -->
