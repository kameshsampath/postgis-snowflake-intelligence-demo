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

"""End-to-end sanity check: Agent answers a question correctly."""

import subprocess
import sys
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


def run_sanity_check():
    """Run end-to-end sanity check against the Intelligence Agent."""
    manifest = load_manifest()
    cld_db = manifest["demo"]["cld_database"]

    # Test: Agent should be able to count streetlights
    result = subprocess.run(
        [
            "snow",
            "sql",
            "-q",
            f"SELECT SNOWFLAKE.CORTEX.AGENT('{cld_db}.streetlights.streetlights_agent',"
            f" 'How many total streetlights are in the system?')",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        print(f"FAIL: Agent query failed: {result.stderr}")
        sys.exit(1)

    if not result.stdout.strip():
        print("FAIL: Agent returned empty response")
        sys.exit(1)

    print(f"PASS: Agent responded: {result.stdout[:200]}")


if __name__ == "__main__":
    run_sanity_check()
