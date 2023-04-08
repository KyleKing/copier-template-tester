# noqa: INP001
"""Generate the code reference pages and navigation.

Copied from:
https://github.com/pawamoy/copier-pdm/blob/79135565c4c7f756204a5f460e87129649f8b704/project/docs/gen_ref_nav.py

"""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

for path in sorted(Path('copier_template_tester').rglob('*.py')):
    module_path = path.with_suffix('')
    doc_path = path.with_suffix('.md')
    full_doc_path = Path('reference', doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == '__init__':
        parts = parts[:-1]
        doc_path = doc_path.with_name('index.md')
        full_doc_path = full_doc_path.with_name('index.md')
    elif parts[-1] == '__main__':
        continue

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, 'w') as fd:
        ident = '.'.join(parts)
        fd.write(f'::: {ident}')

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

# FYI, to add pages manually, use: `nav["package", "module"] = "path/to/file.md"`

with mkdocs_gen_files.open('reference/SUMMARY.md', 'w') as nav_file:
    nav_file.writelines(nav.build_literate_nav())
