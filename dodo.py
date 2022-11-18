"""doit Script.

```python3
# Ensure that packages are installed
poetry install
# List Tasks
poetry run doit list
# (Or use a poetry shell)
# > poetry shell
# > doit list

# Run tasks individually (examples below)
poetry run doit run ptw_ff
poetry doit run coverage open_test_docs
# Or all of the tasks in DOIT_CONFIG
poetry run doit
```

"""

from calcipy.doit_tasks import *  # noqa: F401,F403,H303 (Run 'doit list' to see tasks)
from calcipy.doit_tasks import DOIT_CONFIG_RECOMMENDED
from calcipy.log_helpers import activate_debug_logging

from copier_template_tester import __pkg_name__

activate_debug_logging(pkg_names=[__pkg_name__])

# Create list of all tasks run with `poetry run doit`
DOIT_CONFIG = DOIT_CONFIG_RECOMMENDED
