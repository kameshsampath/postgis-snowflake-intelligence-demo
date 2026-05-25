"""Typed manifest model and I/O for .streetlights-demo/manifest.toml.

This module is the single source of truth for reading and writing the
streetlights-demo manifest file. All other modules should import from here
rather than implementing their own TOML parsing.
"""

from __future__ import annotations

import os
import tempfile
import tomllib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

MANIFEST_REL_PATH = Path(".streetlights-demo") / "manifest.toml"

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

_OWNED_SECTIONS: set[str] = {"snowflake"}


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


@dataclass
class StepState:
    """State of a single workflow step."""

    status: str = ""
    desc: str = ""
    started_at: str = ""
    completed_at: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> StepState:
        return cls(
            status=data.get("status", ""),
            desc=data.get("desc", ""),
            started_at=data.get("started_at", ""),
            completed_at=data.get("completed_at", ""),
        )

    def to_dict(self) -> dict:
        d: dict = {}
        if self.status:
            d["status"] = self.status
        if self.desc:
            d["desc"] = self.desc
        if self.started_at:
            d["started_at"] = self.started_at
        if self.completed_at:
            d["completed_at"] = self.completed_at
        return d


@dataclass
class SnowflakeSection:
    """[snowflake] section of the manifest."""

    connection: str = ""
    role: str = ""
    admin_role: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> SnowflakeSection:
        return cls(
            connection=data.get("connection", ""),
            role=data.get("role", ""),
            admin_role=data.get("admin_role", ""),
        )

    def to_dict(self) -> dict:
        d: dict = {}
        if self.connection:
            d["connection"] = self.connection
        if self.role:
            d["role"] = self.role
        if self.admin_role:
            d["admin_role"] = self.admin_role
        return d


@dataclass
class DemoSection:
    """[streetlights-demo] section of the manifest."""

    prefix: str = ""
    database: str = ""
    cld_database: str = ""
    warehouse: str = ""
    pg_instance: str = ""
    pg_service: str = ""
    city: str = ""
    center_lat: float | None = None
    center_lng: float | None = None
    pg_host: str = ""
    pg_user: str = ""
    pg_network_policy: str = ""
    currency: str = "USD"
    currency_symbol: str = "$"
    steps: dict[str, StepState] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> DemoSection:
        raw_steps = data.get("steps", {})
        steps = {k: StepState.from_dict(v) for k, v in raw_steps.items()}
        return cls(
            prefix=data.get("prefix", ""),
            database=data.get("database", ""),
            cld_database=data.get("cld_database", ""),
            warehouse=data.get("warehouse", ""),
            pg_instance=data.get("pg_instance", ""),
            pg_service=data.get("pg_service", ""),
            city=data.get("city", ""),
            center_lat=data.get("center_lat"),
            center_lng=data.get("center_lng"),
            pg_host=data.get("pg_host", ""),
            pg_user=data.get("pg_user", ""),
            pg_network_policy=data.get("pg_network_policy", ""),
            currency=data.get("currency", "USD"),
            currency_symbol=data.get("currency_symbol", "$"),
            steps=steps,
        )

    def to_dict(self) -> dict:
        d: dict = {}
        if self.prefix:
            d["prefix"] = self.prefix
        if self.database:
            d["database"] = self.database
        if self.cld_database:
            d["cld_database"] = self.cld_database
        if self.warehouse:
            d["warehouse"] = self.warehouse
        if self.pg_instance:
            d["pg_instance"] = self.pg_instance
        if self.pg_service:
            d["pg_service"] = self.pg_service
        if self.city:
            d["city"] = self.city
        if self.center_lat is not None:
            d["center_lat"] = self.center_lat
        if self.center_lng is not None:
            d["center_lng"] = self.center_lng
        if self.pg_host:
            d["pg_host"] = self.pg_host
        if self.pg_user:
            d["pg_user"] = self.pg_user
        if self.pg_network_policy:
            d["pg_network_policy"] = self.pg_network_policy
        if self.currency:
            d["currency"] = self.currency
        if self.currency_symbol:
            d["currency_symbol"] = self.currency_symbol
        if self.steps:
            # Sort steps by chain order
            chain_order = list(STEP_CHAIN.keys())
            ordered = dict(
                sorted(
                    self.steps.items(),
                    key=lambda item: chain_order.index(item[0]) if item[0] in chain_order else 999,
                )
            )
            d["steps"] = {k: v.to_dict() for k, v in ordered.items()}
        return d


