"""Tests for the [databricks] section of the demo manifest (scripts._manifest)."""

from __future__ import annotations

from pathlib import Path


class TestDatabricksSection:
    """Manifest round-trips the [databricks] section and defaults platform to both."""

    def _write_manifest(self, root: Path, body: str) -> Path:
        demo_dir = root / ".streetlights-demo"
        demo_dir.mkdir(parents=True, exist_ok=True)
        path = demo_dir / "manifest.toml"
        path.write_text(body)
        return path

    def test_loads_databricks_section(self, tmp_path: Path) -> None:
        from scripts._manifest import load as load_manifest

        self._write_manifest(
            tmp_path,
            '[snowflake]\nconnection = "dev"\n\n'
            "[databricks]\n"
            'host = "https://adb-123.7.azuredatabricks.net"\n'
            'profile = "default"\n'
            'catalog_name = "DEMO_STREETLIGHTS"\n'
            'schema_name = "streetlights"\n'
            'warehouse = "DEMO_STREETLIGHTS_WH"\n'
            'lakebase_instance = "projects/abc/branches/main"\n'
            'genie_space_name = "DEMO_STREETLIGHTS_GENIE"\n'
            'platform = "databricks"\n\n'
            '[streetlights-demo]\nprefix = "demo"\n',
        )
        manifest = load_manifest(tmp_path)
        assert manifest.databricks.host == "https://adb-123.7.azuredatabricks.net"
        assert manifest.databricks.catalog_name == "DEMO_STREETLIGHTS"
        assert manifest.databricks.lakebase_instance == "projects/abc/branches/main"
        assert manifest.databricks.platform == "databricks"
        # snowflake section untouched
        assert manifest.snowflake.connection == "dev"

    def test_defaults_when_section_absent(self, tmp_path: Path) -> None:
        from scripts._manifest import load as load_manifest

        self._write_manifest(tmp_path, '[streetlights-demo]\nprefix = "demo"\n')
        manifest = load_manifest(tmp_path)
        assert manifest.databricks.host == ""
        assert manifest.databricks.platform == "both"

    def test_round_trip_preserves_databricks(self, tmp_path: Path) -> None:
        from scripts._manifest import load as load_manifest
        from scripts._manifest import save as save_manifest

        self._write_manifest(
            tmp_path,
            '[databricks]\nhost = "https://example.cloud.databricks.com"\nplatform = "both"\n\n'
            '[streetlights-demo]\nprefix = "demo"\n',
        )
        manifest = load_manifest(tmp_path)
        manifest.databricks.warehouse = "DEMO_STREETLIGHTS_WH"
        save_manifest(tmp_path, manifest)

        reloaded = load_manifest(tmp_path)
        assert reloaded.databricks.host == "https://example.cloud.databricks.com"
        assert reloaded.databricks.warehouse == "DEMO_STREETLIGHTS_WH"
        assert reloaded.databricks.platform == "both"
