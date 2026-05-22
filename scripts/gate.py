"""Gate checks for streetlights demo progression.

Provides pre-step validation functions that return GateResult objects
indicating success/failure with a descriptive message.

CLI Usage:
    python3 scripts/gate.py --step setup --action check
    python3 scripts/gate.py --step step-1 --prior-step setup --action check
    python3 scripts/gate.py --step step-2 --action start --desc "Snowflake Postgres Instance"
    python3 scripts/gate.py --step step-2 --action complete
    python3 scripts/gate.py --step step-2 --action reset
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import tomllib
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class GateResult:
    """Result of a gate check."""

    success: bool
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
        if _pg_ping(manifest):
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


# ---------------------------------------------------------------------------
# Step-specific verification checks
# ---------------------------------------------------------------------------


def _check_csv_files(project_root: Path) -> GateResult:
    """Verify 7 CSV files exist in data/ directory."""
    data_dir = project_root / "data"
    expected = [
        "demographics.csv",
        "energy_consumption.csv",
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


def _check_pg_tables(project_root: Path) -> GateResult:
    """Verify PG tables have rows via psql."""
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    instance = manifest["demo"]["pg_instance"]
    pg_service = os.environ.get("PGSERVICE", instance)

    query = (
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
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
    """Verify semantic view exists via snow sql."""
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    connection = manifest.get("snowflake", {}).get("connection", "default")
    cld_db = manifest["demo"]["cld_database"]
    result = subprocess.run(
        ["snow", "sql", "-q", f"SHOW SEMANTIC VIEWS IN DATABASE {cld_db}", "-c", connection],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and "semantic" in result.stdout.lower():
        return GateResult(success=True, message="Semantic view found")
    if result.returncode == 0:
        return GateResult(success=False, message="No semantic views found in CLD database")
    return GateResult(
        success=False, message=f"SHOW SEMANTIC VIEWS failed: {result.stderr.strip()[:200]}"
    )


def _check_cortex_search(project_root: Path) -> GateResult:
    """Verify Cortex Search Service exists."""
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    connection = manifest.get("snowflake", {}).get("connection", "default")
    cld_db = manifest["demo"]["cld_database"]
    result = subprocess.run(
        [
            "snow",
            "sql",
            "-q",
            f"SHOW CORTEX SEARCH SERVICES IN DATABASE {cld_db}",
            "-c",
            connection,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and "search" in result.stdout.lower():
        return GateResult(success=True, message="Cortex Search Service found")
    if result.returncode == 0:
        return GateResult(success=False, message="No Cortex Search Services found")
    return GateResult(
        success=False, message=f"SHOW CORTEX SEARCH SERVICES failed: {result.stderr.strip()[:200]}"
    )


def _check_agent(project_root: Path) -> GateResult:
    """Verify Intelligence Agent exists."""
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    connection = manifest.get("snowflake", {}).get("connection", "default")
    cld_db = manifest["demo"]["cld_database"]
    result = subprocess.run(
        ["snow", "sql", "-q", f"SHOW AGENTS IN DATABASE {cld_db}", "-c", connection],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and "agent" in result.stdout.lower():
        return GateResult(success=True, message="Intelligence Agent found")
    if result.returncode == 0:
        return GateResult(success=False, message="No Agents found in CLD database")
    return GateResult(success=False, message=f"SHOW AGENTS failed: {result.stderr.strip()[:200]}")


def _check_forecast(project_root: Path) -> GateResult:
    """Verify ML Forecast model exists."""
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    connection = manifest.get("snowflake", {}).get("connection", "default")
    cld_db = manifest["demo"]["cld_database"]
    result = subprocess.run(
        [
            "snow",
            "sql",
            "-q",
            f"SHOW SNOWFLAKE.ML.FORECAST IN DATABASE {cld_db}",
            "-c",
            connection,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and "forecast" in result.stdout.lower():
        return GateResult(success=True, message="ML Forecast model found")
    if result.returncode == 0:
        return GateResult(success=False, message="No Forecast models found")
    return GateResult(
        success=False, message=f"SHOW FORECAST failed: {result.stderr.strip()[:200]}"
    )


def _check_streamlit(project_root: Path) -> GateResult:
    """Verify Streamlit app exists."""
    try:
        manifest = _load_manifest(project_root)
    except Exception as e:
        return GateResult(success=False, message=f"Cannot load manifest: {e}")

    connection = manifest.get("snowflake", {}).get("connection", "default")
    cld_db = manifest["demo"]["cld_database"]
    result = subprocess.run(
        ["snow", "sql", "-q", f"SHOW STREAMLITS IN DATABASE {cld_db}", "-c", connection],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and "streamlit" in result.stdout.lower():
        return GateResult(success=True, message="Streamlit app found")
    if result.returncode == 0:
        return GateResult(success=False, message="No Streamlit apps found")
    return GateResult(
        success=False, message=f"SHOW STREAMLITS failed: {result.stderr.strip()[:200]}"
    )


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
    "step-1": _check_csv_files,
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
    "setup": "Initialize Streetlights Demo",
    "step-1": "Generate Synthetic Data",
    "step-2": "Snowflake Postgres Instance",
    "step-3": "Create Schema + Load Data",
    "step-4": "Catalog Integration + CLD",
    "step-5": "Create Semantic View",
    "step-6": "Create Cortex Search Service",
    "step-7": "Create Intelligence Agent",
    "step-8": "Train ML Forecast",
    "step-9": "Deploy SiS App",
    "step-10": "Validate & Demo",
}

# Ordered chain: each step's predecessor (for full chain walk)
STEP_CHAIN: dict[str, str | None] = {
    "setup": None,
    "step-1": "setup",
    "step-2": "step-1",
    "step-3": "step-2",
    "step-4": "step-3",
    "step-5": "step-4",
    "step-6": "step-5",
    "step-7": "step-6",
    "step-8": "step-7",
    "step-9": "step-8",
    "step-10": "step-9",
}


# ---------------------------------------------------------------------------
# TOML writer (simple serializer for manifest structure)
# ---------------------------------------------------------------------------


def _serialize_toml_value(value) -> str:
    """Serialize a single value to TOML format."""
    if isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, float):
        return str(value)
    elif isinstance(value, str):
        # Escape backslashes and quotes
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    elif isinstance(value, list):
        items = ", ".join(_serialize_toml_value(v) for v in value)
        return f"[{items}]"
    else:
        return f'"{value}"'


def _serialize_toml(data: dict, prefix: str = "") -> str:
    """Serialize a dict to TOML format string."""
    lines: list[str] = []
    # First, write all non-dict values at this level
    for key, value in data.items():
        if not isinstance(value, dict):
            lines.append(f"{key} = {_serialize_toml_value(value)}")

    # Then write nested tables
    for key, value in data.items():
        if isinstance(value, dict):
            table_name = f"{prefix}.{key}" if prefix else key
            lines.append("")
            lines.append(f"[{table_name}]")
            # Recursively serialize, but only non-dict values here
            for k, v in value.items():
                if not isinstance(v, dict):
                    lines.append(f"{k} = {_serialize_toml_value(v)}")
            # Nested sub-tables
            for k, v in value.items():
                if isinstance(v, dict):
                    sub_table = f"{table_name}.{k}"
                    lines.append("")
                    lines.append(f"[{sub_table}]")
                    sub_lines = _serialize_toml(v, sub_table)
                    # Only add non-header lines (the recursive call handles deeper nesting)
                    for sl in sub_lines.splitlines():
                        if sl and not sl.startswith("["):
                            lines.append(sl)
                        elif sl.startswith("["):
                            lines.append("")
                            lines.append(sl)

    return "\n".join(lines)


def _write_manifest(project_root: Path, data: dict) -> None:
    """Atomically write manifest.toml."""
    manifest_file = project_root / ".streetlights-demo" / "manifest.toml"
    content = _serialize_toml(data)
    if not content.endswith("\n"):
        content += "\n"

    # Atomic write: write to temp file then rename
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    fd = tempfile.NamedTemporaryFile(
        mode="w",
        dir=manifest_file.parent,
        prefix=".manifest_",
        suffix=".tmp",
        delete=False,
    )
    try:
        fd.write(content)
        fd.close()
        os.replace(fd.name, manifest_file)
    except Exception:
        os.unlink(fd.name)
        raise


def _update_step_status(project_root: Path, step: str, status: str, desc: str = "") -> None:
    """Update or create a step status section in the manifest."""
    manifest = _load_manifest(project_root)

    # Ensure nested structure exists
    if "demo" not in manifest:
        manifest["demo"] = {}
    if "steps" not in manifest["demo"]:
        manifest["demo"]["steps"] = {}

    now = datetime.now(UTC).isoformat()

    step_data = manifest["demo"]["steps"].get(step, {})
    step_data["status"] = status

    if status == "IN_PROGRESS":
        step_data["started_at"] = now
        if desc:
            step_data["desc"] = desc
    elif status == "COMPLETE":
        step_data["completed_at"] = now
        if desc:
            step_data["desc"] = desc

    manifest["demo"]["steps"][step] = step_data
    _write_manifest(project_root, manifest)


def _remove_step(project_root: Path, step: str) -> None:
    """Remove a step section entirely from the manifest."""
    manifest = _load_manifest(project_root)

    steps = manifest.get("demo", {}).get("steps", {})
    if step in steps:
        del steps[step]
        if "demo" in manifest and "steps" in manifest["demo"]:
            manifest["demo"]["steps"] = steps
        _write_manifest(project_root, manifest)


# ---------------------------------------------------------------------------
# Project root discovery
# ---------------------------------------------------------------------------


def _find_project_root() -> Path:
    """Find project root by walking up from CWD looking for .streetlights-demo/manifest.toml."""
    current = Path.cwd()
    while True:
        if (current / ".streetlights-demo" / "manifest.toml").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    # Fallback: use CWD
    raise FileNotFoundError(
        "Could not find .streetlights-demo/manifest.toml in any parent directory"
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
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
        choices=["check", "start", "complete", "reset"],
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
        project_root = _find_project_root()
    except FileNotFoundError as e:
        print(f"BLOCK: {e}")
        raise SystemExit(1)

    # --- Action: reset ---
    if args.action == "reset":
        _remove_step(project_root, args.step)
        print(f"OK: {args.step} reset")
        raise SystemExit(0)

    # --- Action: start ---
    if args.action == "start":
        _update_step_status(project_root, args.step, "IN_PROGRESS", desc=args.desc or "")
        print(f"OK: {args.step} marked IN_PROGRESS")
        raise SystemExit(0)

    # --- Action: complete ---
    if args.action == "complete":
        _update_step_status(project_root, args.step, "COMPLETE")
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
            manifest = _load_manifest(project_root)
            steps = manifest.get("demo", {}).get("steps", {})
        except FileNotFoundError:
            print(f"BLOCK: manifest not found — cannot verify chain for {args.prior_step}")
            raise SystemExit(1)

        for ancestor in chain:
            ancestor_state = steps.get(ancestor, {})
            ancestor_check_fn = STEP_CHECKS.get(ancestor)

            if ancestor_state.get("status") == "COMPLETE":
                # Check freshness
                completed_at = ancestor_state.get("completed_at", "")
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
                        _update_step_status(
                            project_root,
                            ancestor,
                            "COMPLETE",
                            desc=STEP_DESCRIPTIONS.get(ancestor, ""),
                        )
                        # Reload manifest for next iteration
                        manifest = _load_manifest(project_root)
                        steps = manifest.get("demo", {}).get("steps", {})
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
                        _update_step_status(
                            project_root,
                            ancestor,
                            "COMPLETE",
                            desc=STEP_DESCRIPTIONS.get(ancestor, ""),
                        )
                        # Reload manifest for next iteration
                        manifest = _load_manifest(project_root)
                        steps = manifest.get("demo", {}).get("steps", {})
                        continue
                    else:
                        print(f"BLOCK: chain step {ancestor} not complete" f" - {result.message}")
                        raise SystemExit(1)
                else:
                    print(f"BLOCK: chain step {ancestor} not complete")
                    raise SystemExit(1)

    # Self-healing check logic
    try:
        manifest = _load_manifest(project_root)
        steps = manifest.get("demo", {}).get("steps", {})
        step_state = steps.get(args.step, {})
    except FileNotFoundError:
        step_state = {}

    if step_state.get("status") == "COMPLETE":
        # Check if cached result is still fresh
        completed_at = step_state.get("completed_at", "")
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
                # Refresh the timestamp
                _update_step_status(
                    project_root, args.step, "COMPLETE", desc=STEP_DESCRIPTIONS.get(args.step, "")
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
        _update_step_status(
            project_root, args.step, "COMPLETE", desc=STEP_DESCRIPTIONS.get(args.step, "")
        )
        print(f"PASS: {args.step} backfilled")
        raise SystemExit(0)
    else:
        print(f"BLOCK: {args.step} not complete - {result.message}")
        raise SystemExit(1)
