"""Copier Template Tester.

Based on: https://github.com/copier-org/copier/blob/ccfbc9a923f4228af7ca2bf067493665aa15d07c/tests/helpers.py#L20-L81

"""

from pathlib import Path

import copier
from beartype import beartype

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


@beartype
def _validate_config(config: dict) -> None:  # type: ignore[type-arg]
    if 'defaults' not in config:
        print('Warning: You probably want a section: [defaults]')  # noqa: T001
    if not config.get('output'):
        raise RuntimeError('CTT expected headers like: [output."<something>"]')


@beartype
def _load_config(base_dir: Path) -> dict:  # type: ignore[type-arg]
    """Read the ctt config from `CWD`."""
    cfg_path = base_dir / 'ctt.toml'
    if cfg_path.is_file():
        config: dict = tomllib.loads(cfg_path.read_text())  # type: ignore[type-arg]
        _validate_config(config)
        return config
    raise ValueError(f'No configuration file found. Expected: {cfg_path.absolute()}')  # pragma: no cover


@beartype
def _render(  # type: ignore[no-untyped-def]
    src_path: Path,
    dst_path: Path,
    data: dict[str, bool | int | float | str | None],
    **kwargs,
) -> None:
    """Copy the specified directory to the target location with provided data.

    kwargs documentation: https://github.com/copier-org/copier/blob/103828b59fd9eb671b5ffa909004d1577742300b/copier/main.py#L86-L173

    """
    kwargs.setdefault('cleanup_on_error', False)
    kwargs.setdefault('data', data or {})
    kwargs.setdefault('defaults', True)
    kwargs.setdefault('overwrite', True)
    kwargs.setdefault('quiet', False)
    copier.run_auto(str(src_path), dst_path, **kwargs)


@beartype
def run(base_dir: Path | None = None) -> None:
    """Main class to run ctt."""
    base_dir = base_dir or Path.cwd()
    config = _load_config(base_dir)
    defaults = config.get('defaults', {})

    input_path = base_dir
    for key, data in config['output'].items():
        output_path = base_dir / key
        output_path.mkdir(parents=True, exist_ok=True)
        print(f'Creating: {output_path}')  # noqa: T001
        _render(input_path, base_dir / output_path, data=defaults | data)


if __name__ == '__main__':  # pragma: no cover
    run(Path.cwd().parent / 'calcipy_template')
