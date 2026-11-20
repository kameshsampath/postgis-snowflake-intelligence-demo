#!/usr/bin/env python3
# Copyright 2025 Kamesh Sampath <kamesh.sampath@gmail.com>
# SPDX-License-Identifier: Apache-2.0
"""
Platform detection and management utilities for PostGIS Data Intelligence Demo.

This module provides platform-specific path resolution, environment detection,
and lazy loading of platform-specific files and resources.

Usage:
    from platform import Platform, PlatformDetector, get_platform

    # Detect current platform
    current_platform = get_platform()

    # Use platform-specific paths
    detector = PlatformDetector()
    sql_files = detector.get_sql_files()
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Type alias for file paths
FilePath = str | Path


class Platform(Enum):
    """Supported platforms for the demo."""

    SNOWFLAKE = "snowflake"
    DATABRICKS = "databricks"
    BOTH = "both"  # only ever an EXPLICIT choice, never inferred
    UNKNOWN = "unknown"


class PlatformNotChosenError(RuntimeError):
    """Raised when no platform has been explicitly chosen."""


@dataclass
class PlatformConfig:
    """Configuration for a specific platform."""

    name: str
    display_name: str
    directory: str
    sql_dir: str
    dependencies: list[str]
    description: str
    enabled: bool = True


class PlatformDetector:
    """
    Detects and manages the current platform based on environment, manifest, or working directory.

    This class implements lazy loading of platform-specific resources to avoid loading
    unnecessary files (e.g., Snowflake files when on Databricks platform).
    """

    # Platform configurations
    PLATFORM_CONFIGS = {
        Platform.SNOWFLAKE: PlatformConfig(
            name="snowflake",
            display_name="Snowflake",
            directory="snowflake",
            sql_dir="snowflake",
            dependencies=["snow"],
            description="Snowflake Postgres + pg_lake + Cortex AI",
        ),
        Platform.DATABRICKS: PlatformConfig(
            name="databricks",
            display_name="Databricks",
            directory="databricks",
            sql_dir="databricks/sql",
            dependencies=["databricks"],
            description="Databricks Lakebase + Unity Catalog + Genie",
        ),
    }

    def __init__(self, project_root: FilePath | None = None):
        """
        Initialize the platform detector.

        Args:
            project_root: The root directory of the project. If None, attempts
                         to auto-detect from current directory or parent directories.
        """
        self.project_root = Path(project_root) if project_root else self._find_project_root()
        self._cached_platform: Platform | None = None
        self._manifest_cache: dict | None = None

    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        # Look for marker files that identify the project root
        marker_files = [
            ".mise.toml",
            "pyproject.toml",
            "Taskfile.yml",
            ".cortex",
        ]

        current_dir = Path.cwd()

        # Search upwards from current directory
        for parent in [current_dir, *current_dir.parents]:
            for marker in marker_files:
                if (parent / marker).exists():
                    # Verify this is the correct project root
                    if (parent / "pyproject.toml").exists():
                        content = (parent / "pyproject.toml").read_text()
                        if "postgis-data-intelligence-demo" in content:
                            return parent
                    return parent

        return current_dir

    def detect(self, force_refresh: bool = False) -> Platform:
        """
        Detect the current platform.

        Detection order (first match wins):
        1. Environment variable PLATFORM (explicit choice; "both" allowed)
        2. Working directory (if inside snowflake/ or databricks/)
        3. Manifest `platform = "..."` field, else a single-section manifest
        4. Exactly one platform directory present

        BOTH is never inferred: if both platform dirs exist and nothing was
        chosen, detect() returns UNKNOWN and require_platform() fails fast.

        Args:
            force_refresh: If True, forces a fresh detection and clears cache.

        Returns:
            The detected platform, or UNKNOWN if no platform was chosen.
        """
        if not force_refresh and self._cached_platform:
            return self._cached_platform

        platform = self._detect_from_env()

        if platform == Platform.UNKNOWN:
            platform = self._detect_from_pwd()

        if platform == Platform.UNKNOWN:
            platform = self._detect_from_manifest()

        if platform == Platform.UNKNOWN:
            platform = self._detect_from_directories()

        self._cached_platform = platform
        return platform

    def _detect_from_env(self) -> Platform:
        """Detect platform from PLATFORM environment variable."""
        # Check PLATFORM env var first (can be set via mise profile)
        platform_env = os.getenv("PLATFORM", "").lower().strip()

        if platform_env in ["snowflake", "sf"]:
            return Platform.SNOWFLAKE
        elif platform_env in ["databricks", "dbx", "db"]:
            return Platform.DATABRICKS
        elif platform_env in ["both", "all"]:
            return Platform.BOTH

        # Check for platform-specific flags set by mise profiles
        if os.getenv("SNOWFLAKE_PLATFORM", "").lower() == "true":
            return Platform.SNOWFLAKE
        if os.getenv("DATABRICKS_PLATFORM", "").lower() == "true":
            return Platform.DATABRICKS

        return Platform.UNKNOWN

    def _detect_from_pwd(self) -> Platform:
        """Detect platform from current working directory."""
        current_dir = Path.cwd()

        # Check if we're inside a platform-specific directory
        try:
            relative_to_root = current_dir.relative_to(self.project_root)
        except ValueError:
            # cwd is not under the project root (e.g. tests pass a tmp root)
            return Platform.UNKNOWN

        for platform, config in self.PLATFORM_CONFIGS.items():
            if str(relative_to_root).startswith(config.directory):
                return platform

        return Platform.UNKNOWN

    def _detect_from_manifest(self) -> Platform:
        """Detect platform from manifest.toml.

        An explicit `platform = "snowflake" | "databricks" | "both"` field
        always wins. Otherwise, infer from which sections are present.
        """
        manifest_path = self.project_root / ".streetlights-demo" / "manifest.toml"

        if not manifest_path.exists():
            return Platform.UNKNOWN

        try:
            # Parse manifest (simple parsing - don't import tomllib for compatibility)
            content = manifest_path.read_text()

            # Explicit platform choice takes precedence over section presence
            match = re.search(r'^\s*platform\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
            if match:
                return resolve_platform_choice(match.group(1))

            # A manifest with only one platform section is that platform.
            # NEVER infer BOTH from both sections being present.
            if "[snowflake]" in content and "[databricks]" not in content:
                return Platform.SNOWFLAKE
            if "[databricks]" in content and "[snowflake]" not in content:
                return Platform.DATABRICKS
        except Exception:
            pass

        return Platform.UNKNOWN

    def _detect_from_directories(self) -> Platform:
        """Detect platform from platform-specific directories.

        Only an unambiguous single-platform layout counts as a choice.
        If both exist, this is NOT a choice: return UNKNOWN (require_platform
        will then fail fast instead of silently assuming BOTH).
        """
        snowflake_dir = self.project_root / "snowflake"
        databricks_dir = self.project_root / "databricks"

        has_snowflake = snowflake_dir.exists() and any(snowflake_dir.iterdir())
        has_databricks = databricks_dir.exists() and any(databricks_dir.iterdir())

        if has_snowflake and not has_databricks:
            return Platform.SNOWFLAKE
        if has_databricks and not has_snowflake:
            return Platform.DATABRICKS
        return Platform.UNKNOWN

    def require_platform(self) -> Platform:
        """Like detect(), but fails immediately if no platform was chosen.

        Raises:
            PlatformNotChosenError: if detection ends at UNKNOWN.
        """
        platform = self.detect()
        if platform == Platform.UNKNOWN:
            raise PlatformNotChosenError(
                "No platform chosen. Set PLATFORM=snowflake|databricks (env or .env), "
                'add platform = "snowflake"|"databricks" to .streetlights-demo/manifest.toml, '
                "run from inside snowflake/ or databricks/, or pass --platform to the gate CLI."
            )
        return platform

    @property
    def current_platform(self) -> Platform:
        """Get the current platform (cached)."""
        if not self._cached_platform:
            self._cached_platform = self.detect()
        return self._cached_platform

    @property
    def is_snowflake(self) -> bool:
        """Check if current platform is Snowflake or both."""
        return self.current_platform in [Platform.SNOWFLAKE, Platform.BOTH]

    @property
    def is_databricks(self) -> bool:
        """Check if current platform is Databricks or both."""
        return self.current_platform in [Platform.DATABRICKS, Platform.BOTH]

    @property
    def is_both(self) -> bool:
        """Check if current platform is both."""
        return self.current_platform == Platform.BOTH

    def get_platform_config(self, platform: Platform) -> PlatformConfig:
        """Get configuration for a specific platform."""
        return self.PLATFORM_CONFIGS[platform]

    def get_sql_files(self, platform: Platform | None = None) -> list[Path]:
        """
        Get SQL files for the specified platform or current platform.

        Lazy loads only the files for the specified platform.

        Args:
            platform: The platform to get SQL files for. If None, uses current platform.

        Returns:
            List of SQL file paths.
        """
        if platform is None:
            platform = self.current_platform

        sql_files = []

        if platform in [Platform.SNOWFLAKE, Platform.BOTH]:
            snowflake_dir = self.project_root / "snowflake"
            if snowflake_dir.exists():
                sql_files.extend(snowflake_dir.glob("*.sql"))

        if platform in [Platform.DATABRICKS, Platform.BOTH]:
            databricks_sql_dir = self.project_root / "databricks" / "sql"
            if databricks_sql_dir.exists():
                sql_files.extend(databricks_sql_dir.glob("*.sql"))

        return sorted(sql_files)

    def get_script_files(self, platform: Platform | None = None) -> list[Path]:
        """
        Get script files for the specified platform or current platform.

        Args:
            platform: The platform to get script files for. If None, uses current platform.

        Returns:
            List of script file paths.
        """
        if platform is None:
            platform = self.current_platform

        script_files = []

        if platform in [Platform.SNOWFLAKE, Platform.BOTH]:
            snowflake_scripts = self.project_root / "scripts" / "snowflake"
            if snowflake_scripts.exists():
                script_files.extend(snowflake_scripts.glob("*.py"))

        if platform in [Platform.DATABRICKS, Platform.BOTH]:
            databricks_scripts = self.project_root / "scripts" / "databricks"
            if databricks_scripts.exists():
                script_files.extend(databricks_scripts.glob("*.py"))

        return sorted(script_files)

    def get_gate_files(self, platform: Platform | None = None) -> list[Path]:
        """
        Get gate check files for the specified platform.

        Args:
            platform: The platform to get gate files for. If None, uses current platform.

        Returns:
            List of gate module paths.
        """
        gates_dir = self.project_root / "scripts" / "gates"

        if not gates_dir.exists():
            return []

        # Always include base gates
        base_gates = gates_dir / "base_gates.py"
        gate_files = [base_gates] if base_gates.exists() else []

        if platform is None:
            platform = self.current_platform

        if platform in [Platform.SNOWFLAKE, Platform.BOTH]:
            snowflake_gates = gates_dir / "snowflake_gates.py"
            if snowflake_gates.exists():
                gate_files.append(snowflake_gates)

        if platform in [Platform.DATABRICKS, Platform.BOTH]:
            databricks_gates = gates_dir / "databricks_gates.py"
            if databricks_gates.exists():
                gate_files.append(databricks_gates)

        return sorted(gate_files)

    def get_skill_paths(self, platform: Platform | None = None) -> list[Path]:
        """
        Get skill file paths for the specified platform.

        This enables platform-specific skill routing - only loading skills
        relevant to the current platform.

        Args:
            platform: The platform to get skill paths for. If None, uses current platform.

        Returns:
            List of skill directory paths.
        """
        if platform is None:
            platform = self.current_platform

        skill_paths = []
        cortex_dir = self.project_root / ".cortex" / "skills"

        if cortex_dir.exists():
            # Base skill path
            base_skill = cortex_dir / "streetlights-demo"
            if base_skill.exists():
                skill_paths.append(base_skill)

            # Platform-specific skill directories
            if platform in [Platform.SNOWFLAKE, Platform.BOTH]:
                snowflake_skill = cortex_dir / "streetlights-demo-snowflake"
                if snowflake_skill.exists():
                    skill_paths.append(snowflake_skill)

            if platform in [Platform.DATABRICKS, Platform.BOTH]:
                databricks_skill = cortex_dir / "streetlights-demo-databricks"
                if databricks_skill.exists():
                    skill_paths.append(databricks_skill)

        return sorted(skill_paths)

    def get_resource_paths(self, platform: Platform | None = None) -> list[Path]:
        """
        Get resource paths for the specified platform.

        Args:
            platform: The platform to get resources for. If None, uses current platform.

        Returns:
            List of resource paths that should be loaded.
        """
        if platform is None:
            platform = self.current_platform

        ALL_PLATFORM_RESOURCES = {
            Platform.SNOWFLAKE: [
                "init",
                "snowflake",
                "scripts/gate.py",
                "scripts/gates/snowflake_gates.py",
            ],
            Platform.DATABRICKS: [
                "init",
                "databricks",
                "scripts/gate.py",
                "scripts/gates/databricks_gates.py",
            ],
            Platform.BOTH: [
                "init",
                "snowflake",
                "databricks",
                "scripts/gate.py",
                "scripts/gates",
            ],
        }

        resource_patterns = ALL_PLATFORM_RESOURCES.get(platform, [])
        resource_paths = []

        for pattern in resource_patterns:
            if pattern.endswith(".py"):
                path = self.project_root / pattern
                if path.exists():
                    resource_paths.append(path)
            else:
                dir_path = self.project_root / pattern
                if dir_path.exists():
                    resource_paths.append(dir_path)

        return sorted(resource_paths)

    def assert_platform(self, required_platform: Platform) -> bool:
        """
        Assert that the current platform matches the required platform.

        Args:
            required_platform: The platform required for the operation.

        Returns:
            True if platform matches or is compatible.

        Raises:
            RuntimeError: If platform doesn't match.
        """
        if self.current_platform == Platform.UNKNOWN:
            raise RuntimeError(
                f"Cannot determine platform. Current platform: {self.current_platform}"
            )

        if required_platform == Platform.BOTH:
            return True

        if required_platform == Platform.SNOWFLAKE and not self.is_snowflake:
            raise RuntimeError(
                f"Operation requires Snowflake platform, "
                f"but current platform is: {self.current_platform.value}"
            )

        if required_platform == Platform.DATABRICKS and not self.is_databricks:
            raise RuntimeError(
                f"Operation requires Databricks platform, "
                f"but current platform is: {self.current_platform.value}"
            )

        return True

    def get_ignored_paths(self, platform: Platform | None = None) -> list[Path]:
        """
        Get the OTHER platform's resource paths — these are ignored when a
        single platform is explicitly chosen.

        Args:
            platform: The chosen platform. If None, uses current platform.

        Returns:
            Sorted list of paths belonging to the non-chosen platform(s).
            Empty for BOTH/UNKNOWN (nothing is ignored).
        """
        if platform is None:
            platform = self.current_platform

        if platform in (Platform.BOTH, Platform.UNKNOWN):
            return []

        ignored: list[Path] = []
        for other in (Platform.SNOWFLAKE, Platform.DATABRICKS):
            if other != platform:
                ignored.extend(self.get_resource_paths(other))
        return sorted(set(ignored))


# Global detector instance (lazy initialization)
_global_detector: PlatformDetector | None = None


def resolve_platform_choice(value: str) -> Platform:
    """Map a user-supplied platform choice string to a Platform.

    Accepts: snowflake/sf, databricks/dbx/db, both/all.
    Raises ValueError for anything else.
    """
    v = (value or "").lower().strip()
    if v in ("snowflake", "sf"):
        return Platform.SNOWFLAKE
    if v in ("databricks", "dbx", "db"):
        return Platform.DATABRICKS
    if v in ("both", "all"):
        return Platform.BOTH
    raise ValueError(f"Unknown platform choice: {value!r} (expected snowflake|databricks|both)")


def get_platform_detector(project_root: FilePath | None = None) -> PlatformDetector:
    """
    Get the global platform detector instance.

    Args:
        project_root: Optional project root. If provided, creates a new detector.

    Returns:
        The platform detector instance.
    """
    global _global_detector

    if project_root is not None:
        return PlatformDetector(project_root)

    if _global_detector is None:
        _global_detector = PlatformDetector()

    return _global_detector


def get_platform() -> Platform:
    """Get the current platform (UNKNOWN if nothing chosen)."""
    return get_platform_detector().current_platform


def require_platform() -> Platform:
    """Get the current platform; raise PlatformNotChosenError if none chosen."""
    return get_platform_detector().require_platform()


def is_snowflake() -> bool:
    """Check if current platform is Snowflake."""
    return get_platform_detector().is_snowflake


def is_databricks() -> bool:
    """Check if current platform is Databricks."""
    return get_platform_detector().is_databricks


def assert_snowflake() -> bool:
    """Assert that current platform is Snowflake."""
    return get_platform_detector().assert_platform(Platform.SNOWFLAKE)


def assert_databricks() -> bool:
    """Assert that current platform is Databricks."""
    return get_platform_detector().assert_platform(Platform.DATABRICKS)


def get_platform_sql_files() -> list[Path]:
    """Get SQL files for current platform."""
    return get_platform_detector().get_sql_files()


def get_platform_skill_paths() -> list[Path]:
    """Get skill paths for current platform."""
    return get_platform_detector().get_skill_paths()


if __name__ == "__main__":
    detector = PlatformDetector()
    try:
        platform = detector.require_platform()
    except PlatformNotChosenError as e:
        print(f"ERROR: {e}")
        raise SystemExit(1)

    print(f"Detected Platform: {platform.value}")
    print(f"  Is Snowflake: {detector.is_snowflake}")
    print(f"  Is Databricks: {detector.is_databricks}")
    print(f"  Is Both: {detector.is_both}")
    print()
    print(f"SQL Files: {len(detector.get_sql_files())}")
    print(f"Gate Files: {len(detector.get_gate_files())}")
    print(f"Skill Paths: {len(detector.get_skill_paths())}")
