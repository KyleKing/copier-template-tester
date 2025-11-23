from contextlib import nullcontext as does_not_raise
from pathlib import Path

import pytest
from corallium.log import get_logger

from copier_template_tester._config import _validate_config, load_temporal_config
from copier_template_tester.temporal import TemporalSnapshot

logger = get_logger()


@pytest.mark.parametrize(
    ('config', 'expectation'),
    [
        (
            {},
            pytest.raises(
                RuntimeError,
                match=r'CTT expected headers like: \[output."<something>"\]',
            ),
        ),
        (
            {'output': {'something': True}},
            does_not_raise(),
        ),
    ],
    ids=[
        'Check an incomplete config',
        'Check a normal config',
    ],
)
def test_validate_config(config: dict, expectation) -> None:  # type: ignore[type-arg]
    with expectation:
        _validate_config(config)


class TestTemporalConfig:
    """Test temporal configuration loading."""

    def test_load_temporal_config_disabled(self, tmp_path: Path) -> None:
        """Test loading config when temporal testing is disabled."""
        # Create minimal config without temporal section
        config_path = tmp_path / 'ctt.toml'
        config_path.write_text("""
[defaults]
project_name = "test"

[output.test]
project_name = "test"
""")

        settings, snapshots = load_temporal_config(tmp_path)
        assert settings == {}
        assert snapshots == []

    def test_load_temporal_config_enabled_no_snapshots(self, tmp_path: Path) -> None:
        """Test loading config with temporal enabled but no snapshots."""
        config_path = tmp_path / 'ctt.toml'
        config_path.write_text("""
[defaults]
project_name = "test"

[output.test]
project_name = "test"

[temporal]
enabled = true
source_project = "../my-project"
""")

        settings, snapshots = load_temporal_config(tmp_path)
        assert settings['enabled'] is True
        assert settings['source_project'] == '../my-project'
        assert settings['mode'] == 'copy_history'  # default
        assert settings['parallel'] is False  # default
        assert settings['keep_temp_dirs'] is False  # default
        assert snapshots == []

    def test_load_temporal_config_with_snapshots(self, tmp_path: Path) -> None:
        """Test loading config with temporal snapshots."""
        config_path = tmp_path / 'ctt.toml'
        config_path.write_text("""
[defaults]
project_name = "test"

[output.test]
project_name = "test"

[temporal]
enabled = true
source_project = "../my-project"
mode = "shallow_clone"
parallel = true
keep_temp_dirs = true

[[temporal.snapshots]]
name = "v1.0-baseline"
ref = "v1.0.0"
description = "Project at v1.0"
template_data = {project_name = "test", python_version = "3.10"}

[[temporal.snapshots]]
name = "v2.0-current"
ref = "HEAD"
template_data = {project_name = "test", python_version = "3.12"}
""")

        settings, snapshots = load_temporal_config(tmp_path)

        # Check settings
        assert settings['enabled'] is True
        assert settings['source_project'] == '../my-project'
        assert settings['mode'] == 'shallow_clone'
        assert settings['parallel'] is True
        assert settings['keep_temp_dirs'] is True

        # Check snapshots
        assert len(snapshots) == 2

        snapshot1 = snapshots[0]
        assert isinstance(snapshot1, TemporalSnapshot)
        assert snapshot1.name == 'v1.0-baseline'
        assert snapshot1.ref == 'v1.0.0'
        assert snapshot1.description == 'Project at v1.0'
        assert snapshot1.template_data == {'project_name': 'test', 'python_version': '3.10'}

        snapshot2 = snapshots[1]
        assert snapshot2.name == 'v2.0-current'
        assert snapshot2.ref == 'HEAD'
        assert snapshot2.description == ''  # default
        assert snapshot2.template_data == {'project_name': 'test', 'python_version': '3.12'}

    def test_load_temporal_config_missing_source_project(self, tmp_path: Path) -> None:
        """Test that missing source_project raises error."""
        config_path = tmp_path / 'ctt.toml'
        config_path.write_text("""
[defaults]
project_name = "test"

[output.test]
project_name = "test"

[temporal]
enabled = true
""")

        with pytest.raises(ValueError, match='source_project not specified'):
            load_temporal_config(tmp_path)

    def test_load_temporal_config_missing_snapshot_name(self, tmp_path: Path) -> None:
        """Test that snapshot without name raises error."""
        config_path = tmp_path / 'ctt.toml'
        config_path.write_text("""
[defaults]
project_name = "test"

[output.test]
project_name = "test"

[temporal]
enabled = true
source_project = "../my-project"

[[temporal.snapshots]]
ref = "v1.0.0"
""")

        with pytest.raises(ValueError, match='missing required field: name'):
            load_temporal_config(tmp_path)

    def test_load_temporal_config_missing_snapshot_ref(self, tmp_path: Path) -> None:
        """Test that snapshot without ref raises error."""
        config_path = tmp_path / 'ctt.toml'
        config_path.write_text("""
[defaults]
project_name = "test"

[output.test]
project_name = "test"

[temporal]
enabled = true
source_project = "../my-project"

[[temporal.snapshots]]
name = "test"
""")

        with pytest.raises(ValueError, match='missing required field: ref'):
            load_temporal_config(tmp_path)
