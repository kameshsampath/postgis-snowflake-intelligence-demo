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

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")
st.title("Energy & Operational Analytics")

session = get_active_session()

# Energy consumption over time
st.subheader("Energy Consumption Over Time")
energy_time_df = session.sql("""
    SELECT
        DATE_TRUNC('month', "reading_date") AS month,
        SUM("kwh_consumed") AS total_kwh
    FROM "streetlights"."energy_consumption"
    GROUP BY month
    ORDER BY month
""").to_pandas()

if not energy_time_df.empty:
    st.line_chart(energy_time_df.set_index("MONTH")["TOTAL_KWH"])
else:
    st.info("No energy consumption data available.")

# Neighborhood comparison
st.subheader("Energy Consumption by Neighborhood")
neighborhood_df = session.sql("""
    SELECT
        sl."neighborhood_id",
        SUM(ec."kwh_consumed") AS total_kwh,
        COUNT(DISTINCT sl."light_id") AS light_count
    FROM "streetlights"."energy_consumption" ec
    JOIN "streetlights"."street_lights" sl
        ON ec."light_id" = sl."light_id"
    GROUP BY sl."neighborhood_id"
    ORDER BY total_kwh DESC
""").to_pandas()

if not neighborhood_df.empty:
    st.bar_chart(neighborhood_df.set_index("NEIGHBORHOOD_ID")["TOTAL_KWH"])
else:
    st.info("No neighborhood energy data available.")

# Operational status breakdown
st.subheader("Operational Status Breakdown")
status_df = session.sql("""
    SELECT
        "status",
        COUNT(*) AS count
    FROM "streetlights"."street_lights"
    GROUP BY "status"
    ORDER BY count DESC
""").to_pandas()

if not status_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(status_df, use_container_width=True)
    with col2:
        st.bar_chart(status_df.set_index("STATUS")["COUNT"])
