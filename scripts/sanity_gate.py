"""Sanity gate checks for post-step validation.

Verifies that infrastructure components are properly set up
after each step of the demo workflow.
"""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

from scripts.gate import GateResult


def _load_manifest(project_root: Path) -> dict:
    """Load manifest.toml from project_root/.streetlights-demo/."""
    manifest_file = project_root / ".streetlights-demo" / "manifest.toml"
    with open(manifest_file, "rb") as f:
        return tomllib.load(f)


def _semantic_view_exists(cld_db: str) -> bool:
    """Check if semantic view exists in Snowflake."""
    result = subprocess.run(
        ["snow", "sql", "-q", f'SHOW SEMANTIC VIEWS IN SCHEMA {cld_db}."streetlights"'],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and "semantic_view" in result.stdout.lower()


def _cortex_search_status(cld_db: str) -> str:
    """Get Cortex Search service status."""
    result = subprocess.run(
        ["snow", "sql", "-q", f'SHOW CORTEX SEARCH SERVICES IN SCHEMA {cld_db}."streetlights"'],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and "ACTIVE" in result.stdout.upper():
        return "ACTIVE"
    return "NOT_ACTIVE"


def _agent_accessible(cld_db: str) -> bool:
    """Check if Intelligence Agent is accessible."""
    result = subprocess.run(
        [
            "snow",
            "sql",
            "-q",
            f"SELECT SNOWFLAKE.CORTEX.AGENT('{cld_db}.streetlights.streetlights_agent',"
            f" 'How many streetlights are there?')",
        ],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _forecast_model_exists(cld_db: str) -> bool:
    """Check if FORECAST model exists."""
    result = subprocess.run(
        ["snow", "sql", "-q", f'SHOW SNOWFLAKE.ML.FORECAST IN SCHEMA {cld_db}."streetlights"'],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and "energy_forecast" in result.stdout.lower()


def check_semantic_view(project_root: Path) -> GateResult:
    """Sanity: Semantic View DDL succeeded."""
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    cld_db = manifest["demo"]["cld_database"]
    if _semantic_view_exists(cld_db):
        return GateResult(success=True, message="Semantic view exists")
    return GateResult(success=False, message="Semantic view not found")


def check_cortex_search(project_root: Path) -> GateResult:
    """Sanity: Cortex Search service is ACTIVE."""
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    cld_db = manifest["demo"]["cld_database"]
    status = _cortex_search_status(cld_db)
    if status == "ACTIVE":
        return GateResult(success=True, message="Cortex Search service is ACTIVE")
    return GateResult(success=False, message=f"Cortex Search service status: {status}")


def check_agent(project_root: Path) -> GateResult:
    """Sanity: Agent responds to test query."""
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    cld_db = manifest["demo"]["cld_database"]
    if _agent_accessible(cld_db):
        return GateResult(success=True, message="Agent is accessible")
    return GateResult(success=False, message="Agent not accessible or not found")


def check_forecast_model(project_root: Path) -> GateResult:
    """Sanity: FORECAST model is trained."""
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    cld_db = manifest["demo"]["cld_database"]
    if _forecast_model_exists(cld_db):
        return GateResult(success=True, message="Forecast model exists")
    return GateResult(success=False, message="Forecast model not found")
