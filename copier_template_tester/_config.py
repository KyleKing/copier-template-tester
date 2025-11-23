"""CTT config."""

from pathlib import Path
from typing import Any

from corallium.log import get_logger
from corallium.tomllib import tomllib

from .temporal import TemporalSnapshot

logger = get_logger()


def _validate_config(config: dict[str, Any]) -> None:
    if 'defaults' not in config:
        logger.text('Warning: You probably want a section: [defaults]')
    if not config.get('output'):
        raise RuntimeError('CTT expected headers like: [output."<something>"]')


def load_config(base_dir: Path) -> dict[str, Any]:
    """Read the ctt config from `CWD`."""
    cfg_path = base_dir / 'ctt.toml'
    if not cfg_path.is_file():  # pragma: no cover
        msg = f'No configuration file found. Expected: {cfg_path.absolute()}'
        raise ValueError(msg)
    config: dict[str, Any] = tomllib.loads(cfg_path.read_text())
    _validate_config(config)
    return config


def load_temporal_config(base_dir: Path) -> tuple[dict[str, Any], list[TemporalSnapshot]]:
    """Load temporal testing configuration from ctt.toml.

    Args:
        base_dir: Base directory containing ctt.toml

    Returns:
        Tuple of (temporal_config, snapshots) where:
        - temporal_config: Dict with enabled, mode, source_project, parallel, keep_temp_dirs
        - snapshots: List of TemporalSnapshot instances

    Raises:
        ValueError: If config file not found or temporal config invalid

    Example config:
        [temporal]
        enabled = true
        mode = "copy_history"
        source_project = "../my-project"
        parallel = true
        keep_temp_dirs = false

        [[temporal.snapshots]]
        name = "v1.0-baseline"
        ref = "v1.0.0"
        description = "Project state at v1.0 release"
        template_data = {project_name = "my-project", python_version = "3.10"}

    """
    config = load_config(base_dir)

    # Check if temporal testing is configured
    temporal_config = config.get('temporal', {})
    if not temporal_config.get('enabled', False):
        return {}, []

    # Extract temporal configuration
    temporal_settings = {
        'enabled': temporal_config.get('enabled', False),
        'mode': temporal_config.get('mode', 'copy_history'),
        'source_project': temporal_config.get('source_project'),
        'parallel': temporal_config.get('parallel', False),
        'keep_temp_dirs': temporal_config.get('keep_temp_dirs', False),
    }

    # Validate source_project
    if not temporal_settings['source_project']:
        msg = 'Temporal testing enabled but source_project not specified in [temporal]'
        raise ValueError(msg)

    # Parse snapshots
    snapshot_configs = temporal_config.get('snapshots', [])
    snapshots = []

    for snapshot_config in snapshot_configs:
        # Validate required fields
        if 'name' not in snapshot_config:
            msg = 'Temporal snapshot missing required field: name'
            raise ValueError(msg)
        if 'ref' not in snapshot_config:
            msg = f"Temporal snapshot '{snapshot_config['name']}' missing required field: ref"
            raise ValueError(msg)

        snapshot = TemporalSnapshot(
            name=snapshot_config['name'],
            ref=snapshot_config['ref'],
            description=snapshot_config.get('description', ''),
            template_data=snapshot_config.get('template_data', {}),
        )
        snapshots.append(snapshot)

    if not snapshots:
        logger.warning('Temporal testing enabled but no snapshots configured')

    return temporal_settings, snapshots
