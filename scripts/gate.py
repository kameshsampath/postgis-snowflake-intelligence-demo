"""Gate checks for streetlights demo progression.

Provides pre-step validation functions that return GateResult objects
indicating success/failure with a descriptive message.

This module now imports from modular gate files in scripts/gates/.

Platform Detection:
    Automatically detects and uses platform-specific gate checks.
    Only loads gate functions relevant to the current platform.

CLI Usage:
    uv run gate --step setup --action check
    uv run gate --step step-1 --prior-step setup --action check
    uv run gate --step step-2 --action start --desc "Snowflake Postgres Instance"
    uv run gate --step step-2 --action complete
    uv run gate --step step-2 --action reset

    For platform-specific gates:
    uv run gate --step sf:step-1 --action check    # Snowflake
    uv run gate --step dbx:setup --action check    # Databricks
"""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts._manifest import find_project_root, remove_step, update_step
from scripts._manifest import load as load_manifest
from scripts.gates import GateResult
from scripts.gates.base_gates import (
    check_csv_files,
    check_csv_neighborhood_names,
    check_manifest,
    check_step1_complete,
)
from scripts.generate_ddl import generate_iceberg_ddl, get_dry_run_step3
from scripts.platform import Platform, PlatformDetector, get_platform_detector

# ---------------------------------------------------------------------------
# Step verification mapping
# ---------------------------------------------------------------------------


def get_step_checks(platform: Platform, detector: PlatformDetector = None) -> dict[str, callable]:
    """
    Get platform-specific step checks.

    This function returns only the step checks relevant to the specified platform,
    avoiding loading unnecessary gate functions.

    Args:
        platform: The target platform (SNOWFLAKE, DATABRICKS, BOTH, or UNKNOWN)
        detector: Optional PlatformDetector instance for lazy loading

    Returns:
        Dictionary mapping step names to check functions
    """
    if detector is None:
        detector = get_platform_detector()

    # Base checks (shared across platforms)
    from scripts.gates.base_gates import (
        check_manifest,
        check_pg_reachable,
        check_step1_complete,
    )

    step_checks: dict[str, callable] = {
        "setup": check_manifest,
        "step-1": check_step1_complete,
    }

    # Platform-specific checks
    if platform in [Platform.SNOWFLAKE, Platform.BOTH]:
        from scripts.gates.snowflake_gates import (
            check_cld_healthy,
            check_cortex_search,
            check_pg_tables,
            check_semantic_view,
        )

        step_checks.update(
            {
                "step-2": check_pg_reachable,
                "step-3": check_pg_tables,
                "step-4": check_cld_healthy,
                "step-5": check_semantic_view,
                "step-6": check_cortex_search,
                "step-7": lambda p: GateResult(
                    success=True, message="Intelligence Agent ready"
                ),  # Placeholder for Snowflake Intelligence Agent
            }
        )

        # Snowflake app phase
        from scripts.gates.snowflake_gates import (
            check_snowflake_all,
            check_snowflake_forecast,
            check_streamlit,
        )

        step_checks.update(
            {
                "step-8": check_snowflake_forecast,
                "step-9": check_streamlit,
                "step-10": check_snowflake_all,
            }
        )

    if platform in [Platform.DATABRICKS, Platform.BOTH]:
        from scripts.gates.databricks_gates import (
            check_dbx_all,
            check_dbx_app_deployed,
            check_dbx_forecast_ready,
            check_genie_space_active,
            check_lakebase_reachable,
            check_uc_sync_healthy,
            check_vector_index_ready,
        )

        # Databricks-specific step mappings
        step_checks.update(
            {
                "dbx/setup": check_lakebase_reachable,
                "dbx/genie-space": check_genie_space_active,
                "dbx/vector-search": check_vector_index_ready,
                "dbx/forecast": check_dbx_forecast_ready,
                "dbx/app": check_dbx_app_deployed,
                "dbx/all": check_dbx_all,
            }
        )

        # Databricks platform steps (step-1 through step-10 for Databricks)
        # These are alternative step names for Databricks implementation
        step_checks.update(
            {
                "step-2": check_lakebase_reachable,  # Step 2: Lakebase setup
                "step-3": check_pg_reachable,  # Step 3: Schema + Load
                "step-4": check_uc_sync_healthy,  # Step 4: UC Sync
                "step-5": check_genie_space_active,  # Step 5: Genie space
                "step-6": check_vector_index_ready,  # Step 6: Vector Search
                "step-7": lambda p: GateResult(
                    success=True, message="Genie Agent ready"
                ),  # Step 7: Genie Agent
                "step-8": check_dbx_forecast_ready,  # Step 8: AI_FORECAST
                "step-9": check_dbx_app_deployed,  # Step 9: Databricks App
                "step-10": check_dbx_all,  # Step 10: Validation
            }
        )

    return step_checks


