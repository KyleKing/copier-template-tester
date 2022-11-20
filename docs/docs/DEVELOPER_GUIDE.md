# Developer Notes

## Local Development

```sh
git clone https://github.com/kyleking/copier-template-tester.git
cd copier-template-tester
poetry install

# See the available tasks
poetry run doit list

# Run the default task list (lint, auto-format, test coverage, etc.)
poetry run doit --continue

# Make code changes and run specific tasks as needed:
poetry run doit run test
```

## Publishing

For testing, create an account on [TestPyPi](https://test.pypi.org/legacy/). Replace `...` with the API token generated on TestPyPi or PyPi respectively

```sh
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config pypi-token.testpypi ...

poetry run doit run publish_test_pypi
# If you didn't configure a token, you will need to provide your username and password to publish
```

To publish to the real PyPi

```sh
poetry config pypi-token.pypi ...
poetry run doit run publish

# For a full release, triple check the default tasks, increment the version, rebuild documentation (twice), and publish!
poetry run doit run --continue
poetry run doit run cl_bump lock document deploy_docs publish

# For pre-releases use cl_bump_pre
poetry run doit run cl_bump_pre -p rc
poetry run doit run lock document deploy_docs publish
```

## Current Status

<!-- {cts} COVERAGE -->
| File                                 |   Statements |   Missing |   Excluded | Coverage   |
|--------------------------------------|--------------|-----------|------------|------------|
| `copier_template_tester/__init__.py` |            2 |         0 |          0 | 100.0%     |
| `copier_template_tester/main.py`     |           38 |         0 |          5 | 100.0%     |
| **Totals**                           |           40 |         0 |          5 | 100.0%     |

Generated on: 2022-11-20
<!-- {cte} -->