@dataclass
class Manifest:
    """Top-level manifest model."""

    schema_version: str = "1"
    project_name: str = "streetlights-demo"
    snowflake: SnowflakeSection = field(default_factory=SnowflakeSection)
    demo: DemoSection = field(default_factory=DemoSection)
    _extra: dict = field(default_factory=dict, repr=False)

    @property
    def demo_id(self) -> str:
        return self.project_name

    @classmethod
    def from_dict(cls, data: dict) -> Manifest:
        schema_version = data.get("schema_version", "1")
        project_name = data.get("project_name", "streetlights-demo")

        snowflake = SnowflakeSection.from_dict(data.get("snowflake", {}))
        demo = DemoSection.from_dict(data.get(project_name, {}))

        # Preserve non-owned sections
        owned = _OWNED_SECTIONS | {project_name}
        extra = {k: v for k, v in data.items() if isinstance(v, dict) and k not in owned}

        return cls(
            schema_version=schema_version,
            project_name=project_name,
            snowflake=snowflake,
            demo=demo,
            _extra=extra,
        )

    def to_dict(self) -> dict:
        d: dict = {}
        d["schema_version"] = self.schema_version
        d["project_name"] = self.project_name

        sf = self.snowflake.to_dict()
        if sf:
            d["snowflake"] = sf

        demo = self.demo.to_dict()
        if demo:
            d[self.demo_id] = demo

        # Append non-owned sections
        d.update(self._extra)
        return d


# ---------------------------------------------------------------------------
# TOML serializer
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
                    for sl in sub_lines.splitlines():
                        if sl and not sl.startswith("["):
                            lines.append(sl)
                        elif sl.startswith("["):
                            lines.append("")
                            lines.append(sl)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def find_project_root() -> Path:
    """Find project root by walking up from CWD looking for .streetlights-demo/manifest.toml."""
    current = Path.cwd()
    while True:
        if (current / MANIFEST_REL_PATH).exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    raise FileNotFoundError(
        "Could not find .streetlights-demo/manifest.toml in any parent directory"
    )


def load(project_root: Path) -> Manifest:
    """Load manifest.toml and return a typed Manifest model."""
    manifest_file = project_root / MANIFEST_REL_PATH
    with open(manifest_file, "rb") as f:
        data = tomllib.load(f)
    return Manifest.from_dict(data)


def save(project_root: Path, manifest: Manifest) -> None:
    """Atomically write manifest to disk."""
    manifest_file = project_root / MANIFEST_REL_PATH
    content = _serialize_toml(manifest.to_dict())
    if not content.endswith("\n"):
        content += "\n"

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


def update_step(project_root: Path, step: str, status: str, desc: str = "") -> None:
    """Update or create a step status in the manifest."""
    manifest = load(project_root)
    now = datetime.now(UTC).isoformat()

    step_state = manifest.demo.steps.get(step, StepState())

    step_state.status = status
    if status == "IN_PROGRESS":
        step_state.started_at = now
        if desc:
            step_state.desc = desc
    elif status == "COMPLETE":
        step_state.completed_at = now
        if desc:
            step_state.desc = desc

    manifest.demo.steps[step] = step_state
    save(project_root, manifest)


def remove_step(project_root: Path, step: str) -> None:
    """Remove a step section entirely from the manifest."""
    manifest = load(project_root)
    if step in manifest.demo.steps:
        del manifest.demo.steps[step]
        save(project_root, manifest)
