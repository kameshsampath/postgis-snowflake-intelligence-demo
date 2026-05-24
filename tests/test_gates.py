"""Tests for scripts.gate and scripts.sanity_gate — validation gates.

Gate scripts are used by the CoCo skill to verify preconditions before
proceeding to the next step. They should:
- Exit 0 on success, non-zero on failure
- Print clear error messages on failure
- Be callable as CLI commands via Click
- Check specific infrastructure and configuration state

Based on plan (Stage 6) and architecture review:
- gate.py: Pre-step validation (manifest exists, PG reachable, CLD healthy, etc.)
- sanity_gate.py: Post-step sanity checks (table counts, view exists, service up)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


class TestGateManifestCheck:
    """gate.py should verify manifest.toml exists and is parseable."""

    def test_gate_passes_with_valid_manifest(self, manifest_dir: Path) -> None:
        """Gate check passes when manifest.toml exists and is valid."""
        from scripts.gate import check_manifest

        result = check_manifest(project_root=manifest_dir)
        assert result.success is True

    def test_gate_fails_when_manifest_missing(self, empty_manifest_dir: Path) -> None:
        """Gate check fails when .streetlights-demo/manifest.toml is absent."""
        from scripts.gate import check_manifest

        result = check_manifest(project_root=empty_manifest_dir)
        assert result.success is False
        assert "manifest" in result.message.lower()

    def test_gate_fails_on_malformed_manifest(self, tmp_path: Path) -> None:
        """Gate check fails when manifest.toml has invalid TOML."""
        from scripts.gate import check_manifest

        demo_dir = tmp_path / ".streetlights-demo"
        demo_dir.mkdir()
        (demo_dir / "manifest.toml").write_text("invalid [[ toml content")

        result = check_manifest(project_root=tmp_path)
        assert result.success is False


class TestGatePgReachable:
    """gate.py should verify PostgreSQL instance is reachable."""

    def test_gate_passes_when_pg_reachable(self, manifest_dir: Path) -> None:
        """Gate passes when PG instance responds to connection check."""
        from scripts.gate import check_pg_reachable

        with patch("scripts.gate._pg_ping", return_value=True):
            result = check_pg_reachable(project_root=manifest_dir)
            assert result.success is True

    def test_gate_fails_when_pg_unreachable(self, manifest_dir: Path) -> None:
        """Gate fails when PG instance is not reachable."""
        from scripts.gate import check_pg_reachable

        with patch("scripts.gate._pg_ping", return_value=False):
            result = check_pg_reachable(project_root=manifest_dir)
            assert result.success is False
            assert "pg" in result.message.lower() or "postgres" in result.message.lower()


class TestGateCldHealthy:
    """gate.py should verify Catalog-Linked Database is healthy."""

    def test_gate_passes_when_cld_has_tables(self, manifest_dir: Path) -> None:
        """Gate passes when CLD database shows tables."""
        from scripts.gate import check_cld_healthy

        wh_rows = [{"name": "TESTUSER_STREETLIGHTS_WH"}]
        with (
            patch("scripts.gate._snow_json", return_value=(0, wh_rows)),
            patch("scripts.gate._cld_table_count", return_value=7),
        ):
            result = check_cld_healthy(project_root=manifest_dir)
            assert result.success is True

    def test_gate_fails_when_cld_has_zero_tables(self, manifest_dir: Path) -> None:
        """Gate fails when CLD database has no tables (propagation not done)."""
        from scripts.gate import check_cld_healthy

        wh_rows = [{"name": "TESTUSER_STREETLIGHTS_WH"}]
        with (
            patch("scripts.gate._snow_json", return_value=(0, wh_rows)),
            patch("scripts.gate._cld_table_count", return_value=0),
        ):
            result = check_cld_healthy(project_root=manifest_dir)
            assert result.success is False
            assert "table" in result.message.lower() or "cld" in result.message.lower()

    def test_gate_fails_when_cld_database_missing(self, manifest_dir: Path) -> None:
        """Gate fails when CLD database does not exist."""
        from scripts.gate import check_cld_healthy

        with patch("scripts.gate._cld_table_count", side_effect=Exception("does not exist")):
            result = check_cld_healthy(project_root=manifest_dir)
            assert result.success is False


class TestGateAccountParams:
    """gate.py should verify required account parameters are enabled."""

    def test_gate_passes_with_required_params_enabled(self, manifest_dir: Path) -> None:
        """Gate passes when ENABLE_SNOWFLAKE_POSTGRES is enabled."""
        from scripts.gate import check_account_params

        with patch(
            "scripts.gate._get_account_params",
            return_value={"ENABLE_SNOWFLAKE_POSTGRES": True},
        ):
            result = check_account_params(project_root=manifest_dir)
            assert result.success is True

    def test_gate_fails_when_required_param_missing(self, manifest_dir: Path) -> None:
        """Gate fails when ENABLE_SNOWFLAKE_POSTGRES is not enabled."""
        from scripts.gate import check_account_params

        with patch(
            "scripts.gate._get_account_params",
            return_value={"ENABLE_SNOWFLAKE_POSTGRES": False},
        ):
            result = check_account_params(project_root=manifest_dir)
            assert result.success is False
            assert "account" in result.message.lower() or "param" in result.message.lower()


class TestGateResult:
    """Test the GateResult data structure."""

    def test_gate_result_has_success_and_message(self) -> None:
        """GateResult has success bool and message string."""
        from scripts.gate import GateResult

        r = GateResult(success=True, message="All good")
        assert r.success is True
        assert r.message == "All good"

    def test_gate_result_failure(self) -> None:
        """GateResult can represent failure."""
        from scripts.gate import GateResult

        r = GateResult(success=False, message="Manifest not found")
        assert r.success is False
        assert "Manifest" in r.message


class TestSanityGateSemanticView:
    """sanity_gate.py should verify Semantic View exists after Step 5."""

    def test_sanity_passes_when_semantic_view_exists(self, manifest_dir: Path) -> None:
        """Sanity gate passes when semantic view is found in Snowflake."""
        from scripts.sanity_gate import check_semantic_view

        with patch("scripts.sanity_gate._semantic_view_exists", return_value=True):
            result = check_semantic_view(project_root=manifest_dir)
            assert result.success is True

    def test_sanity_fails_when_semantic_view_missing(self, manifest_dir: Path) -> None:
        """Sanity gate fails when semantic view does not exist."""
        from scripts.sanity_gate import check_semantic_view

        with patch("scripts.sanity_gate._semantic_view_exists", return_value=False):
            result = check_semantic_view(project_root=manifest_dir)
            assert result.success is False
            assert "semantic" in result.message.lower()


class TestSanityGateCortexSearch:
    """sanity_gate.py should verify Cortex Search service after Step 6."""

    def test_sanity_passes_when_search_service_active(self, manifest_dir: Path) -> None:
        """Sanity gate passes when Cortex Search service is ACTIVE."""
        from scripts.sanity_gate import check_cortex_search

        with patch("scripts.sanity_gate._cortex_search_status", return_value="ACTIVE"):
            result = check_cortex_search(project_root=manifest_dir)
            assert result.success is True

    def test_sanity_fails_when_search_service_not_active(self, manifest_dir: Path) -> None:
        """Sanity gate fails when Cortex Search service is not ACTIVE."""
        from scripts.sanity_gate import check_cortex_search

        with patch("scripts.sanity_gate._cortex_search_status", return_value="PROVISIONING"):
            result = check_cortex_search(project_root=manifest_dir)
            assert result.success is False


class TestSanityGateAgent:
    """sanity_gate.py should verify Intelligence Agent after Step 7."""

    def test_sanity_passes_when_agent_accessible(self, manifest_dir: Path) -> None:
        """Sanity gate passes when the Cortex Agent is accessible."""
        from scripts.sanity_gate import check_agent

        with patch("scripts.sanity_gate._agent_accessible", return_value=True):
            result = check_agent(project_root=manifest_dir)
            assert result.success is True

    def test_sanity_fails_when_agent_not_found(self, manifest_dir: Path) -> None:
        """Sanity gate fails when the Cortex Agent doesn't exist."""
        from scripts.sanity_gate import check_agent

        with patch("scripts.sanity_gate._agent_accessible", return_value=False):
            result = check_agent(project_root=manifest_dir)
            assert result.success is False
            assert "agent" in result.message.lower()


