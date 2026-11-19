"""Databricks-specific gate checks for PostGIS Data Intelligence Demo.

Provides Databricks-specific validation functions for the implementation.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from scripts._manifest import load as load_manifest
from scripts.gates.base_gates import GateResult


def _dbx_sql_query(query: str, profile: str | None = None) -> tuple[int, list[dict]]:
    """Run a Databricks SQL query and return (returncode, list-of-row-dicts)."""
    import json as _json

    # Use databricks CLI for SQL execution
    cmd = ["databricks", "sql", "-q", query, "--format", "json"]
    if profile:
        cmd.extend(["--profile", profile])

    r = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode != 0:
        return r.returncode, []
    try:
        return 0, _json.loads(r.stdout)
    except Exception:
        return 0, []


def _dbx_load_manifest(project_root: Path):
    """Load manifest with Databricks-specific sections."""
    try:
        return load_manifest(project_root)
    except Exception as e:
        raise Exception(f"Cannot load manifest: {e}")


# ---------------------------------------------------------------------------
# Databricks gate checks
# ---------------------------------------------------------------------------


def check_lakebase_reachable(project_root: Path) -> GateResult:
    """Gate: Lakebase instance is reachable and accessible."""
    try:
        manifest = _dbx_load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    # Get Databricks configuration from manifest or environment
    import os

    dbx_section = getattr(manifest, "databricks", None)
    profile = getattr(dbx_section, "profile", None) if dbx_section else None
    host = getattr(dbx_section, "host", None) if dbx_section else None

    if not host:
        host = os.environ.get("DATABRICKS_HOST", "")
        if not host:
            return GateResult(
                success=False,
                message=(
                    "No Databricks connection configured. "
                    "Set DATABRICKS_HOST or configure manifest."
                ),
            )
        profile = os.environ.get("DATABRICKS_PROFILE", profile or "default")

    # Try a simple query to test connectivity
    query = "SHOW CATALOGS"
    rc, rows = _dbx_sql_query(query, profile)
    if rc == 0:
        return GateResult(success=True, message="Databricks connection is valid")
    return GateResult(success=False, message=f"Failed to connect to Databricks: return code {rc}")


def check_uc_sync_healthy(project_root: Path) -> GateResult:
    """Gate: Unity Catalog sync between Lakebase and UC is healthy."""
    try:
        manifest = _dbx_load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    # Get catalog and schema names from manifest
    dbx_section = getattr(manifest, "databricks", None)
    catalog_name = getattr(dbx_section, "catalog_name", None) if dbx_section else None
    schema_name = getattr(dbx_section, "schema_name", "streetlights") if dbx_section else None

    if not catalog_name:
        return GateResult(
            success=False,
            message="Databricks catalog name not configured in manifest",
        )

    # Try to query a known table from Lakebase
    query = f"SELECT COUNT(*) FROM {catalog_name}.{schema_name}.street_lights_clean"
    rc, rows = _dbx_sql_query(query)
    if rc == 0 and rows:
        try:
            count = rows[0].get("COUNT(*)", 0)
            if count > 0:
                return GateResult(
                    success=True,
                    message=f"UC sync healthy: {count} rows found in street_lights_clean",
                )
            return GateResult(
                success=False,
                message="UC sync found table but no data",
            )
        except (KeyError, ValueError):
            return GateResult(
                success=False,
                message="UC sync table exists but could not parse count",
            )
    return GateResult(
        success=False,
        message="UC sync not healthy: could not query Lakebase tables",
    )


def check_genie_space_active(project_root: Path) -> GateResult:
    """Gate: Genie space exists and responds to queries."""
    try:
        manifest = _dbx_load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    dbx_section = getattr(manifest, "databricks", None)
    genie_space_name = getattr(dbx_section, "genie_space_name", None) if dbx_section else None
    if not genie_space_name:
        return GateResult(
            success=False,
            message="Genie space name not configured in manifest",
        )

    # Try to describe the Genie space
    from scripts.gates.base_gates import mask_ip

    query = f"DESCRIBE GENIE SPACE {genie_space_name}"
    rc, rows = _dbx_sql_query(query)
    if rc == 0 and rows:
        return GateResult(
            success=True,
            message=f"Genie space '{mask_ip(genie_space_name)}' is active",
        )
    return GateResult(
        success=False,
        message=f"Genie space '{mask_ip(genie_space_name)}' not found or not active",
    )


def check_vector_index_ready(project_root: Path) -> GateResult:
    """Gate: Vector Search index exists and is queryable."""
    try:
        manifest = _dbx_load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    dbx_section = getattr(manifest, "databricks", None)
    vector_index_name = getattr(dbx_section, "vector_index_name", None) if dbx_section else None
    if not vector_index_name:
        return GateResult(
            success=False,
            message="Vector Search index name not configured in manifest",
        )

    # Check if vector index exists
    query = "SHOW VECTOR SEARCH INDEXES"
    rc, rows = _dbx_sql_query(query)
    if rc == 0:
        index_names = [row.get("name", "") for row in rows]
        if vector_index_name in index_names:
            return GateResult(
                success=True,
                message=f"Vector Search index '{vector_index_name}' is ready",
            )
        available = ", ".join(index_names) if index_names else "none"
        return GateResult(
            success=False,
            message=f"Vector Search index '{vector_index_name}' not found. "
            f"Available: {available}",
        )
    return GateResult(success=False, message="Failed to list Vector Search indexes")


def check_dbx_forecast_ready(project_root: Path) -> GateResult:
    """Gate: ML forecast model exists and predictions are available."""
    try:
        manifest = _dbx_load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    dbx_section = getattr(manifest, "databricks", None)
    forecast_model_name = (
        getattr(dbx_section, "forecast_model_name", None) if dbx_section else None
    )
    if not forecast_model_name:
        return GateResult(
            success=False,
            message="Forecast model name not configured in manifest",
        )

    # Check if forecast model exists
    query = "SHOW MODELS"
    rc, rows = _dbx_sql_query(query)
    if rc == 0:
        model_names = [row.get("name", "") for row in rows]
        if forecast_model_name in model_names:
            return GateResult(
                success=True,
                message=f"Forecast model '{forecast_model_name}' is ready",
            )
        return GateResult(
            success=False,
            message=f"Forecast model '{forecast_model_name}' not found",
        )
    return GateResult(success=False, message="Failed to list ML models")


def check_dbx_app_deployed(project_root: Path) -> GateResult:
    """Gate: Databricks App (Streamlit) is deployed and accessible."""
    try:
        manifest = _dbx_load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    dbx_section = getattr(manifest, "databricks", None)
    app_name = getattr(dbx_section, "app_name", None) if dbx_section else None
    if not app_name:
        return GateResult(
            success=False,
            message="Databricks App name not configured in manifest",
        )

    # Check if app exists
    query = "SHOW APPS"
    rc, rows = _dbx_sql_query(query)
    if rc == 0:
        app_names = [row.get("name", "") for row in rows]
        if app_name in app_names:
            return GateResult(
                success=True,
                message=f"Databricks App '{app_name}' is deployed",
            )
        return GateResult(
            success=False,
            message=f"Databricks App '{app_name}' not found",
        )
    return GateResult(success=False, message="Failed to list Databricks Apps")


def check_dbx_all(project_root: Path) -> GateResult:
    """Run all Databricks-specific checks sequentially."""
    dbx_checks = [
        ("lakebase_reachable", check_lakebase_reachable),
        ("uc_sync_healthy", check_uc_sync_healthy),
        ("genie_space_active", check_genie_space_active),
        ("vector_index_ready", check_vector_index_ready),
        ("forecast_ready", check_dbx_forecast_ready),
        ("app_deployed", check_dbx_app_deployed),
    ]
    failures: list[str] = []
    for name, fn in dbx_checks:
        result = fn(project_root)
        if not result.success:
            failures.append(f"{name}: {result.message}")

    if failures:
        return GateResult(
            success=False,
            message=f"{len(failures)} Databricks check(s) failed:\n"
            + "\n".join(f"  - {f}" for f in failures),
        )
    return GateResult(success=True, message="All Databricks checks passed")
