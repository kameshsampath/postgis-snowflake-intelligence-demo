# Copyright 2025 Kamesh Sampath
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Gate checks for streetlights demo progression."""

import subprocess
import sys
import time
import tomllib
from pathlib import Path


def load_manifest() -> dict:
    """Load and return manifest.toml, or exit with error."""
    manifest_path = Path.cwd()
    while manifest_path != manifest_path.parent:
        candidate = manifest_path / ".streetlights-demo" / "manifest.toml"
        if candidate.exists():
            with open(candidate, "rb") as f:
                return tomllib.load(f)
        manifest_path = manifest_path.parent
    print("ERROR: .streetlights-demo/manifest.toml not found")
    sys.exit(1)


def check_manifest_exists() -> bool:
    """Gate: manifest.toml exists and is parseable."""
    try:
        load_manifest()
        return True
    except (SystemExit, Exception):
        return False


def check_pg_reachable(manifest: dict) -> bool:
    """Gate: PG instance responds to connection."""
    instance = manifest["demo"]["pg_instance"]
    result = subprocess.run(
        ["snow", "postgres", "execute", "-i", instance, "-c", "SELECT 1"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def check_pg_managed_storage(manifest: dict) -> bool:
    """Gate: verify instance uses managed storage (required for CLD)."""
    instance = manifest["demo"]["pg_instance"]
    result = subprocess.run(
        ["snow", "postgres", "describe", "-i", instance, "--format", "json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    return "MANAGED" in result.stdout.upper()


def check_account_params() -> bool:
    """Gate: required account params are set."""
    params = ["ENABLE_SNOWFLAKE_POSTGRES", "ENABLE_POSTGRES_HIDDEN_EXTERNAL_VOLUME"]
    for param in params:
        result = subprocess.run(
            ["snow", "sql", "-q", f"SHOW PARAMETERS LIKE '{param}' IN ACCOUNT"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or "true" not in result.stdout.lower():
            return False
    return True


def check_cld_healthy(manifest: dict, retries: int = 3, delay: float = 10.0) -> bool:
    """Gate: CLD DB exists + table count > 0 (with retry for propagation)."""
    cld_db = manifest["demo"]["cld_database"]
    for attempt in range(retries):
        result = subprocess.run(
            ["snow", "sql", "-q", f"SHOW TABLES IN DATABASE {cld_db}"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and "street_lights" in result.stdout:
            return True
        if attempt < retries - 1:
            time.sleep(delay)
    return False


def check_semantic_view_exists(manifest: dict) -> bool:
    """Gate: Semantic View exists."""
    cld_db = manifest["demo"]["cld_database"]
    result = subprocess.run(
        ["snow", "sql", "-q", f'SHOW SEMANTIC VIEWS IN SCHEMA {cld_db}."streetlights"'],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and "semantic_view" in result.stdout.lower()


def check_cortex_search_ready(manifest: dict) -> bool:
    """Gate: Cortex Search service is ACTIVE."""
    cld_db = manifest["demo"]["cld_database"]
    result = subprocess.run(
        [
            "snow",
            "sql",
            "-q",
            f'SHOW CORTEX SEARCH SERVICES IN SCHEMA {cld_db}."streetlights"',
        ],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and "ACTIVE" in result.stdout.upper()


def check_agent_accessible(manifest: dict) -> bool:
    """Gate: Agent responds to a test query."""
    cld_db = manifest["demo"]["cld_database"]
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


def check_forecast_model_ready(manifest: dict) -> bool:
    """Gate: FORECAST model is trained."""
    cld_db = manifest["demo"]["cld_database"]
    result = subprocess.run(
        [
            "snow",
            "sql",
            "-q",
            f'SHOW SNOWFLAKE.ML.FORECAST IN SCHEMA {cld_db}."streetlights"',
        ],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and "energy_forecast" in result.stdout.lower()


if __name__ == "__main__":
    manifest = load_manifest()
    checks = [
        ("manifest_exists", lambda: check_manifest_exists()),
        ("pg_reachable", lambda: check_pg_reachable(manifest)),
        ("pg_managed_storage", lambda: check_pg_managed_storage(manifest)),
        ("account_params", lambda: check_account_params()),
        ("cld_healthy", lambda: check_cld_healthy(manifest)),
        ("semantic_view_exists", lambda: check_semantic_view_exists(manifest)),
        ("cortex_search_ready", lambda: check_cortex_search_ready(manifest)),
        ("agent_accessible", lambda: check_agent_accessible(manifest)),
        ("forecast_model_ready", lambda: check_forecast_model_ready(manifest)),
    ]

    print("Running gate checks...")
    all_passed = True
    for name, check_fn in checks:
        try:
            passed = check_fn()
        except Exception as e:
            passed = False
            print(f"  [{name}] ERROR: {e}")
        status = "PASS" if passed else "FAIL"
        print(f"  [{name}] {status}")
        if not passed:
            all_passed = False

    sys.exit(0 if all_passed else 1)
