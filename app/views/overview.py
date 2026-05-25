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

import streamlit as st

from snowflake.snowpark.context import get_active_session

st.title("Streetlights Intelligence Dashboard")

session = get_active_session()
db = (session.get_current_database() or "KAMESHS_STREETLIGHTS").strip('"')
cld_db = f"{db}_CLD"

try:
    kpi_df = session.sql(f"""
        SELECT
            COUNT(*)                                                              AS total_lights,
            SUM(CASE WHEN "status" = 'operational'          THEN 1 ELSE 0 END)
                AS operational_count,
            SUM(CASE WHEN "status" = 'faulty'               THEN 1 ELSE 0 END)
                AS faulty_count,
            SUM(CASE WHEN "status" = 'maintenance_required' THEN 1 ELSE 0 END)
                AS maintenance_count,
            COUNT(DISTINCT "neighborhood")                                        AS neighborhoods
        FROM {cld_db}."streetlights"."street_lights"
    """).to_pandas()

    row = kpi_df.iloc[0]
    total = int(row["TOTAL_LIGHTS"])
    op_pct = round(100.0 * int(row["OPERATIONAL_COUNT"]) / total, 1) if total else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Streetlights", f"{total:,}")
    col2.metric("Operational", f"{op_pct}%", f"{int(row['OPERATIONAL_COUNT']):,}")
    col3.metric("Faulty", f"{int(row['FAULTY_COUNT']):,}", delta_color="inverse")
    col4.metric("Maintenance Required", f"{int(row['MAINTENANCE_COUNT']):,}", delta_color="off")
    col5.metric("Neighborhoods", int(row["NEIGHBORHOODS"]))

except Exception as e:
    st.warning(f"Could not load metrics: {e}")

st.divider()

st.markdown("""
| Page | What it shows |
|---|---|
| **Neighborhood Overview** | All streetlights on an interactive map — color-coded by status |
| **Faulty Lights** | Faulty lights with maintenance history and neighborhood breakdown |
| **Analytics** | Energy trends, neighborhood comparisons, seasonal maintenance patterns |
| **Energy Forecast** | ML-powered energy consumption predictions (Snowflake ML Forecast) |

Use **Snowflake Intelligence** to chat with the streetlights agent for cross-source Q&A.
""")
