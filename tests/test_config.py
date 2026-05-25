"""Tests for scripts._config — TOML manifest loader.

These tests define the expected interface for the config loader module.
The module should:
- Load .streetlights-demo/manifest.toml from a given root or cwd
- Provide typed access to all manifest sections
- Raise clear errors when manifest is missing or malformed
- Support schema versioning
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestLoadManifest:
    """Test manifest loading from .streetlights-demo/manifest.toml."""

    def test_load_from_explicit_path(self, manifest_path: Path) -> None:
        """Config loader can load a manifest from an explicit file path."""
        from scripts._config import load_manifest

        config = load_manifest(manifest_path)
        assert config is not None

    def test_load_from_project_root(self, manifest_dir: Path) -> None:
        """Config loader discovers manifest.toml from a project root directory."""
        from scripts._config import load_manifest

        config = load_manifest(project_root=manifest_dir)
        assert config is not None

    def test_raises_when_manifest_missing(self, empty_manifest_dir: Path) -> None:
        """Config loader raises FileNotFoundError when manifest doesn't exist."""
        from scripts._config import load_manifest

        with pytest.raises(FileNotFoundError):
            load_manifest(project_root=empty_manifest_dir)

    def test_raises_on_malformed_toml(self, tmp_path: Path) -> None:
        """Config loader raises ValueError on invalid TOML content."""
        from scripts._config import load_manifest

        demo_dir = tmp_path / ".streetlights-demo"
        demo_dir.mkdir()
        (demo_dir / "manifest.toml").write_text("this is [[ invalid toml")

        with pytest.raises((ValueError, Exception)):
            load_manifest(project_root=tmp_path)


class TestManifestFields:
    """Test typed access to manifest configuration fields."""

    def test_schema_version(self, manifest_path: Path) -> None:
        """Manifest exposes schema_version as a string."""
        from scripts._config import load_manifest

        config = load_manifest(manifest_path)
        assert config.schema_version == "1"

    def test_project_name(self, manifest_path: Path) -> None:
        """Manifest exposes project_name."""
        from scripts._config import load_manifest

        config = load_manifest(manifest_path)
        assert config.project_name == "streetlights-demo"

    def test_demo_resource_prefix(self, manifest_path: Path) -> None:
        """Manifest exposes project.demo_resource_prefix."""
        from scripts._config import load_manifest

        config = load_manifest(manifest_path)
        assert config.demo_resource_prefix == "testuser"

    def test_snowflake_connection(self, manifest_path: Path) -> None:
        """Manifest exposes snowflake.connection."""
        from scripts._config import load_manifest

        config = load_manifest(manifest_path)
        assert config.snowflake_connection == "devrel-ent"

    def test_demo_database(self, manifest_path: Path) -> None:
        """Manifest exposes demo.database."""
        from scripts._config import load_manifest

        config = load_manifest(manifest_path)
        assert config.database == "TESTUSER_STREETLIGHTS"

    def test_demo_cld_database(self, manifest_path: Path) -> None:
        """Manifest exposes demo.cld_database."""
        from scripts._config import load_manifest

        config = load_manifest(manifest_path)
        assert config.cld_database == "TESTUSER_STREETLIGHTS_CLD"

    def test_demo_warehouse(self, manifest_path: Path) -> None:
        """Manifest exposes demo.warehouse."""
        from scripts._config import load_manifest

        config = load_manifest(manifest_path)
        assert config.warehouse == "TESTUSER_STREETLIGHTS_WH"

    def test_demo_pg_instance(self, manifest_path: Path) -> None:
        """Manifest exposes demo.pg_instance."""
        from scripts._config import load_manifest

        config = load_manifest(manifest_path)
        assert config.pg_instance == "testuser_streetlights_pg"

    def test_demo_city(self, manifest_path: Path) -> None:
        """Manifest exposes demo.city."""
        from scripts._config import load_manifest

        config = load_manifest(manifest_path)
        assert config.city == "Portland"

    def test_demo_center_lat(self, manifest_path: Path) -> None:
        """Manifest exposes demo.center_lat as a float."""
        from scripts._config import load_manifest

        config = load_manifest(manifest_path)
        assert config.center_lat == pytest.approx(45.5152)

    def test_demo_center_lng(self, manifest_path: Path) -> None:
        """Manifest exposes demo.center_lng as a float."""
        from scripts._config import load_manifest

        config = load_manifest(manifest_path)
        assert config.center_lng == pytest.approx(-122.6784)


class TestManifestDefaults:
    """Test that missing optional fields get sensible defaults."""

    def test_missing_city_defaults_to_none_or_empty(self, tmp_path: Path) -> None:
        """If demo.city is not specified, config returns None or empty string."""
        from scripts._config import load_manifest

        demo_dir = tmp_path / ".streetlights-demo"
        demo_dir.mkdir()
        (demo_dir / "manifest.toml").write_text(
            'schema_version = "1"\n'
            'project_name = "streetlights-demo"\n'
            "\n"
            "[project]\n"
            'demo_resource_prefix = "test"\n'
            "\n"
            "[snowflake]\n"
            'connection = "default"\n'
            "\n"
            "[demo]\n"
            'database = "TEST_DB"\n'
            'cld_database = "TEST_CLD"\n'
            'warehouse = "TEST_WH"\n'
            'pg_instance = "test_pg"\n'
        )
        config = load_manifest(project_root=tmp_path)
        # city should be None or empty when not specified
        assert config.city is None or config.city == ""

    def test_unsupported_schema_version_raises(self, tmp_path: Path) -> None:
        """If schema_version is unsupported, raise an error."""
        from scripts._config import load_manifest

        demo_dir = tmp_path / ".streetlights-demo"
        demo_dir.mkdir()
        (demo_dir / "manifest.toml").write_text(
            'schema_version = "999"\n'
            'project_name = "streetlights-demo"\n'
            "\n"
            "[project]\n"
            'demo_resource_prefix = "test"\n'
            "\n"
            "[snowflake]\n"
            'connection = "default"\n'
            "\n"
            "[demo]\n"
            'database = "TEST_DB"\n'
            'cld_database = "TEST_CLD"\n'
            'warehouse = "TEST_WH"\n'
            'pg_instance = "test_pg"\n'
        )
        with pytest.raises(ValueError, match="schema_version"):
            load_manifest(project_root=tmp_path)
