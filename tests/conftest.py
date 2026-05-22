"""Shared fixtures for streetlights-demo tests."""

from __future__ import annotations

from pathlib import Path

import pytest

SAMPLE_MANIFEST = """\
schema_version = "1"
project_name   = "streetlights-demo"

[snowflake]
connection = "devrel-ent"

[streetlights-demo]
prefix       = "testuser"
database     = "TESTUSER_STREETLIGHTS"
cld_database = "TESTUSER_STREETLIGHTS_CLD"
warehouse    = "TESTUSER_STREETLIGHTS_WH"
pg_instance  = "testuser_streetlights_pg"
city         = "Portland"
center_lat   = 45.5152
center_lng   = -122.6784
"""


@pytest.fixture()
def manifest_dir(tmp_path: Path) -> Path:
    """Create a temporary .streetlights-demo directory with a valid manifest."""
    demo_dir = tmp_path / ".streetlights-demo"
    demo_dir.mkdir()
    manifest_file = demo_dir / "manifest.toml"
    manifest_file.write_text(SAMPLE_MANIFEST)
    return tmp_path


@pytest.fixture()
def manifest_path(manifest_dir: Path) -> Path:
    """Return path to the manifest.toml inside the temp directory."""
    return manifest_dir / ".streetlights-demo" / "manifest.toml"


@pytest.fixture()
def empty_manifest_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with NO .streetlights-demo folder."""
    return tmp_path
