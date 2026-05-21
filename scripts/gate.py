"""Gate checks for streetlights demo progression.

Provides pre-step validation functions that return GateResult objects
indicating success/failure with a descriptive message.
"""

from __future__ import annotations

import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GateResult:
    """Result of a gate check."""

    success: bool
    message: str


def _load_manifest(project_root: Path) -> dict:
    """Load manifest.toml from project_root/.streetlights-demo/."""
    manifest_file = project_root / ".streetlights-demo" / "manifest.toml"
    with open(manifest_file, "rb") as f:
        return tomllib.load(f)


def _pg_ping(instance: str) -> bool:
    """Check if PG instance is reachable via snow CLI."""
    result = subprocess.run(
        ["snow", "postgres", "execute", "-i", instance, "-c", "SELECT 1"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _cld_table_count(cld_db: str) -> int:
    """Return table count in CLD database."""
    result = subprocess.run(
        ["snow", "sql", "-q", f"SELECT COUNT(*) FROM {cld_db}.INFORMATION_SCHEMA.TABLES"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise Exception(f"CLD database {cld_db} does not exist or is not accessible")
    # Parse count from output
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line.isdigit():
            return int(line)
    return 0


def _get_account_params() -> dict[str, bool]:
    """Get account parameters related to Snowflake Postgres."""
    params = {}
    for param in ["ENABLE_SNOWFLAKE_POSTGRES", "ENABLE_POSTGRES_HIDDEN_EXTERNAL_VOLUME"]:
        result = subprocess.run(
            ["snow", "sql", "-q", f"SHOW PARAMETERS LIKE '{param}' IN ACCOUNT"],
            capture_output=True,
            text=True,
        )
        params[param] = result.returncode == 0 and "true" in result.stdout.lower()
    return params


def check_manifest(project_root: Path) -> GateResult:
    """Gate: manifest.toml exists and is parseable."""
    manifest_file = project_root / ".streetlights-demo" / "manifest.toml"
    if not manifest_file.exists():
        return GateResult(
            success=False,
            message="Manifest not found at .streetlights-demo/manifest.toml",
        )
    try:
        _load_manifest(project_root)
        return GateResult(success=True, message="Manifest loaded successfully")
    except Exception as e:
        return GateResult(success=False, message=f"Manifest parse error: {e}")


def check_pg_reachable(project_root: Path) -> GateResult:
    """Gate: PG instance responds to connection check."""
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    instance = manifest["demo"]["pg_instance"]
    if _pg_ping(instance):
        return GateResult(success=True, message=f"PG instance '{instance}' is reachable")
    return GateResult(success=False, message=f"PG instance '{instance}' is not reachable")


def check_cld_healthy(project_root: Path) -> GateResult:
    """Gate: CLD DB exists + table count > 0."""
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    cld_db = manifest["demo"]["cld_database"]
    try:
        count = _cld_table_count(cld_db)
    except Exception as e:
        return GateResult(success=False, message=f"CLD database error: {e}")

    if count > 0:
        return GateResult(success=True, message=f"CLD healthy: {count} tables found")
    return GateResult(success=False, message="CLD has 0 tables — propagation may not be complete")


def check_account_params(project_root: Path) -> GateResult:
    """Gate: required account params are set."""
    params = _get_account_params()
    if params.get("ENABLE_SNOWFLAKE_POSTGRES"):
        return GateResult(success=True, message="Account params enabled")
    return GateResult(
        success=False,
        message="Required account param ENABLE_SNOWFLAKE_POSTGRES is not enabled",
    )
