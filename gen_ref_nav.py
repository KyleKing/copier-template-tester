"""Generate the code reference pages.

Adapted without navigation from:
https://github.com/pawamoy/copier-pdm/blob/adff9b64887d0b4c9ec0b42de1698b34858a511e/project/scripts/gen_ref_nav.py

"""

from pathlib import Path

import mkdocs_gen_files
from corallium.tomllib import tomllib


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


_config = tomllib.loads(Path('pyproject.toml').read_text(encoding='utf-8'))
_pkg_name = _config['tool']['poetry']['name']
src = Path(_pkg_name)
for path in sorted(src.rglob('*.py')):
    for line in path.read_text().split('\n'):
        if has_public_code(line):
            break
    else:
        continue  # Do not include the file in generated documentation

    module_path = path.with_suffix('')
    doc_path = path.with_suffix('.md')
    full_doc_path = Path('reference', doc_path)

    parts = tuple(module_path.parts)
    if parts[-1] == '__init__':
        parts = parts[:-1]
        doc_path = doc_path.with_name('index.md')
        full_doc_path = full_doc_path.with_name('index.md')
    elif parts[-1].startswith('_'):
        continue

    with mkdocs_gen_files.open(full_doc_path, 'w') as fd:
        ident = '.'.join(parts)
        fd.write(f'::: {ident}')

    mkdocs_gen_files.set_edit_path(full_doc_path, path)
