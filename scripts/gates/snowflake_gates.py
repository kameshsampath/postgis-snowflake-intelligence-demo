# Copyright 2025 Kamesh Sampath <kamesh.sampath@hotmail.com>
# SPDX-License-Identifier: Apache-2.0

"""Snowflake-specific gate checks for PostGIS Data Intelligence Demo.

Provides Snowflake-specific validation functions for the demo workflow.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from scripts._manifest import load as load_manifest
from scripts.gates.base_gates import GateResult


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


def _get_pg_allowed_ips(instance: str, connection: str | None = None) -> list[str]:
    """Get allowed IPs from PG instance network policy via DESCRIBE."""
    if not connection:
        return []
    query = f"DESCRIBE POSTGRES INSTANCE {instance}"
    rc, rows = _snow_json(query, connection)
    if rc != 0:
        return []
    # Extract IP-like patterns from the describe output
    import re

    ips: list[str] = []
    for row in rows:
        for v in row.values():
            ips.extend(re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?", str(v)))
    return ips


def _pg_ping(manifest: any) -> bool:
    """Check if PG instance is reachable via psql SELECT 1."""
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
    for param in [
        "ENABLE_SNOWFLAKE_POSTGRES",
        "ENABLE_POSTGRES_HIDDEN_EXTERNAL_VOLUME",
    ]:
        query = f"SHOW PARAMETERS LIKE '{param}' IN ACCOUNT"
        rc, rows = _snow_json(query, connection)
        params[param] = rc == 0 and any(r.get("value", "").lower() == "true" for r in rows)
    return params


# ---------------------------------------------------------------------------
# Snowflake gate checks
# ---------------------------------------------------------------------------


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


def check_pg_tables(project_root: Path) -> GateResult:
    """Verify PG tables have rows via psql."""
    from scripts.generate_ddl import generate_iceberg_ddl

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
            success=False,
            message=f"psql query failed: {result.stderr.strip()[:200]}",
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError) as e:
        return GateResult(success=False, message=f"PG table check failed: {e}")


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
            message=f"Warehouse '{warehouse}' not found — " f"re-run Step 4 setup (01_setup.sql)",
        )

    cld_db = manifest.demo.cld_database
    try:
        count = _cld_table_count(cld_db, connection)
    except Exception as e:
        return GateResult(success=False, message=f"CLD database error: {e}")

    if count > 0:
        return GateResult(
            success=True,
            message=f"CLD healthy: {count} tables found, warehouse present",
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


def check_pg_network_access(project_root: Path) -> GateResult:
    """Gate: current IP is in PG instance's network policy.

    Detects IP mismatch when user moves networks (WiFi, VPN, etc.).
    Returns the current IP and allowed IPs for the skill to offer a fix.
    """
    from scripts.gates.base_gates import get_current_ip, mask_ip

    try:
        manifest = load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    instance = manifest.demo.pg_instance

    # Get current public IP
    current_ip = get_current_ip()
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
                message=f"PG reachable (current IP: {mask_ip(current_ip)}, "
                f"policy IPs unknown)",
            )
        return GateResult(
            success=False,
            message=(
                f"PG unreachable. Current IP: {mask_ip(current_ip)}. "
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
            message=f"Current IP {mask_ip(current_ip)} is in PG network policy",
        )

    return GateResult(
        success=False,
        message=(
            f"IP MISMATCH: Your current IP ({mask_ip(current_ip)}) is NOT in the "
            f"PG instance network policy.\n"
            f"Allowed IPs: {', '.join([mask_ip(ip) for ip in allowed_ips])}\n"
            f"You likely switched networks. "
            f"Run `$snowflake-postgres` to update the network policy."
        ),
    )


def check_semantic_view(project_root: Path) -> GateResult:
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


def check_cortex_search(project_root: Path) -> GateResult:
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
