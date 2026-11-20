# Copyright 2025 Kamesh Sampath <kamesh.sampath@hotmail.com>
# SPDX-License-Identifier: Apache-2.0

"""Base gate checks and utilities for PostGIS Data Intelligence Demo.

Provides common gate checks and utilities used by both Snowflake and Databricks
implementations.
"""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from pathlib import Path

from scripts._manifest import load as load_manifest


@dataclass(frozen=True)
class GateResult:
    """Result of a gate check."""

    success: bool
    message: str


# ---------------------------------------------------------------------------
# IP utilities
# ---------------------------------------------------------------------------


def get_current_ip() -> str:
    """Detect current public IP address."""
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=5) as resp:
            import json

            data = json.loads(resp.read().decode())
            return data["ip"]
    except Exception:
        # Fallback
        try:
            with urllib.request.urlopen("https://ifconfig.me/ip", timeout=5) as resp:
                return resp.read().decode().strip()
        except Exception:
            return ""


def mask_ip(ip: str) -> str:
    """Mask last two octets for display: 192.168.1.2 -> 192.168.*.*"""
    parts = ip.split(".")
    return f"{parts[0]}.{parts[1]}.*.*" if len(parts) == 4 else "[ip hidden]"


# ---------------------------------------------------------------------------
# CSV validation utilities
# ---------------------------------------------------------------------------


_TEMPLATE_NAME_PREFIXES: frozenset[str] = frozenset(
    {
        "North",
        "South",
        "East",
        "West",
        "Central",
        "Upper",
        "Lower",
        "Old",
        "New",
        "Lake",
        "River",
        "Park",
        "Hill",
        "Oak",
        "Cedar",
        "Pine",
        "Maple",
        "Elm",
        "Harbor",
        "Bridge",
        "Market",
        "Garden",
    }
)

_TEMPLATE_NAME_SUFFIXES: frozenset[str] = frozenset(
    {
        "District",
        "Heights",
        "Square",
        "Village",
        "Quarter",
        "Commons",
        "Place",
        "Crossing",
        "Landing",
        "Point",
        "Green",
        "Park",
    }
)


def is_template_name(name: str) -> bool:
    """Return True when name matches the two-word Prefix Suffix template pattern."""
    parts = name.split()
    return (
        len(parts) == 2
        and parts[0] in _TEMPLATE_NAME_PREFIXES
        and parts[1] in _TEMPLATE_NAME_SUFFIXES
    )


def check_csv_files(project_root: Path) -> tuple[bool, str, list[str]]:
    """Verify 8 CSV files exist in data/ directory."""
    data_dir = project_root / "data"
    expected = [
        "demographics.csv",
        "energy_consumption.csv",
        "intent_log.csv",
        "light_sensors.csv",
        "maintenance_records.csv",
        "power_grid_zones.csv",
        "street_lights.csv",
        "weather_enrichment.csv",
    ]
    missing = [f for f in expected if not (data_dir / f).exists()]
    if missing:
        return False, f"Missing CSV files in data/: {', '.join(missing)}", missing
    return True, f"All {len(expected)} CSV files present in data/", []


def check_csv_neighborhood_names(project_root: Path) -> GateResult:
    """Verify street_lights.csv has at least one non-template neighborhood name."""
    import csv

    csv_path = project_root / "data" / "street_lights.csv"
    if not csv_path.exists():
        return GateResult(success=False, message="data/street_lights.csv not found")

    try:
        with csv_path.open(newline="") as f:
            reader = csv.DictReader(f)
            names = {row["neighborhood"] for row in reader if row.get("neighborhood")}
    except Exception as e:
        return GateResult(success=False, message=f"Cannot read street_lights.csv: {e}")

    if not names:
        return GateResult(
            success=False,
            message="street_lights.csv has no neighborhood values",
        )

    if all(is_template_name(n) for n in names):
        return GateResult(
            success=False,
            message=(
                "All neighborhood names are generated templates — OSM lookup likely "
                "failed. Re-run `uv run generate` to retry fetching real names."
            ),
        )

    return GateResult(
        success=True,
        message=f"Neighborhood names look real ({len(names)} unique values)",
    )


def check_step1_complete(project_root: Path) -> GateResult:
    """Verify step-1: CSV files exist and contain real neighborhood names."""
    result = check_csv_files(project_root)
    if not result[0]:
        return GateResult(success=False, message=result[1])
    return check_csv_neighborhood_names(project_root)


# ---------------------------------------------------------------------------
# Environment synchronization
# ---------------------------------------------------------------------------


def check_env_sync(project_root: Path) -> GateResult:
    """Gate: .env is in sync with manifest (no drift)."""
    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    env_path = project_root / ".env"
    if not env_path.exists():
        return GateResult(
            success=False,
            message=r"\.env not found — run `$streetlights-demo setup` to generate it",
        )

    # Parse .env (simple KEY=VALUE format)
    env_vars: dict[str, str] = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env_vars[key.strip()] = value.strip()

    # Check key values against manifest
    drift: list[str] = []
    expected = {
        "PGSERVICE": manifest.demo.pg_service or manifest.demo.pg_instance,
        "SNOWFLAKE_CONNECTION": manifest.snowflake.connection,
        "DEMO_PREFIX": manifest.demo.prefix,
        "DEMO_WAREHOUSE": manifest.demo.warehouse,
    }

    for key, manifest_val in expected.items():
        env_val = env_vars.get(key, "")
        if manifest_val and env_val and env_val != manifest_val:
            drift.append(f"{key}: .env='{env_val}' vs manifest='{manifest_val}'")

    if drift:
        return GateResult(
            success=False,
            message=(
                f".env is out of sync with manifest ({len(drift)} drifted):\n"
                + "\n".join(f"  - {d}" for d in drift)
                + "\nRe-run `$streetlights-demo setup` to regenerate."
            ),
        )

    return GateResult(success=True, message=".env is in sync with manifest")


# ---------------------------------------------------------------------------
# Manifest checks
# ---------------------------------------------------------------------------


def check_manifest(project_root: Path) -> GateResult:
    """Gate: manifest.toml exists and is parseable."""
    manifest_file = project_root / ".streetlights-demo" / "manifest.toml"
    if not manifest_file.exists():
        return GateResult(
            success=False,
            message="Manifest not found at .streetlights-demo/manifest.toml",
        )
    try:
        load_manifest(project_root)
        return GateResult(success=True, message="Manifest loaded successfully")
    except Exception as e:
        return GateResult(success=False, message=f"Manifest parse error: {e}")
