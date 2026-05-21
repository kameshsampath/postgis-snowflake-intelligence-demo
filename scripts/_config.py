"""TOML manifest loader for .streetlights-demo/manifest.toml.

Provides typed access to all manifest configuration fields.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_SCHEMA_VERSIONS = {"1"}
MANIFEST_REL_PATH = Path(".streetlights-demo") / "manifest.toml"


@dataclass(frozen=True)
class DemoConfig:
    """Typed representation of the streetlights-demo manifest."""

    schema_version: str
    project_name: str
    demo_resource_prefix: str
    snowflake_connection: str
    database: str
    cld_database: str
    warehouse: str
    pg_instance: str
    pg_service: str
    city: str | None
    center_lat: float | None
    center_lng: float | None


def load_manifest(
    path: Path | None = None,
    *,
    project_root: Path | None = None,
) -> DemoConfig:
    """Load and parse the streetlights-demo manifest.

    Args:
        path: Explicit path to a manifest.toml file.
        project_root: Project root directory containing .streetlights-demo/.

    Returns:
        DemoConfig with typed access to all manifest fields.

    Raises:
        FileNotFoundError: If manifest cannot be found.
        ValueError: If TOML is malformed or schema_version is unsupported.
    """
    manifest_path = _resolve_path(path, project_root)

    if not manifest_path.exists():
        msg = f"Manifest not found: {manifest_path}"
        raise FileNotFoundError(msg)

    raw = manifest_path.read_text(encoding="utf-8")

    try:
        data = tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        msg = f"Malformed TOML in {manifest_path}: {exc}"
        raise ValueError(msg) from exc

    schema_version = data.get("schema_version", "")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        msg = (
            f"Unsupported schema_version '{schema_version}'."
            f" Supported: {SUPPORTED_SCHEMA_VERSIONS}"
        )
        raise ValueError(msg)

    project = data.get("project", {})
    snowflake = data.get("snowflake", {})
    demo = data.get("demo", {})

    return DemoConfig(
        schema_version=schema_version,
        project_name=data.get("project_name", ""),
        demo_resource_prefix=project.get("demo_resource_prefix", ""),
        snowflake_connection=snowflake.get("connection", ""),
        database=demo.get("database", ""),
        cld_database=demo.get("cld_database", ""),
        warehouse=demo.get("warehouse", ""),
        pg_instance=demo.get("pg_instance", ""),
        pg_service=demo.get("pg_service", demo.get("pg_instance", "")),
        city=demo.get("city") or None,
        center_lat=demo.get("center_lat"),
        center_lng=demo.get("center_lng"),
    )


def _resolve_path(
    path: Path | None,
    project_root: Path | None,
) -> Path:
    """Resolve the manifest path from explicit path or project root."""
    if path is not None:
        return Path(path)

    if project_root is not None:
        return project_root / MANIFEST_REL_PATH

    # Walk up from CWD
    cwd = Path.cwd()
    current = cwd
    while True:
        candidate = current / MANIFEST_REL_PATH
        if candidate.exists():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent

    # Return default (will trigger FileNotFoundError in caller)
    return cwd / MANIFEST_REL_PATH
