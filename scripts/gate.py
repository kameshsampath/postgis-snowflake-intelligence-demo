"""Gate checks for streetlights demo progression.

Provides pre-step validation functions that return GateResult objects
indicating success/failure with a descriptive message.
"""

from __future__ import annotations

import json
import subprocess
import tomllib
import urllib.request
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


def _get_pg_allowed_ips(instance: str) -> list[str]:
    """Get allowed IPs from PG instance network policy via DESCRIBE."""
    import re

    result = subprocess.run(
        ["snow", "sql", "-q", f"DESCRIBE POSTGRES INSTANCE {instance}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    # Extract IP-like patterns from the describe output
    ips = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?", result.stdout)
    return ips


def _pg_ping(manifest: dict) -> bool:
    """Check if PG instance is reachable via psql SELECT 1.

    Uses PGSERVICE (from .envrc/direnv) or falls back to explicit host/user.
    The $snowflake-postgres skill manages ~/.pg_service.conf + ~/.pgpass.
    """
    import os

    instance = manifest["demo"]["pg_instance"]

    # Preferred: use PGSERVICE (set by .envrc from manifest)
    pg_service = os.environ.get("PGSERVICE", instance)
    try:
        result = subprocess.run(
            ["psql", f"service={pg_service} connect_timeout=10", "-c", "SELECT 1"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: explicit host/user from manifest
    pg_host = manifest.get("demo", {}).get("pg_host", "")
    pg_user = manifest.get("demo", {}).get("pg_user", "")
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
    result = subprocess.run(
        ["snow", "sql", "-q", f"SHOW POSTGRES INSTANCES LIKE '{instance}'"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and instance.lower() in result.stdout.lower()


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


def check_env_sync(project_root: Path) -> GateResult:
    """Gate: .env is in sync with manifest (no drift).

    Manifest is the source of truth. If .env has stale values,
    warn the user to re-run setup or regenerate.
    """
    try:
        manifest = _load_manifest(project_root)
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
    demo = manifest.get("demo", {})
    expected = {
        "PGSERVICE": demo.get("pg_service", demo.get("pg_instance", "")),
        "SNOWFLAKE_CONNECTION": manifest.get("snowflake", {}).get("connection", ""),
        "DEMO_PREFIX": manifest.get("project", {}).get("demo_resource_prefix", ""),
        "DEMO_WAREHOUSE": demo.get("warehouse", ""),
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
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    instance = manifest["demo"]["pg_instance"]
    if _pg_ping(manifest):
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


def check_snowflake_connection(project_root: Path) -> GateResult:
    """Gate: Snowflake CLI connection from manifest works."""
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    connection = manifest.get("snowflake", {}).get("connection", "default")
    result = subprocess.run(
        ["snow", "sql", "-q", "SELECT CURRENT_ACCOUNT()", "-c", connection],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return GateResult(
            success=True,
            message=f"Snowflake connection '{connection}' is valid",
        )
    return GateResult(
        success=False,
        message=f"Snowflake connection '{connection}' failed: {result.stderr.strip()[:200]}",
    )


def check_pg_network_access(project_root: Path) -> GateResult:
    """Gate: current IP is in PG instance's network policy.

    Detects IP mismatch when user moves networks (WiFi, VPN, etc.).
    Returns the current IP and allowed IPs for the skill to offer a fix.
    """
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    instance = manifest["demo"]["pg_instance"]

    # Get current public IP
    current_ip = _get_current_ip()
    if not current_ip:
        return GateResult(
            success=False,
            message="Could not detect current public IP. Check internet connectivity.",
        )

    # Get allowed IPs from PG instance
    allowed_ips = _get_pg_allowed_ips(instance)
    if not allowed_ips:
        # Can't determine policy — fall back to connectivity check
        if _pg_ping(instance):
            return GateResult(
                success=True,
                message=f"PG reachable (current IP: {current_ip}, policy IPs unknown)",
            )
        return GateResult(
            success=False,
            message=(
                f"PG unreachable. Current IP: {current_ip}. "
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
            message=f"Current IP {current_ip} is in PG network policy",
        )

    return GateResult(
        success=False,
        message=(
            f"IP MISMATCH: Your current IP ({current_ip}) is NOT in the "
            f"PG instance network policy.\n"
            f"Allowed IPs: {', '.join(allowed_ips)}\n"
            f"You likely switched networks. "
            f"Run `$snowflake-postgres` to update the network policy."
        ),
    )
