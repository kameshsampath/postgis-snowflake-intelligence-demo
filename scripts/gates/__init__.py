"""Gate check modules for PostGIS Data Intelligence Demo.

This package contains platform-specific gate check modules:
- base_gates.py: Common gate checks and utilities
- snowflake_gates.py: Snowflake-specific gate checks
- databricks_gates.py: Databricks-specific gate checks
"""

from scripts.gates.base_gates import (
    GateResult,
    check_csv_files,
    check_csv_neighborhood_names,
    check_manifest,
    check_step1_complete,
)
from scripts.gates.databricks_gates import (
    check_dbx_all,
    check_dbx_app_deployed,
    check_dbx_forecast_ready,
    check_genie_space_active,
    check_lakebase_reachable,
    check_uc_sync_healthy,
    check_vector_index_ready,
)
from scripts.gates.snowflake_gates import (
    check_account_params,
    check_cld_healthy,
    check_cortex_search,
    check_pg_network_access,
    check_pg_reachable,
    check_pg_tables,
    check_semantic_view,
    check_snowflake_connection,
)

__all__ = [
    # Base
    "GateResult",
    "check_manifest",
    "check_csv_files",
    "check_csv_neighborhood_names",
    "check_step1_complete",
    # Snowflake
    "check_snowflake_connection",
    "check_pg_reachable",
    "check_pg_tables",
    "check_cld_healthy",
    "check_account_params",
    "check_pg_network_access",
    "check_semantic_view",
    "check_cortex_search",
    # Databricks
    "check_lakebase_reachable",
    "check_uc_sync_healthy",
    "check_genie_space_active",
    "check_vector_index_ready",
    "check_dbx_forecast_ready",
    "check_dbx_app_deployed",
    "check_dbx_all",
]
