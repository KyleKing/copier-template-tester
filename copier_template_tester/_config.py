"""CTT config."""

from pathlib import Path

from beartype import beartype
from corallium.log import get_logger
from corallium.tomllib import tomllib

logger = get_logger()


@beartype
def _validate_config(config: dict) -> None:  # type: ignore[type-arg]
    if 'defaults' not in config:
        logger.text('Warning: You probably want a section: [defaults]')
    if not config.get('output'):
        raise RuntimeError('CTT expected headers like: [output."<something>"]')


@beartype
def load_config(base_dir: Path) -> dict:  # type: ignore[type-arg]
    """Read the ctt config from `CWD`."""
    cfg_path = base_dir / 'ctt.toml'
    if cfg_path.is_file():
        config: dict = tomllib.loads(cfg_path.read_text())  # type: ignore[type-arg]
        _validate_config(config)
        return config
    msg = f'No configuration file found. Expected: {cfg_path.absolute()}'
    raise ValueError(msg)
