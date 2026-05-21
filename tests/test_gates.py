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

        with patch("scripts.gate._cld_table_count", return_value=7):
            result = check_cld_healthy(project_root=manifest_dir)
            assert result.success is True

    def test_gate_fails_when_cld_has_zero_tables(self, manifest_dir: Path) -> None:
        """Gate fails when CLD database has no tables (propagation not done)."""
        from scripts.gate import check_cld_healthy

        with patch("scripts.gate._cld_table_count", return_value=0):
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
