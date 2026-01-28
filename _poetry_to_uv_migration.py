# /// script
# dependencies = ["tomlkit>=0.13"]
# requires-python = ">=3.9"
# ///
"""Migration Script for Poetry to uv conversion.

Run this script to migrate an existing poetry-based project to uv.
The script will self-delete only if no migration is needed.

Usage:
    uv run _poetry_to_uv_migration.py

If migration is performed, review changes carefully before running:
    uv lock
    uv sync --all-extras
"""

from __future__ import annotations

from itertools import starmap
from pathlib import Path


def _log(message: str) -> None:
    print(f'[migration] {message}')  # noqa: T201


def _check_if_migration_needed() -> bool:
    """Check if migration is needed by checking for poetry.lock."""
    return Path('poetry.lock').is_file()


def _format_dependency_spec(name: str, spec: str | dict) -> str:
    """Format a dependency specification string."""
    if isinstance(spec, str):
        return f'{name}{spec}'

    version = spec.get('version', '>=0')
    extras = spec.get('extras', [])
    markers = spec.get('markers', '')

    old_calcipy_extras = {'doc', 'lint', 'nox', 'tags', 'test', 'types'}
    if name == 'calcipy' and set(extras) == old_calcipy_extras:
        return 'calcipy[dev]>=5.0.0'

    base = name
    if extras:
        base = f"{name}[{','.join(extras)}]"

    result = f'{base}{version}'
    if markers:
        result = f'{result}; {markers}'
    return result


def _convert_dependencies(deps: dict) -> list[str]:
    """Convert Poetry dependencies to project format, excluding python version."""
    dep_list = []
    for name, spec in deps.items():
        if name == 'python':
            continue
        dep_list.append(_format_dependency_spec(name, spec))
    return dep_list


def _migrate_dependencies() -> bool:
    """Convert dependencies from Poetry to uv format in pyproject.toml.

    Returns:
        True if migration was performed, False otherwise.
    """
    import tomlkit  # noqa: PLC0415

    pyproject_path = Path('pyproject.toml')
    content = pyproject_path.read_text(encoding='utf-8')
    doc = tomlkit.parse(content)
    modified = False

    # Migrate main dependencies to [project.dependencies]
    try:
        _log('Migrating [project.dependencies]...')
        poetry = doc['tool']['poetry']
        deps = _convert_dependencies(poetry['dependencies'])
        if deps:
            if 'project' not in doc:
                doc.add('project', tomlkit.table())

            # Merge with existing dependencies
            existing_deps = doc['project'].get('dependencies', [])
            all_deps = list(existing_deps) + deps
            doc['project']['dependencies'] = tomlkit.array(all_deps)
            modified = True
            _log(f'Migrated {len(deps)} dependencies to [project.dependencies]')
    except (KeyError, AttributeError) as err:
        _log(f'Skipping [project.dependencies]: {err}')

    # Migrate dev dependencies to [dependency-groups.dev]
    try:
        _log('Migrating [dependency-groups.dev]...')
        poetry = doc['tool']['poetry']
        dev_deps_dict = poetry['group']['dev']['dependencies']
        dev_deps = list(starmap(_format_dependency_spec, dev_deps_dict.items()))
        if dev_deps:
            if 'dependency-groups' not in doc:
                doc.add('dependency-groups', tomlkit.table())

            # Merge with existing dev dependencies
            existing_dev_deps = doc['dependency-groups'].get('dev', [])
            all_dev_deps = list(existing_dev_deps) + dev_deps
            doc['dependency-groups']['dev'] = tomlkit.array(all_dev_deps)
            modified = True
            _log(f'Migrated {len(dev_deps)} dependencies to [dependency-groups.dev]')
    except (KeyError, AttributeError) as err:
        _log(f'Skipping [dependency-groups.dev]: {err}')

    if modified:
        pyproject_path.write_text(tomlkit.dumps(doc), encoding='utf-8')
        _log('Dependencies migrated successfully')
        return True

    _log('No dependency migration needed')
    return False


def _cleanup_poetry_files() -> bool:
    """Remove Poetry-specific files.

    Returns:
        True if any file was removed, False otherwise.
    """
    removed = False

    try:
        poetry_lock = Path('poetry.lock')
        if poetry_lock.is_file():
            _log('Removing poetry.lock')
            poetry_lock.unlink()
            removed = True
    except OSError as err:
        _log(f'Failed to remove poetry.lock: {err}')

    try:
        poetry_toml = Path('poetry.toml')
        if poetry_toml.is_file():
            _log('Removing poetry.toml')
            poetry_toml.unlink()
            removed = True
    except OSError as err:
        _log(f'Failed to remove poetry.toml: {err}')

    return removed


def main() -> None:
    """Run the migration."""
    if not _check_if_migration_needed():
        _log('No poetry.lock found - migration not needed and self-deleting')
        Path(__file__).unlink()
        return

    _log('Starting Poetry to uv dependency migration...')
    _log('')

    migration_performed = False

    # Migrate dependencies
    try:
        migration_performed |= _migrate_dependencies()
    except Exception as err:
        _log(f'Error migrating dependencies: {err}')

    # Cleanup poetry files
    try:
        migration_performed |= _cleanup_poetry_files()
    except Exception as err:
        _log(f'Error cleaning up poetry files: {err}')

    if not migration_performed:
        _log('No changes were made')
        return

    _log('')
    _log('Migration complete!')
    _log('')
    _log('Next steps:')
    _log('  1. Review changes: git diff')
    _log('  2. Run: uv lock')
    _log('  3. Run: uv sync --all-extras')
    _log('  4. Delete this script when done')
    _log('')


if __name__ == '__main__':
    main()