# For backward compatibility, create a default STEP_CHECKS
# This will detect platform at import time
try:
    _detector = get_platform_detector()
    _platform = _detector.detect()
    STEP_CHECKS: dict[str, callable] = get_step_checks(_platform, _detector)
except Exception:
    # Fallback if platform detection fails
    STEP_CHECKS: dict[str, callable] = {
        "setup": check_manifest,
        "step-1": check_step1_complete,
    }


def get_step_descriptions(platform: Platform) -> dict[str, str]:
    """
    Get platform-specific step descriptions.

    Args:
        platform: The target platform

    Returns:
        Dictionary mapping step names to descriptions
    """
    descriptions: dict[str, str] = {
        "setup": "Initializing streetlights demo",
        "step-1": "Generating synthetic data",
    }

    if platform in [Platform.SNOWFLAKE, Platform.BOTH]:
        descriptions.update(
            {
                "step-2": "Creating Snowflake Postgres instance",
                "step-3": "Creating schema and loading data",
                "step-4": "Creating Catalog Integration + CLD",
                "step-5": "Creating Semantic View",
                "step-6": "Creating Cortex Search service",
                "step-7": "Creating Intelligence Agent",
                "step-8": "Training ML Forecast model",
                "step-9": "Deploying Streamlit app",
                "step-10": "Validating end-to-end demo",
            }
        )

    if platform in [Platform.DATABRICKS, Platform.BOTH]:
        descriptions.update(
            {
                "dbx/setup": "Setting up Databricks catalog and Lakebase sync",
                "dbx/genie-space": "Configuring Genie space and semantic layer",
                "dbx/vector-search": "Creating Vector Search index",
                "dbx/forecast": "Training ML forecast model",
                "dbx/app": "Deploying Databricks App",
                "dbx/all": "Validating complete Databricks implementation",
                # Databricks step descriptions
                "step-2": "Creating Lakebase instance",
                "step-3": "Creating schema and loading data",
                "step-4": "Setting up Unity Catalog sync",
                "step-5": "Configuring Genie space",
                "step-6": "Creating Vector Search index",
                "step-7": "Setting up Genie Agent",
                "step-8": "Training AI_FORECAST model",
                "step-9": "Deploying Databricks App",
                "step-10": "Validating complete implementation",
            }
        )

    return descriptions


# For backward compatibility
try:
    _platform = get_platform_detector().detect()
    STEP_DESCRIPTIONS: dict[str, str] = get_step_descriptions(_platform)
except Exception:
    STEP_DESCRIPTIONS: dict[str, str] = {
        "setup": "Initializing streetlights demo",
        "step-1": "Generating synthetic data",
    }


# ---------------------------------------------------------------------------
# Attribute chaining
# ---------------------------------------------------------------------------


