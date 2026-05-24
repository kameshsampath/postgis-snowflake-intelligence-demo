"""Gate checks for streetlights demo progression.

Provides pre-step validation functions that return GateResult objects
indicating success/failure with a descriptive message.

CLI Usage:
    uv run gate --step setup --action check
    uv run gate --step step-1 --prior-step setup --action check
    uv run gate --step step-2 --action start --desc "Snowflake Postgres Instance"
    uv run gate --step step-2 --action complete
    uv run gate --step step-2 --action reset
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from scripts._manifest import (
    STEP_CHAIN,
    Manifest,
    find_project_root,
    remove_step,
    update_step,
)
from scripts._manifest import (
    load as load_manifest,
)
from scripts.generate_ddl import generate_iceberg_ddl, get_dry_run_step3


@dataclass(frozen=True)
class GateResult:
    """Result of a gate check."""

    success: bool
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _snow_json(query: str, connection: str) -> tuple[int, list[dict]]:
    """Run a snow sql query and return (returncode, list-of-row-dicts)."""
    import json as _json

    r = subprocess.run(
        [
            "snow",
            "sql",
            "-q",
            query,
            "-c",
            connection,
            "--format",
            "json",
            "--enable-templating",
            "STANDARD",
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return r.returncode, []
    try:
        return 0, _json.loads(r.stdout)
    except Exception:
        return 0, []


def _get_current_ip() -> str:
    """Detect current public IP address."""
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json", timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data["ip"]
    except Exception:
        # Fallback
        try:
            with urllib.request.urlopen("https://ifconfig.me/ip", timeout=5) as resp:
                return resp.read().decode().strip()
        except Exception:
            return ""


def _mask_ip(ip: str) -> str:
    """Mask last two octets for display: 192.168.1.2 → 192.168.*.*"""
    parts = ip.split(".")
    return f"{parts[0]}.{parts[1]}.*.*" if len(parts) == 4 else "[ip hidden]"


def _get_pg_allowed_ips(instance: str, connection: str | None = None) -> list[str]:
    """Get allowed IPs from PG instance network policy via DESCRIBE."""
    import re

    if not connection:
        return []
    query = f"DESCRIBE POSTGRES INSTANCE {instance}"
    rc, rows = _snow_json(query, connection)
    if rc != 0:
        return []
    # Extract IP-like patterns from the describe output
    ips: list[str] = []
    for row in rows:
        for v in row.values():
            ips.extend(re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?", str(v)))
    return ips


def _pg_ping(manifest: Manifest) -> bool:
    """Check if PG instance is reachable via psql SELECT 1.

    Uses PGSERVICE (from .envrc/direnv) or falls back to explicit host/user.
    The $snowflake-postgres skill manages ~/.pg_service.conf + ~/.pgpass.
    """
    instance = manifest.demo.pg_instance

    # Preferred: use pg_service from manifest (NOT env var)
    pg_service = manifest.demo.pg_service or instance
    try:
        result = subprocess.run(
            ["psql", f"service={pg_service}", "-c", "SELECT 1"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: explicit host/user from manifest
    pg_host = manifest.demo.pg_host
    pg_user = manifest.demo.pg_user
    if pg_host and pg_user:
        try:
            result = subprocess.run(
                [
                    "psql",
                    "-h",
                    pg_host,
                    "-U",
                    pg_user,
                    "-d",
                    "streetlights",
                    "-c",
                    "SELECT 1",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                env={**os.environ, "PGCONNECT_TIMEOUT": "10"},
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # Last resort: verify instance exists via Snowflake SQL
    query = f"SHOW POSTGRES INSTANCES LIKE '{instance}'"
    rc, rows = _snow_json(query, manifest.snowflake.connection)
    return rc == 0 and any(r.get("name", "").lower() == instance.lower() for r in rows)


def _cld_table_count(cld_db: str, connection: str | None = None) -> int:
    """Return table count in CLD database."""
    if not connection:
        raise Exception(f"CLD database {cld_db} does not exist or is not accessible")
    query = f"SELECT COUNT(*) FROM {cld_db}.INFORMATION_SCHEMA.TABLES"
    rc, rows = _snow_json(query, connection)
    if rc != 0:
        raise Exception(f"CLD database {cld_db} does not exist or is not accessible")
    try:
        return int(rows[0]["COUNT(*)"]) if rows else 0
    except (KeyError, ValueError):
        return 0


def _get_account_params(connection: str | None = None) -> dict[str, bool]:
    """Get account parameters related to Snowflake Postgres."""
    params = {}
    if not connection:
        return params
    for param in ["ENABLE_SNOWFLAKE_POSTGRES", "ENABLE_POSTGRES_HIDDEN_EXTERNAL_VOLUME"]:
        query = f"SHOW PARAMETERS LIKE '{param}' IN ACCOUNT"
        rc, rows = _snow_json(query, connection)
        params[param] = rc == 0 and any(r.get("value", "").lower() == "true" for r in rows)
    return params


# ---------------------------------------------------------------------------
# Gate check functions
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


def check_env_sync(project_root: Path) -> GateResult:
    """Gate: .env is in sync with manifest (no drift).

    Manifest is the source of truth. If .env has stale values,
    warn the user to re-run setup or regenerate.
    """
    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    env_path = project_root / ".env"
    if not env_path.exists():
        return GateResult(
            success=False,
            message=".env not found — run `$streetlights-demo setup` to generate it",
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


def check_pg_reachable(project_root: Path) -> GateResult:
    """Gate: PG instance responds to psql connection check."""
    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    instance = manifest.demo.pg_instance
    if _pg_ping(manifest):
        return GateResult(success=True, message=f"PG instance '{instance}' is reachable")
    return GateResult(success=False, message=f"PG instance '{instance}' is not reachable")


def check_cld_healthy(project_root: Path) -> GateResult:
    """Gate: warehouse exists + CLD DB exists + table count > 0."""
    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    connection = manifest.snowflake.connection
    warehouse = manifest.demo.warehouse

    # Check warehouse exists (use JSON format for reliable parsing)
    wh_query = f"SHOW WAREHOUSES LIKE '{warehouse}'"
    wh_rc, wh_rows = _snow_json(wh_query, connection)
    if wh_rc != 0:
        return GateResult(success=False, message="Could not query warehouses")
    wh_exists = any(r.get("name", "").upper() == warehouse.upper() for r in wh_rows)
    if not wh_exists:
        return GateResult(
            success=False,
            message=f"Warehouse '{warehouse}' not found — re-run Step 4 setup (01_setup.sql)",
        )

    cld_db = manifest.demo.cld_database
    try:
        count = _cld_table_count(cld_db, connection)
    except Exception as e:
        return GateResult(success=False, message=f"CLD database error: {e}")

    if count > 0:
        return GateResult(
            success=True, message=f"CLD healthy: {count} tables found, warehouse present"
        )
    return GateResult(success=False, message="CLD has 0 tables — propagation may not be complete")


def check_account_params(project_root: Path) -> GateResult:
    """Gate: required account params are set."""
    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")
    params = _get_account_params(manifest.snowflake.connection)
    if params.get("ENABLE_SNOWFLAKE_POSTGRES"):
        return GateResult(success=True, message="Account params enabled")
    return GateResult(
        success=False,
        message="Required account param ENABLE_SNOWFLAKE_POSTGRES is not enabled",
    )


def check_snowflake_connection(project_root: Path) -> GateResult:
    """Gate: Snowflake CLI connection from manifest works."""
    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    connection = manifest.snowflake.connection or "default"
    rc, rows = _snow_json("SELECT CURRENT_ACCOUNT()", connection)
    if rc == 0:
        return GateResult(
            success=True,
            message=f"Snowflake connection '{connection}' is valid",
        )
    return GateResult(
        success=False,
        message=f"Snowflake connection '{connection}' failed",
    )


def check_pg_network_access(project_root: Path) -> GateResult:
    """Gate: current IP is in PG instance's network policy.

    Detects IP mismatch when user moves networks (WiFi, VPN, etc.).
    Returns the current IP and allowed IPs for the skill to offer a fix.
    """
    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    instance = manifest.demo.pg_instance

    # Get current public IP
    current_ip = _get_current_ip()
    if not current_ip:
        return GateResult(
            success=False,
            message="Could not detect current public IP. Check internet connectivity.",
        )

    # Get allowed IPs from PG instance
    allowed_ips = _get_pg_allowed_ips(instance, manifest.snowflake.connection)
    if not allowed_ips:
        # Can't determine policy — fall back to connectivity check
        if _pg_ping(manifest):
            return GateResult(
                success=True,
                message=f"PG reachable (current IP: {_mask_ip(current_ip)}, policy IPs unknown)",
            )
        return GateResult(
            success=False,
            message=(
                f"PG unreachable. Current IP: {_mask_ip(current_ip)}. "
                f"Could not read network policy — IP may not be allowed."
            ),
        )

    # Check if current IP is in the allowed list (exact match or CIDR prefix)
    ip_allowed = any(
        current_ip == allowed.rstrip("/32") or current_ip.startswith(allowed.split("/")[0])
        for allowed in allowed_ips
    )

    if ip_allowed:
        return GateResult(
            success=True,
            message=f"Current IP {_mask_ip(current_ip)} is in PG network policy",
        )

    return GateResult(
        success=False,
        message=(
            f"IP MISMATCH: Your current IP ({_mask_ip(current_ip)}) is NOT in the "
            f"PG instance network policy.\n"
            f"Allowed IPs: {', '.join([_mask_ip(ip) for ip in allowed_ips])}\n"
            f"You likely switched networks. "
            f"Run `$snowflake-postgres` to update the network policy."
        ),
    )


# ---------------------------------------------------------------------------
# Step-specific verification checks
# ---------------------------------------------------------------------------


def _check_csv_files(project_root: Path) -> GateResult:
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
        return GateResult(
            success=False,
            message=f"Missing CSV files in data/: {', '.join(missing)}",
        )
    return GateResult(success=True, message=f"All {len(expected)} CSV files present in data/")


# ---------------------------------------------------------------------------
# Template name detection — mirrors _location.py without importing it
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


def _is_template_name(name: str) -> bool:
    """Return True when name matches the two-word Prefix Suffix template pattern."""
    parts = name.split()
    return (
        len(parts) == 2
        and parts[0] in _TEMPLATE_NAME_PREFIXES
        and parts[1] in _TEMPLATE_NAME_SUFFIXES
    )


def _check_csv_neighborhood_names(project_root: Path) -> GateResult:
    """Verify street_lights.csv has at least one non-template neighborhood name.

    If every neighborhood is a generated template (e.g. "North District"), the
    OpenStreetMap lookup likely failed silently during generation. The user should
    re-run ``uv run generate`` to retry.
    """
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

    if all(_is_template_name(n) for n in names):
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


def _check_step1_complete(project_root: Path) -> GateResult:
    """Verify step-1: CSV files exist and contain real neighborhood names."""
    result = _check_csv_files(project_root)
    if not result.success:
        return result
    return _check_csv_neighborhood_names(project_root)


def _check_pg_tables(project_root: Path) -> GateResult:
    """Verify PG tables have rows via psql."""
    # Pre-flight: generate DDL if missing (user may not have run generate yet)
    ddl_path = project_root / "init" / "02_create_iceberg_tables.sql"
    if not ddl_path.exists():
        generate_iceberg_ddl(output_path=ddl_path)

    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    instance = manifest.demo.pg_instance
    pg_service = manifest.demo.pg_service or instance

    query = (
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = 'streetlights' AND table_type = 'FOREIGN'"
    )
    try:
        result = subprocess.run(
            ["psql", f"service={pg_service}", "-t", "-c", query],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            count = int(result.stdout.strip())
            if count > 0:
                return GateResult(success=True, message=f"PG has {count} tables with data")
            return GateResult(success=False, message="PG has no tables — load data first")
        return GateResult(
            success=False, message=f"psql query failed: {result.stderr.strip()[:200]}"
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
        return GateResult(success=False, message=f"PG table check failed: {e}")


def _check_semantic_view(project_root: Path) -> GateResult:
    """Verify semantic view exists and YAML primary_key columns are valid identifiers."""
    import re as _re

    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    connection = manifest.snowflake.connection or "default"
    # Semantic view is created in the regular database (CLD is read-only)
    database = manifest.demo.database
    query = f"SHOW SEMANTIC VIEWS IN DATABASE {database}"
    rc, rows = _snow_json(query, connection)
    if rc != 0:
        return GateResult(success=False, message="SHOW SEMANTIC VIEWS failed")
    if not rows:
        return GateResult(success=False, message="No semantic views found in database")

    # Build FQN for YAML validation
    row = rows[0]
    db_name = row.get("database_name", database)
    schema_name = row.get("schema_name", "PUBLIC")
    view_name = row.get("name", "STREETLIGHTS_SEMANTIC_VIEW")
    fqn = f"{db_name}.{schema_name}.{view_name}"

    # Validate YAML: primary_key columns must not be quoted (e.g., '"id"' is invalid)
    yaml_query = f"SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('{fqn}') AS YAML_CONTENT"
    yaml_rc, yaml_rows = _snow_json(yaml_query, connection)
    if yaml_rc != 0 or not yaml_rows:
        return GateResult(
            success=False,
            message=f"Could not read YAML from semantic view {fqn}",
        )

    yaml_str = str(list(yaml_rows[0].values())[0]) if yaml_rows else ""
    # Detect quoted primary_key columns: pattern "- '"id"'" under primary_key.columns
    if _re.search(r"primary_key:.*?columns:.*?- '\"", yaml_str, _re.DOTALL):
        return GateResult(
            success=False,
            message=(
                f"Semantic view YAML has quoted primary_key columns (e.g. '\"id\"'). "
                f"Redeploy {fqn} with unquoted PRIMARY KEY identifiers."
            ),
        )

    return GateResult(
        success=True,
        message=f"Semantic view found and YAML primary_key columns are valid ({fqn})",
    )


def _check_cortex_search(project_root: Path) -> GateResult:
    """Verify Cortex Search Service exists."""
    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    connection = manifest.snowflake.connection or "default"
    database = manifest.demo.database
    query = f"SHOW CORTEX SEARCH SERVICES IN DATABASE {database}"
    rc, rows = _snow_json(query, connection)
    if rc == 0 and len(rows) > 0:
        return GateResult(success=True, message="Cortex Search Service found")
    if rc == 0:
        return GateResult(success=False, message="No Cortex Search Services found")
    return GateResult(success=False, message="SHOW CORTEX SEARCH SERVICES failed")


def _check_agent(project_root: Path) -> GateResult:
    """Verify Intelligence Agent exists."""
    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    connection = manifest.snowflake.connection or "default"
    database = manifest.demo.database
    query = f"SHOW AGENTS IN DATABASE {database}"
    rc, rows = _snow_json(query, connection)
    if rc == 0 and len(rows) > 0:
        return GateResult(success=True, message="Intelligence Agent found")
    if rc == 0:
        return GateResult(success=False, message="No Agents found in database")
    return GateResult(success=False, message="SHOW AGENTS failed")


def _check_forecast(project_root: Path) -> GateResult:
    """Verify ML Forecast model exists."""
    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    connection = manifest.snowflake.connection or "default"
    database = manifest.demo.database
    query = f"SHOW SNOWFLAKE.ML.FORECAST IN DATABASE {database}"
    rc, rows = _snow_json(query, connection)
    if rc == 0 and len(rows) > 0:
        return GateResult(success=True, message="ML Forecast model found")
    if rc == 0:
        return GateResult(success=False, message="No Forecast models found")
    return GateResult(success=False, message="SHOW FORECAST failed")


def _check_streamlit(project_root: Path) -> GateResult:
    """Verify Streamlit app exists."""
    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    connection = manifest.snowflake.connection or "default"
    database = manifest.demo.database
    query = f"SHOW STREAMLITS IN DATABASE {database}"
    rc, rows = _snow_json(query, connection)
    if rc == 0 and len(rows) > 0:
        return GateResult(success=True, message="Streamlit app found")
    if rc == 0:
        return GateResult(success=False, message="No Streamlit apps found")
    return GateResult(success=False, message="SHOW STREAMLITS failed")


def _check_all(project_root: Path) -> GateResult:
    """Run ALL checks sequentially for final validation."""
    checks = [
        ("manifest", check_manifest),
        ("csv_files", _check_csv_files),
        ("pg_reachable", check_pg_reachable),
        ("pg_tables", _check_pg_tables),
        ("cld_healthy", check_cld_healthy),
        ("semantic_view", _check_semantic_view),
        ("cortex_search", _check_cortex_search),
        ("agent", _check_agent),
        ("forecast", _check_forecast),
        ("streamlit", _check_streamlit),
    ]
    failures: list[str] = []
    for name, fn in checks:
        result = fn(project_root)
        if not result.success:
            failures.append(f"{name}: {result.message}")

    if failures:
        return GateResult(
            success=False,
            message=f"{len(failures)} check(s) failed:\n"
            + "\n".join(f"  - {f}" for f in failures),
        )
    return GateResult(success=True, message="All checks passed — demo fully operational")


# Step verification mapping
STEP_CHECKS: dict[str, callable] = {
    "setup": check_manifest,
    "step-1": _check_step1_complete,
    "step-2": check_pg_reachable,
    "step-3": _check_pg_tables,
    "step-4": check_cld_healthy,
    "step-5": _check_semantic_view,
    "step-6": _check_cortex_search,
    "step-7": _check_agent,
    "step-8": _check_forecast,
    "step-9": _check_streamlit,
    "step-10": _check_all,
}

STEP_DESCRIPTIONS: dict[str, str] = {
    "setup": "Initializing streetlights demo",
    "step-1": "Generating synthetic data",
    "step-2": "Creating Snowflake Postgres instance",
    "step-3": "Creating schema and loading data",
    "step-4": "Creating Catalog Integration + CLD",
    "step-5": "Creating Semantic View",
    "step-6": "Creating Cortex Search service",
    "step-7": "Creating Intelligence Agent",
    "step-8": "Training ML Forecast model",
    "step-9": "Deploying SiS app",
    "step-10": "Validating end-to-end demo",
}


# ---------------------------------------------------------------------------
# Dry-run: show execution plan per step
# ---------------------------------------------------------------------------


def _dry_run(project_root: Path, step: str) -> None:
    """Print the execution plan for a given step without running anything."""
    try:
        manifest = load_manifest(project_root)
    except FileNotFoundError:
        print("ERROR: manifest not found — run setup first")
        raise SystemExit(1)

    prefix = manifest.demo.prefix
    cld_database = manifest.demo.cld_database
    warehouse = manifest.demo.warehouse
    pg_instance = manifest.demo.pg_instance
    connection = manifest.snowflake.connection
    role = manifest.snowflake.role

    if step == "step-2":
        print("Step 2: Snowflake Postgres Instance")
        print("=" * 40)
        print()
        print(f"  PG Instance:     {pg_instance}")
        print(f"  Managed Storage: {prefix}_pg_store (auto-created)")
        print("  Database:        postgres (default)")
        print(f"  Warehouse:       {warehouse}")
        print()
        print("Actions:")
        print("  1. Create Snowflake Postgres instance")
        print("  2. Configure network policy (add current IP)")
        print("  3. Wait for instance to be READY")

    elif step == "step-3":
        print(get_dry_run_step3())

    elif step == "step-4":
        print("Step 4: Catalog Integration + CLD")
        print("=" * 40)
        print()
        print(f"  Catalog Integration: {prefix}_cat_int")
        print(f"  CLD Database:        {cld_database}")
        print(f"  Source PG Instance:  {pg_instance}")
        print()
        print("Actions:")
        print("  1. Create catalog integration")
        print(f"  2. CREATE DATABASE {cld_database} ... LINKED_CATALOG = TRUE")
        print("  3. Wait ~30s for CLD propagation")
        print("  4. Verify table count > 0")

    elif step == "step-5":
        print("Step 5: Semantic View")
        print("=" * 40)
        print()
        print(f"  Database: {cld_database}")
        print("  DDL source: snowflake/02_semantic_view.sql")
        print()
        print("Actions:")
        print("  1. Generate semantic view DDL from table schemas")
        print("  2. Execute DDL in Snowflake")
        print()
        print("  File:    snowflake/02_semantic_view.sql")
        print("  Command: snow sql -f snowflake/02_semantic_view.sql \\")
        print(
            f'             -D "PREFIX={prefix.upper()}" -c {connection} --enable-templating STANDARD'  # noqa: E501
        )

    elif step == "step-6":
        print("Step 6: Cortex Search Service")
        print("=" * 40)
        print()
        print(f"  Database: {cld_database}")
        print(f"  Warehouse: {warehouse}")
        print()
        print("Actions:")
        print("  1. Create Cortex Search service on maintenance data")
        print("  2. Verify service is active")
        print()
        print("  File:    snowflake/03_cortex_search.sql")
        print("  Command: snow sql -f snowflake/03_cortex_search.sql \\")
        print(
            f'             -D "PREFIX={prefix.upper()}" -c {connection} --enable-templating STANDARD'  # noqa: E501
        )

    elif step == "step-7":
        print("Step 7: Intelligence Agent")
        print("=" * 40)
        print()
        print(f"  Database: {cld_database}")
        print()
        print("Actions:")
        print("  1. Create Intelligence Agent with semantic view + search")
        print("  2. Verify agent responds to test query")
        print()
        print("  File:    snowflake/04_intelligence_agent.sql")
        print("  Command: snow sql -f snowflake/04_intelligence_agent.sql \\")
        print(f'             -D "PREFIX={prefix.upper()}" -D "ROLE={role}" \\')
        print(f"             -c {connection} --enable-templating STANDARD")

    elif step == "step-8":
        print("Step 8: ML Forecast Model")
        print("=" * 40)
        print()
        print(f"  Database: {cld_database}")
        print(f"  Warehouse: {warehouse} (resized MEDIUM during training, XSMALL after)")
        print()
        print("Actions:")
        print("  1. Grant CREATE VIEW + CREATE FORECAST on schema (as ACCOUNTADMIN)")
        print("  2. Resize warehouse to MEDIUM")
        print("  3. Create energy_daily_vw (with lat/lng/neighborhood/status)")
        print("  4. Train SNOWFLAKE.ML.FORECAST on energy_consumption (background)")
        print("  5. Resize warehouse back to XSMALL (auto, after training)")
        print()
        print("  File:    snowflake/05_ml_forecast.sql")
        print("  Command: snow sql -f snowflake/05_ml_forecast.sql \\")
        print(f'             -D "PREFIX={prefix.upper()}" -D "ROLE={role}" \\')
        print(
            f"             -c {connection} --enable-templating STANDARD"  # noqa: E501
        )

    elif step == "step-9":
        print("Step 9: Streamlit App")
        print("=" * 40)
        print()
        print(f"  Database: {cld_database}")
        print(f"  Warehouse: {warehouse}")
        print()
        print("Actions:")
        print("  1. Deploy Streamlit-in-Snowflake app")
        print("  2. Verify app is accessible")
        print()
        print("  Deployment: handled by $developing-with-streamlit-in-snowflake skill")
        print("  Source dir: app/  Entry point: app/Home.py")

    else:
        print(f"No dry-run available for '{step}'")
        raise SystemExit(1)

    raise SystemExit(0)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point for the gate checker."""
    parser = argparse.ArgumentParser(
        description="Streetlights demo gate checker and step state manager"
    )
    parser.add_argument(
        "--step",
        required=True,
        help="Step identifier (setup, step-1, step-2, ..., step-10)",
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["check", "verify", "start", "complete", "reset", "dry-run"],
        help="Action to perform",
    )
    parser.add_argument(
        "--prior-step",
        help="If provided, verify prior step is COMPLETE before checking current",
    )
    parser.add_argument(
        "--desc",
        help="Description for start action",
    )

    args = parser.parse_args()

    try:
        project_root = find_project_root()
    except FileNotFoundError as e:
        print(f"BLOCK: {e}")
        raise SystemExit(1)

    # --- Action: reset ---
    if args.action == "reset":
        remove_step(project_root, args.step)
        print(f"OK: {args.step} reset")
        raise SystemExit(0)

    # --- Action: dry-run ---
    if args.action == "dry-run":
        _dry_run(project_root, args.step)

    # --- Action: start ---
    if args.action == "start":
        update_step(project_root, args.step, "IN_PROGRESS", desc=args.desc or "")
        print(f"OK: {args.step} marked IN_PROGRESS")
        raise SystemExit(0)

    # --- Action: complete ---
    if args.action == "complete":
        update_step(project_root, args.step, "COMPLETE")
        print(f"OK: {args.step} marked COMPLETE")
        raise SystemExit(0)

    # --- Action: check ---
    cache_ttl = 3600  # 1 hour

    # Full chain verification: walk backwards from --prior-step to build the
    # ancestor chain, then verify each ancestor (skip if fresh, re-verify if stale).
    if args.prior_step:
        # Build chain: [setup, step-1, ..., prior_step]
        chain: list[str] = []
        current = args.prior_step
        while current is not None:
            chain.append(current)
            current = STEP_CHAIN.get(current)
        chain.reverse()  # Now oldest-first: [setup, step-1, ..., prior_step]

        try:
            manifest = load_manifest(project_root)
            steps = manifest.demo.steps
        except FileNotFoundError:
            print(f"BLOCK: manifest not found — cannot verify chain for {args.prior_step}")
            raise SystemExit(1)

        for ancestor in chain:
            ancestor_state = steps.get(ancestor)
            ancestor_check_fn = STEP_CHECKS.get(ancestor)

            if ancestor_state and ancestor_state.status == "COMPLETE":
                # Check freshness
                completed_at = ancestor_state.completed_at
                is_fresh = False
                if completed_at:
                    try:
                        completed_time = datetime.fromisoformat(completed_at)
                        elapsed = (datetime.now(UTC) - completed_time).total_seconds()
                        is_fresh = elapsed < cache_ttl
                    except (ValueError, TypeError):
                        pass

                if is_fresh:
                    continue  # Fresh — trust it

                # Stale — re-verify
                if ancestor_check_fn:
                    result = ancestor_check_fn(project_root)
                    if result.success:
                        update_step(
                            project_root,
                            ancestor,
                            "COMPLETE",
                            desc=STEP_DESCRIPTIONS.get(ancestor, ""),
                        )
                        # Reload manifest for next iteration
                        manifest = load_manifest(project_root)
                        steps = manifest.demo.steps
                        continue
                    else:
                        print(
                            f"BLOCK: chain step {ancestor} was COMPLETE"
                            f" but re-verification failed - {result.message}"
                        )
                        raise SystemExit(1)
                else:
                    continue  # No check fn, trust cached status
            else:
                # Not COMPLETE — try to backfill
                if ancestor_check_fn:
                    result = ancestor_check_fn(project_root)
                    if result.success:
                        update_step(
                            project_root,
                            ancestor,
                            "COMPLETE",
                            desc=STEP_DESCRIPTIONS.get(ancestor, ""),
                        )
                        # Reload manifest for next iteration
                        manifest = load_manifest(project_root)
                        steps = manifest.demo.steps
                        continue
                    else:
                        print(f"BLOCK: chain step {ancestor} not complete" f" - {result.message}")
                        raise SystemExit(1)
                else:
                    print(f"BLOCK: chain step {ancestor} not complete")
                    raise SystemExit(1)

    # --- Action: check (readiness) ---
    # Chain passed (or no chain needed). Now determine if the current step is ready.
    # "check" does NOT run the current step's own verifier — that's what "verify" does.
    if args.action == "check":
        try:
            manifest = load_manifest(project_root)
            step_state = manifest.demo.steps.get(args.step)
        except FileNotFoundError:
            step_state = None

        if step_state and step_state.status == "COMPLETE":
            # Already complete — check freshness
            completed_at = step_state.completed_at
            if completed_at:
                try:
                    completed_time = datetime.fromisoformat(completed_at)
                    elapsed = (datetime.now(UTC) - completed_time).total_seconds()
                    if elapsed < cache_ttl:
                        print(f"PASS: {args.step} already complete (cached)")
                        raise SystemExit(0)
                except (ValueError, TypeError):
                    pass

            # Stale — re-verify if we have a check function
            check_fn = STEP_CHECKS.get(args.step)
            if check_fn:
                result = check_fn(project_root)
                if result.success:
                    update_step(
                        project_root,
                        args.step,
                        "COMPLETE",
                        desc=STEP_DESCRIPTIONS.get(args.step, ""),
                    )
                    print(f"PASS: {args.step} already complete (re-verified)")
                    raise SystemExit(0)
                else:
                    print(
                        f"BLOCK: {args.step} was COMPLETE but re-verification"
                        f" failed - {result.message}"
                    )
                    raise SystemExit(1)
            else:
                print(f"PASS: {args.step} already complete (cached, no re-check available)")
                raise SystemExit(0)

        # Step NOT complete — it's ready to run (chain already validated above)
        print(f"PASS: {args.step} ready")
        raise SystemExit(0)

    # --- Action: verify (post-execution verification) ---
    # Runs the current step's own verifier to confirm execution succeeded.
    if args.action == "verify":
        try:
            manifest = load_manifest(project_root)
            step_state = manifest.demo.steps.get(args.step)
        except FileNotFoundError:
            step_state = None

        if step_state and step_state.status == "COMPLETE":
            # Already complete — check freshness
            completed_at = step_state.completed_at
            if completed_at:
                try:
                    completed_time = datetime.fromisoformat(completed_at)
                    elapsed = (datetime.now(UTC) - completed_time).total_seconds()
                    if elapsed < cache_ttl:
                        print(f"PASS: {args.step} verified (cached)")
                        raise SystemExit(0)
                except (ValueError, TypeError):
                    pass

            # Stale — re-verify
            check_fn = STEP_CHECKS.get(args.step)
            if check_fn:
                result = check_fn(project_root)
                if result.success:
                    update_step(
                        project_root,
                        args.step,
                        "COMPLETE",
                        desc=STEP_DESCRIPTIONS.get(args.step, ""),
                    )
                    print(f"PASS: {args.step} re-verified")
                    raise SystemExit(0)
                else:
                    print(
                        f"BLOCK: {args.step} was COMPLETE but re-verification"
                        f" failed - {result.message}"
                    )
                    raise SystemExit(1)
            else:
                print(f"PASS: {args.step} verified (cached, no re-check available)")
                raise SystemExit(0)

        # Section MISSING or status != COMPLETE — run step-specific verify
        check_fn = STEP_CHECKS.get(args.step)
        if not check_fn:
            print(f"BLOCK: unknown step '{args.step}'")
            raise SystemExit(1)

        result = check_fn(project_root)
        if result.success:
            # Backfill as COMPLETE
            update_step(
                project_root,
                args.step,
                "COMPLETE",
                desc=STEP_DESCRIPTIONS.get(args.step, ""),
            )
            print(f"PASS: {args.step} backfilled")
            raise SystemExit(0)
        else:
            print(f"BLOCK: {args.step} not complete - {result.message}")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
