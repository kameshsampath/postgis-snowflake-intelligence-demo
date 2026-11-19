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

    def test_detect_from_directories_both(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from scripts.platform import Platform, PlatformDetector

        monkeypatch.delenv("PLATFORM", raising=False)
        (tmp_path / "snowflake").mkdir()
        (tmp_path / "snowflake" / "x.sql").write_text("SELECT 1")
        (tmp_path / "databricks").mkdir()
        (tmp_path / "databricks" / "databricks.yml").write_text("bundle:\n  name: x\n")
        detector = PlatformDetector(project_root=tmp_path)
        assert detector.detect() == Platform.BOTH
        assert detector.is_both is True

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
