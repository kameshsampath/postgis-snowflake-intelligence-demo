# Copyright 2025 Kamesh Sampath <kamesh.sampath@gmail.com>
# SPDX-License-Identifier: Apache-2.0

"""Tests for scripts.platform — platform detection and lazy resource loading."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestPlatformDetection:
    """PlatformDetector resolves platform from env, cwd, manifest, and dirs."""

    def test_env_var_snowflake(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts.platform import Platform, PlatformDetector

        monkeypatch.setenv("PLATFORM", "snowflake")
        detector = PlatformDetector(project_root=tmp_path)
        assert detector.detect() == Platform.SNOWFLAKE
        assert detector.is_snowflake is True
        assert detector.is_databricks is False

    def test_env_var_databricks_aliases(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from scripts.platform import Platform, PlatformDetector

        for value in ("databricks", "dbx", "db"):
            monkeypatch.setenv("PLATFORM", value)
            assert (
                PlatformDetector(project_root=tmp_path).detect(force_refresh=True)
                == Platform.DATABRICKS
            )

    def test_both_dirs_without_a_choice_never_yields_both(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Both platform dirs present + no explicit choice => UNKNOWN, and
        require_platform() fails immediately instead of assuming BOTH."""
        from scripts.platform import Platform, PlatformDetector, PlatformNotChosenError

        monkeypatch.delenv("PLATFORM", raising=False)
        (tmp_path / "snowflake").mkdir()
        (tmp_path / "snowflake" / "x.sql").write_text("SELECT 1")
        (tmp_path / "databricks").mkdir()
        (tmp_path / "databricks" / "databricks.yml").write_text("bundle:\n  name: x\n")
        detector = PlatformDetector(project_root=tmp_path)
        assert detector.detect() == Platform.UNKNOWN
        with pytest.raises(PlatformNotChosenError):
            detector.require_platform()

    def test_detect_from_directories_databricks_only(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from scripts.platform import Platform, PlatformDetector

        monkeypatch.delenv("PLATFORM", raising=False)
        (tmp_path / "databricks" / "sql").mkdir(parents=True)
        (tmp_path / "databricks" / "sql" / "01_setup.sql").write_text("SELECT 1")
        detector = PlatformDetector(project_root=tmp_path)
        assert detector.detect() == Platform.DATABRICKS

    def test_unknown_when_nothing_present(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from scripts.platform import Platform, PlatformDetector

        monkeypatch.delenv("PLATFORM", raising=False)
        detector = PlatformDetector(project_root=tmp_path)
        assert detector.detect() == Platform.UNKNOWN


class TestPlatformResources:
    """Lazy loading returns only the current platform's files."""

    def test_sql_files_per_platform(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts.platform import PlatformDetector

        (tmp_path / "snowflake").mkdir()
        (tmp_path / "snowflake" / "01_setup.sql").write_text("SELECT 1")
        (tmp_path / "databricks" / "sql").mkdir(parents=True)
        (tmp_path / "databricks" / "sql" / "01_setup.sql").write_text("SELECT 1")

        monkeypatch.setenv("PLATFORM", "databricks")
        detector = PlatformDetector(project_root=tmp_path)
        sql_files = detector.get_sql_files()
        assert len(sql_files) == 1
        assert "databricks" in str(sql_files[0])

        monkeypatch.setenv("PLATFORM", "both")
        detector = PlatformDetector(project_root=tmp_path)
        detector.detect(force_refresh=True)
        assert len(detector.get_sql_files()) == 2

    def test_gate_files_include_base_and_platform(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from scripts.platform import PlatformDetector

        gates = tmp_path / "scripts" / "gates"
        gates.mkdir(parents=True)
        (gates / "base_gates.py").write_text("")
        (gates / "databricks_gates.py").write_text("")

        monkeypatch.setenv("PLATFORM", "databricks")
        detector = PlatformDetector(project_root=tmp_path)
        names = [p.name for p in detector.get_gate_files()]
        assert "base_gates.py" in names
        assert "databricks_gates.py" in names
        assert "snowflake_gates.py" not in names

    def test_assert_platform_raises_on_mismatch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from scripts.platform import Platform, PlatformDetector

        monkeypatch.setenv("PLATFORM", "databricks")
        detector = PlatformDetector(project_root=tmp_path)
        with pytest.raises(RuntimeError):
            detector.assert_platform(Platform.SNOWFLAKE)
        assert detector.assert_platform(Platform.DATABRICKS) is True


class TestChosenPlatformIsolation:
    """Choosing one platform must ignore ALL of the other platform's paths."""

    def _make_both_layout(self, root: Path) -> None:
        (root / "snowflake").mkdir()
        (root / "snowflake" / "01_setup.sql").write_text("SELECT 1")
        (root / "databricks" / "sql").mkdir(parents=True)
        (root / "databricks" / "sql" / "01_setup.sql").write_text("SELECT 1")
        gates = root / "scripts" / "gates"
        gates.mkdir(parents=True)
        for name in ("base_gates.py", "snowflake_gates.py", "databricks_gates.py"):
            (gates / name).write_text("")
        cortex = root / ".cortex" / "skills"
        for name in (
            "streetlights-demo",
            "streetlights-demo-snowflake",
            "streetlights-demo-databricks",
        ):
            (cortex / name).mkdir(parents=True)

    def test_databricks_choice_ignores_all_snowflake_paths(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from scripts.platform import Platform, PlatformDetector

        self._make_both_layout(tmp_path)
        monkeypatch.setenv("PLATFORM", "databricks")
        detector = PlatformDetector(project_root=tmp_path)

        assert detector.detect() == Platform.DATABRICKS
        assert all("snowflake" not in str(p) for p in detector.get_sql_files())
        assert all("snowflake" not in str(p) for p in detector.get_gate_files())
        assert all("snowflake" not in str(p) for p in detector.get_skill_paths())
        assert all("snowflake" not in str(p) for p in detector.get_resource_paths())
        # the ignored list is exactly the snowflake side
        assert detector.get_ignored_paths() != []
        assert all("snowflake" in str(p) for p in detector.get_ignored_paths())

    def test_snowflake_choice_ignores_all_databricks_paths(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from scripts.platform import Platform, PlatformDetector

        self._make_both_layout(tmp_path)
        monkeypatch.setenv("PLATFORM", "snowflake")
        detector = PlatformDetector(project_root=tmp_path)

        assert detector.detect() == Platform.SNOWFLAKE
        assert all("databricks" not in str(p) for p in detector.get_sql_files())
        assert all("databricks" not in str(p) for p in detector.get_gate_files())
        assert all("databricks" not in str(p) for p in detector.get_resource_paths())
        assert detector.get_ignored_paths() != []
        assert all("databricks" in str(p) for p in detector.get_ignored_paths())

    def test_both_ignores_nothing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from scripts.platform import Platform, PlatformDetector

        self._make_both_layout(tmp_path)
        monkeypatch.setenv("PLATFORM", "both")
        detector = PlatformDetector(project_root=tmp_path)

        assert detector.detect() == Platform.BOTH
        assert detector.get_ignored_paths() == []
        assert len(detector.get_sql_files()) == 2

    def test_manifest_platform_field_is_an_explicit_choice(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from scripts.platform import Platform, PlatformDetector

        monkeypatch.delenv("PLATFORM", raising=False)
        demo = tmp_path / ".streetlights-demo"
        demo.mkdir()
        (demo / "manifest.toml").write_text(
            '[snowflake]\nconnection = "dev"\n\n'
            '[databricks]\nhost = "https://x.cloud.databricks.com"\nplatform = "databricks"\n'
        )
        detector = PlatformDetector(project_root=tmp_path)
        assert detector.detect() == Platform.DATABRICKS

    def test_manifest_with_both_sections_but_no_choice_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Both sections present without platform=... is NOT a choice: UNKNOWN,
        and require_platform() raises instead of returning BOTH."""
        from scripts.platform import Platform, PlatformDetector, PlatformNotChosenError

        monkeypatch.delenv("PLATFORM", raising=False)
        demo = tmp_path / ".streetlights-demo"
        demo.mkdir()
        (demo / "manifest.toml").write_text(
            '[snowflake]\nconnection = "dev"\n\n[databricks]\nhost = "https://x"\n'
        )
        detector = PlatformDetector(project_root=tmp_path)
        assert detector.detect() == Platform.UNKNOWN
        with pytest.raises(PlatformNotChosenError):
            detector.require_platform()

    def test_resolve_platform_choice(self) -> None:
        from scripts.platform import Platform, resolve_platform_choice

        assert resolve_platform_choice("dbx") == Platform.DATABRICKS
        assert resolve_platform_choice("SF") == Platform.SNOWFLAKE
        assert resolve_platform_choice("both") == Platform.BOTH
        with pytest.raises(ValueError):
            resolve_platform_choice("gcp")

    def test_gate_step_checks_exclude_other_platform(self) -> None:
        from scripts.gate import get_step_checks
        from scripts.platform import Platform

        sf_checks = get_step_checks(Platform.SNOWFLAKE)
        assert not any(k.startswith("dbx/") for k in sf_checks)
        assert "step-2" in sf_checks  # snowflake-owned

        dbx_checks = get_step_checks(Platform.DATABRICKS)
        assert "dbx/setup" in dbx_checks
        # on the DBX path, step-2 is the Lakebase check, not the Snowflake PG one
        assert dbx_checks["step-2"].__module__ == "scripts.gates.databricks_gates"
