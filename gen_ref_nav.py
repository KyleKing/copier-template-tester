"""Generate the code reference pages.

Runs standalone (before ``zensical build``) and writes real Markdown stubs to
``<doc_dir>/reference/`` for ``mkdocstrings`` to render. Zensical does not yet
support the ``mkdocs-gen-files`` plugin, so this replaces its virtual filesystem
with on-disk files. See: https://github.com/zensical/backlog/issues/8

Adapted without navigation from:
https://github.com/pawamoy/copier-pdm/blob/adff9b64887d0b4c9ec0b42de1698b34858a511e/project/scripts/gen_ref_nav.py

"""

import shutil
from pathlib import Path

from corallium.tomllib import tomllib

_DOC_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _DOC_DIR.parent
_REFERENCE_DIR = _DOC_DIR / 'reference'


def has_public_code(line: str) -> bool:
    """Determine if a given line contains code that will be documented.

    Returns:
        bool: True if line appears to be a public function, class, or method

    """
    for key in ('def', 'async def', 'class'):
        starts = line.startswith(f'{key} ')
        if starts and not line.startswith(f'{key} _'):
            return True
        if starts:
            break
    return False


_config = tomllib.loads((_PROJECT_ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
_pkg_name = _config['project']['name']
src = _PROJECT_ROOT / _pkg_name

if _REFERENCE_DIR.exists():
    shutil.rmtree(_REFERENCE_DIR)

for path in sorted(src.rglob('*.py')):
    for line in path.read_text().split('\n'):
        if has_public_code(line):
            break
    else:
        continue  # Do not include the file in generated documentation

    rel_path = path.relative_to(_PROJECT_ROOT)
    module_path = rel_path.with_suffix('')
    doc_path = rel_path.with_suffix('.md')

    parts = tuple(module_path.parts)
    if parts[-1] == '__init__':
        parts = parts[:-1]
        doc_path = doc_path.with_name('index.md')
    elif parts[-1].startswith('_'):
        continue

    full_doc_path = _REFERENCE_DIR / doc_path
    full_doc_path.parent.mkdir(parents=True, exist_ok=True)
    full_doc_path.write_text(f'::: {".".join(parts)}\n', encoding='utf-8')
