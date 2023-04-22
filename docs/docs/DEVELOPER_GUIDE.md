# Developer Notes

## Local Development

```sh
git clone https://github.com/kyleking/copier-template-tester.git
cd copier-template-tester
poetry install --sync

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
| File                                            |   Statements |   Missing |   Excluded | Coverage   |
|-------------------------------------------------|--------------|-----------|------------|------------|
| `copier_template_tester/__init__.py`            |            2 |         0 |          0 | 100.0%     |
| `copier_template_tester/_config.py`             |           20 |         2 |          0 | 90.0%      |
| `copier_template_tester/_pre_commit_support.py` |           19 |         0 |          0 | 100.0%     |
| `copier_template_tester/_write_output.py`       |           52 |         7 |          2 | 86.5%      |
| `copier_template_tester/main.py`                |           25 |         0 |         15 | 100.0%     |
| **Totals**                                      |          118 |         9 |         17 | 92.4%      |

Generated on: 2023-04-22
<!-- {cte} -->