def get_step_chain(platform: Platform) -> dict[str, str | None]:
    """
    Get platform-specific step dependency chain.

    Args:
        platform: The target platform

    Returns:
        Dictionary mapping step names to their prerequisite step
    """
    chain: dict[str, str | None] = {
        "setup": None,
        "step-1": "setup",
    }

    if platform in [Platform.SNOWFLAKE, Platform.BOTH]:
        chain.update(
            {
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
        )

    if platform in [Platform.DATABRICKS, Platform.BOTH]:
        chain.update(
            {
                "dbx/setup": None,
                "dbx/genie-space": "dbx/setup",
                "dbx/vector-search": "dbx/genie-space",
                "dbx/forecast": "dbx/vector-search",
                "dbx/app": "dbx/forecast",
                "dbx/all": "dbx/app",
                # Databricks step chain
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
        )

    return chain


# For backward compatibility
try:
    _platform = get_platform_detector().detect()
    STEP_CHAIN: dict[str, str | None] = get_step_chain(_platform)
except Exception:
    STEP_CHAIN: dict[str, str | None] = {
        "setup": None,
        "step-1": "setup",
    }


# Step-specific verification checks (non-gate utility functions)
# These are kept here for backward compatibility


def check_step1_complete(project_root: Path) -> GateResult:
    """Verify step-1: CSV files exist and contain real neighborhood names."""
    result = check_csv_files(project_root)
    if not result[0]:
        return GateResult(success=False, message=result[1])
    return check_csv_neighborhood_names(project_root)


def _check_pg_tables(project_root: Path) -> GateResult:
    """Verify PG tables have rows via psql."""
    # Pre-flight: generate DDL if missing (user may not have run generate yet)
    ddl_path = project_root / "init" / "02_create_iceberg_tables.sql"
    if not ddl_path.exists():
        generate_iceberg_ddl(output_path=ddl_path)

    from scripts._manifest import load as load_manifest
    from scripts.gates.base_gates import GateResult

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
        import subprocess

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


def _check_all(project_root: Path) -> GateResult:
    """Run ALL checks sequentially for final validation."""
    from scripts.gates.base_gates import check_manifest
    from scripts.platform import get_platform

    platform = get_platform()
    checks = []

    # Shared checks
    checks.extend(
        [
            ("manifest", check_manifest),
            ("csv_files", lambda p: GateResult(*check_csv_files(p)[:2])),
        ]
    )

    # Platform-specific checks
    if platform in [Platform.SNOWFLAKE, Platform.BOTH]:
        from scripts.gates.base_gates import check_pg_reachable
        from scripts.gates.snowflake_gates import (
            check_cld_healthy,
            check_cortex_search,
            check_pg_tables,
            check_semantic_view,
        )

        checks.extend(
            [
                ("pg_reachable", check_pg_reachable),
                ("pg_tables", check_pg_tables),
                ("cld_healthy", check_cld_healthy),
                ("semantic_view", check_semantic_view),
                ("cortex_search", check_cortex_search),
            ]
        )

    if platform in [Platform.DATABRICKS, Platform.BOTH]:
        from scripts.gates.databricks_gates import (
            check_genie_space_active,
            check_lakebase_reachable,
            check_uc_sync_healthy,
            check_vector_index_ready,
        )

        checks.extend(
            [
                ("lakebase_reachable", check_lakebase_reachable),
                ("uc_sync_healthy", check_uc_sync_healthy),
                ("genie_space_active", check_genie_space_active),
                ("vector_index_ready", check_vector_index_ready),
            ]
        )

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
        print("  Source dir: app/  Entry point: app/home.py")

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
        help="Step identifier (setup, step-1, step-2, ..., step-10, dbx/*)",
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

    # Full chain verification
    if args.prior_step:
        _validate_chain(project_root, args.prior_step, cache_ttl)

    # --- Action: check (readiness) ---
    # Chain passed (or no chain needed). Now determine if the current step is ready.
    if args.action == "check":
        _check_readiness(project_root, args.step, cache_ttl)

    # --- Action: verify (post-execution verification) ---
    if args.action == "verify":
        _verify_completion(project_root, args.step, cache_ttl)


def _validate_chain(project_root: Path, prior_step: str, cache_ttl: int) -> None:
    """Validate that all ancestor steps are complete."""
    # Build chain: [setup, step-1, ..., prior_step]
    chain: list[str] = []
    current = prior_step
    while current is not None:
        chain.append(current)
        current = STEP_CHAIN.get(current)
    chain.reverse()  # Now oldest-first: [setup, step-1, ..., prior_step]

    try:
        manifest = load_manifest(project_root)
        steps = manifest.demo.steps
    except FileNotFoundError:
        print(f"BLOCK: manifest not found — cannot verify chain for {prior_step}")
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
                    from datetime import UTC, datetime

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
                    print(f"BLOCK: chain step {ancestor} not complete - {result.message}")
                    raise SystemExit(1)
            else:
                print(f"BLOCK: chain step {ancestor} not complete")
                raise SystemExit(1)


def _check_readiness(project_root: Path, step: str, cache_ttl: int) -> None:
    """Check if the current step is ready to be executed."""
    try:
        manifest = load_manifest(project_root)
        step_state = manifest.demo.steps.get(step)
    except FileNotFoundError:
        step_state = None

    if step_state and step_state.status == "COMPLETE":
        # Already complete — check freshness
        completed_at = step_state.completed_at
        if completed_at:
            try:
                from datetime import UTC, datetime

                completed_time = datetime.fromisoformat(completed_at)
                elapsed = (datetime.now(UTC) - completed_time).total_seconds()
                if elapsed < cache_ttl:
                    print(f"PASS: {step} already complete (cached)")
                    raise SystemExit(0)
            except (ValueError, TypeError):
                pass

        # Stale — re-verify if we have a check function
        check_fn = STEP_CHECKS.get(step)
        if check_fn:
            result = check_fn(project_root)
            if result.success:
                update_step(
                    project_root,
                    step,
                    "COMPLETE",
                    desc=STEP_DESCRIPTIONS.get(step, ""),
                )
                print(f"PASS: {step} already complete (re-verified)")
                raise SystemExit(0)
            else:
                print(f"BLOCK: {step} was COMPLETE but re-verification failed - {result.message}")
                raise SystemExit(1)
        else:
            print(f"PASS: {step} already complete (cached, no re-check available)")
            raise SystemExit(0)

    # Step NOT complete — it's ready to run (chain already validated above)
    print(f"PASS: {step} ready")
    raise SystemExit(0)


def _verify_completion(project_root: Path, step: str, cache_ttl: int) -> None:
    """Verify that the current step has completed successfully."""
    try:
        manifest = load_manifest(project_root)
        step_state = manifest.demo.steps.get(step)
    except FileNotFoundError:
        step_state = None

    if step_state and step_state.status == "COMPLETE":
        # Already complete — check freshness
        completed_at = step_state.completed_at
        if completed_at:
            try:
                from datetime import UTC, datetime

                completed_time = datetime.fromisoformat(completed_at)
                elapsed = (datetime.now(UTC) - completed_time).total_seconds()
                if elapsed < cache_ttl:
                    print(f"PASS: {step} verified (cached)")
                    raise SystemExit(0)
            except (ValueError, TypeError):
                pass

        # Stale — re-verify
        check_fn = STEP_CHECKS.get(step)
        if check_fn:
            result = check_fn(project_root)
            if result.success:
                update_step(
                    project_root,
                    step,
                    "COMPLETE",
                    desc=STEP_DESCRIPTIONS.get(step, ""),
                )
                print(f"PASS: {step} re-verified")
                raise SystemExit(0)
            else:
                print(f"BLOCK: {step} was COMPLETE but re-verification failed - {result.message}")
                raise SystemExit(1)
        else:
            print(f"PASS: {step} verified (cached, no re-check available)")
            raise SystemExit(0)

    # Step MISSING or status != COMPLETE — run step-specific verify
    check_fn = STEP_CHECKS.get(step)
    if not check_fn:
        print(f"BLOCK: unknown step '{step}'")
        raise SystemExit(1)

    result = check_fn(project_root)
    if result.success:
        # Backfill as COMPLETE
        update_step(
            project_root,
            step,
            "COMPLETE",
            desc=STEP_DESCRIPTIONS.get(step, ""),
        )
        print(f"PASS: {step} backfilled")
        raise SystemExit(0)
    else:
        print(f"BLOCK: {step} not complete - {result.message}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