class TestSanityGateForecast:
    """sanity_gate.py should verify ML Forecast model after Step 8."""

    def test_sanity_passes_when_forecast_model_exists(self, manifest_dir: Path) -> None:
        """Sanity gate passes when FORECAST model exists."""
        from scripts.sanity_gate import check_forecast_model

        with patch("scripts.sanity_gate._forecast_model_exists", return_value=True):
            result = check_forecast_model(project_root=manifest_dir)
            assert result.success is True

    def test_sanity_fails_when_forecast_model_missing(self, manifest_dir: Path) -> None:
        """Sanity gate fails when FORECAST model doesn't exist."""
        from scripts.sanity_gate import check_forecast_model

        with patch("scripts.sanity_gate._forecast_model_exists", return_value=False):
            result = check_forecast_model(project_root=manifest_dir)
            assert result.success is False
            assert "forecast" in result.message.lower()


class TestGateChainVerification:
    """gate.py chain walk should verify the full ancestor chain, not just the immediate prior."""

    def _run_gate_cli(self, args: list[str], cwd: Path) -> tuple[int, str]:
        """Run gate.py as a subprocess and return (exit_code, stdout)."""
        import subprocess

        result = subprocess.run(
            ["python3", "-m", "scripts.gate", *args],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        return result.returncode, result.stdout.strip()

    def test_chain_skips_fresh_ancestors(self, manifest_dir: Path) -> None:
        """Fresh ancestors (< 1hr) are skipped without re-verification."""

        from scripts._manifest import update_step

        # Mark setup and step-1 as COMPLETE with fresh timestamps
        update_step(manifest_dir, "setup", "COMPLETE", desc="Initialize")
        update_step(manifest_dir, "step-1", "COMPLETE", desc="Generate Data")

        # step-2 check: mock _pg_ping to return True (PG reachable)
        with patch("scripts.gate._pg_ping", return_value=True):
            exit_code, output = self._run_gate_cli(
                ["--step", "step-2", "--prior-step", "step-1", "--action", "check"],
                cwd=manifest_dir,
            )

        # step-2 should backfill (PG reachable) — chain ancestors were fresh so skipped
        assert exit_code == 0
        assert "PASS" in output

    def test_chain_reverifies_stale_ancestor(self, manifest_dir: Path) -> None:
        """Stale ancestors (> 1hr) get re-verified via their check function."""
        from datetime import UTC, datetime, timedelta

        from scripts._manifest import load as load_manifest
        from scripts._manifest import save as save_manifest
        from scripts._manifest import update_step

        # Mark setup as COMPLETE but 2 hours ago (stale)
        update_step(manifest_dir, "setup", "COMPLETE", desc="Initialize")
        manifest = load_manifest(manifest_dir)
        old_time = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        manifest.demo.steps["setup"].completed_at = old_time
        save_manifest(manifest_dir, manifest)

        # Mark step-1 as COMPLETE (fresh)
        update_step(manifest_dir, "step-1", "COMPLETE", desc="Generate Data")

        # When step-2 checks its chain, setup is stale so check_manifest runs
        # check_manifest will pass (manifest exists) and re-stamp setup
        with patch("scripts.gate._pg_ping", return_value=True):
            exit_code, output = self._run_gate_cli(
                ["--step", "step-2", "--prior-step", "step-1", "--action", "check"],
                cwd=manifest_dir,
            )

        assert exit_code == 0
        assert "PASS" in output

        # Verify setup was re-stamped with fresh timestamp
        manifest = load_manifest(manifest_dir)
        setup_state = manifest.demo.steps["setup"]
        completed_time = datetime.fromisoformat(setup_state.completed_at)
        elapsed = (datetime.now(UTC) - completed_time).total_seconds()
        assert elapsed < 60  # Should have been re-stamped just now

    def test_chain_blocks_when_stale_ancestor_fails_reverification(
        self, manifest_dir: Path
    ) -> None:
        """Chain blocks if a stale ancestor fails re-verification."""
        from datetime import UTC, datetime, timedelta

        from scripts._manifest import load as load_manifest
        from scripts._manifest import save as save_manifest
        from scripts._manifest import update_step

        # Mark setup as COMPLETE but stale, and make check_manifest fail
        update_step(manifest_dir, "setup", "COMPLETE", desc="Initialize")
        manifest = load_manifest(manifest_dir)
        old_time = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        manifest.demo.steps["setup"].completed_at = old_time
        save_manifest(manifest_dir, manifest)

        # Delete the manifest to make check_manifest fail on re-verification
        manifest_file = manifest_dir / ".streetlights-demo" / "manifest.toml"
        manifest_file.unlink()

        exit_code, output = self._run_gate_cli(
            ["--step", "step-2", "--prior-step", "step-1", "--action", "check"],
            cwd=manifest_dir,
        )

        assert exit_code == 1
        assert "BLOCK" in output

    def test_chain_backfills_missing_ancestor(self, manifest_dir: Path) -> None:
        """Missing ancestors get backfilled if their verifier passes."""
        from scripts._manifest import load as load_manifest
        from scripts._manifest import update_step

        # step-1 is NOT marked in manifest at all (missing)
        # But setup is fresh
        update_step(manifest_dir, "setup", "COMPLETE", desc="Initialize")

        # Create CSV files so step-1 check passes
        data_dir = manifest_dir / "data"
        data_dir.mkdir(exist_ok=True)
        for name in [
            "street_lights.csv",
            "maintenance_records.csv",
            "energy_consumption.csv",
            "light_sensors.csv",
            "weather_enrichment.csv",
            "demographics.csv",
            "power_grid_zones.csv",
        ]:
            (data_dir / name).write_text("col1,col2\nval1,val2\n")

        # step-2 gate walks chain: setup (fresh, skip) → step-1 (missing, backfill)
        with patch("scripts.gate._pg_ping", return_value=True):
            exit_code, output = self._run_gate_cli(
                ["--step", "step-2", "--prior-step", "step-1", "--action", "check"],
                cwd=manifest_dir,
            )

        assert exit_code == 0
        assert "PASS" in output

        # step-1 should now be COMPLETE in manifest
        manifest = load_manifest(manifest_dir)
        assert manifest.demo.steps["step-1"].status == "COMPLETE"
        assert manifest.demo.steps["step-1"].desc == "Generating synthetic data"

    def test_chain_blocks_when_missing_ancestor_fails(self, manifest_dir: Path) -> None:
        """Chain blocks when a missing ancestor cannot be backfilled."""
        from scripts._manifest import update_step

        # setup is fresh but step-1 is missing and CSV files do NOT exist
        update_step(manifest_dir, "setup", "COMPLETE", desc="Initialize")

        exit_code, output = self._run_gate_cli(
            ["--step", "step-2", "--prior-step", "step-1", "--action", "check"],
            cwd=manifest_dir,
        )

        assert exit_code == 1
        assert "BLOCK" in output
        assert "step-1" in output

    def test_deep_chain_walk_verifies_all_ancestors(self, manifest_dir: Path) -> None:
        """A step deep in the chain verifies ALL ancestors, not just immediate prior.

        Uses subprocess with real file state (CSV files) to prove the chain walks
        past the immediate prior all the way back to setup.
        """
        from scripts._manifest import load as load_manifest
        from scripts._manifest import update_step

        # Mark setup as fresh
        update_step(manifest_dir, "setup", "COMPLETE", desc="Initialize")

        # step-1 is NOT in manifest (missing) — create CSV files so it can backfill
        data_dir = manifest_dir / "data"
        data_dir.mkdir(exist_ok=True)
        for name in [
            "street_lights.csv",
            "maintenance_records.csv",
            "energy_consumption.csv",
            "light_sensors.csv",
            "weather_enrichment.csv",
            "demographics.csv",
            "power_grid_zones.csv",
        ]:
            (data_dir / name).write_text("col1,col2\nval1,val2\n")

        # Run: step-2 --prior-step step-1
        # Chain is [setup, step-1] — setup is fresh (skip), step-1 is missing (backfill from CSVs)
        # After chain passes, "check" returns PASS (step-2 is ready) without running
        # step-2's own verifier (_pg_ping).
        exit_code, output = self._run_gate_cli(
            ["--step", "step-2", "--prior-step", "step-1", "--action", "check"],
            cwd=manifest_dir,
        )

        # "check" now only validates the chain and returns readiness — always exit 0
        # when chain passes, regardless of step-2's own verifier state.
        assert exit_code == 0
        assert "PASS" in output

        # The key assertion: step-1 was backfilled by the chain walk
        manifest = load_manifest(manifest_dir)
        assert manifest.demo.steps["step-1"].status == "COMPLETE"
        assert manifest.demo.steps["step-1"].desc == "Generating synthetic data"


class TestGateVerifyAction:
    """gate.py --action verify runs the current step's own verifier."""

    def _run_gate_cli(self, args: list[str], cwd: Path) -> tuple[int, str]:
        """Run gate.py as a subprocess and return (exit_code, stdout)."""
        import subprocess

        result = subprocess.run(
            ["python3", "-m", "scripts.gate", *args],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        return result.returncode, result.stdout.strip()

    def test_verify_passes_when_step_output_exists(self, manifest_dir: Path) -> None:
        """Verify passes and backfills when the step's verifier succeeds."""
        from scripts._manifest import load as load_manifest
        from scripts._manifest import update_step

        # setup is not COMPLETE yet — but its verifier (check_manifest) passes
        # because manifest_dir has a valid manifest
        update_step(manifest_dir, "setup", "IN_PROGRESS", desc="Initialize")

        exit_code, output = self._run_gate_cli(
            ["--step", "setup", "--action", "verify"],
            cwd=manifest_dir,
        )

        assert exit_code == 0
        assert "PASS" in output
        assert "backfill" in output.lower()

        # Should be backfilled to COMPLETE
        manifest = load_manifest(manifest_dir)
        assert manifest.demo.steps["setup"].status == "COMPLETE"

    def test_verify_fails_when_step_output_missing(self, manifest_dir: Path) -> None:
        """Verify blocks when the step's verifier fails."""
        from scripts._manifest import update_step

        # step-1 is not COMPLETE, and CSV files don't exist → _check_csv_data fails
        update_step(manifest_dir, "setup", "COMPLETE", desc="Initialize")

        exit_code, output = self._run_gate_cli(
            ["--step", "step-1", "--action", "verify"],
            cwd=manifest_dir,
        )

        assert exit_code == 1
        assert "BLOCK" in output

    def test_verify_uses_cache_when_fresh(self, manifest_dir: Path) -> None:
        """Verify returns cached result when step is COMPLETE and fresh."""
        from scripts._manifest import update_step

        # Mark step as freshly COMPLETE
        update_step(manifest_dir, "setup", "COMPLETE", desc="Initialize")

        exit_code, output = self._run_gate_cli(
            ["--step", "setup", "--action", "verify"],
            cwd=manifest_dir,
        )

        assert exit_code == 0
        assert "PASS" in output
        assert "cached" in output.lower()

    def test_check_returns_ready_without_running_verifier(self, manifest_dir: Path) -> None:
        """Check returns 'ready' for incomplete steps without running the verifier.

        This is the critical behavioral difference: check does NOT run the current
        step's verifier. It only checks the chain.
        """
        from scripts._manifest import update_step

        # Chain: setup is fresh, step-1 is fresh
        update_step(manifest_dir, "setup", "COMPLETE", desc="Initialize")
        update_step(manifest_dir, "step-1", "COMPLETE", desc="Generate Data")

        # step-2 is NOT in manifest — with old behavior, check would run _pg_ping
        # and BLOCK. With new behavior, it just says "ready".
        exit_code, output = self._run_gate_cli(
            ["--step", "step-2", "--prior-step", "step-1", "--action", "check"],
            cwd=manifest_dir,
        )

        assert exit_code == 0
        assert "PASS" in output
        assert "ready" in output.lower()


class TestManifestIO:
    """Test manifest read/write preserves non-owned sections."""

    def test_non_owned_sections_preserved(self, manifest_dir: Path) -> None:
        """Non-owned sections survive a load/save cycle."""
        from scripts._manifest import load as load_manifest
        from scripts._manifest import save as save_manifest

        # Add a non-owned section
        manifest_file = manifest_dir / ".streetlights-demo" / "manifest.toml"
        content = manifest_file.read_text()
        content += '\n[other_tool]\nfoo = "bar"\n'
        manifest_file.write_text(content)

        # Load and save back
        manifest = load_manifest(manifest_dir)
        save_manifest(manifest_dir, manifest)

        # Reload and verify preserved
        manifest2 = load_manifest(manifest_dir)
        assert "other_tool" in manifest2._extra
        assert manifest2._extra["other_tool"]["foo"] == "bar"
