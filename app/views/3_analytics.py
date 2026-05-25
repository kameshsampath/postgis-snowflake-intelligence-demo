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

import plotly.express as px
import streamlit as st

from snowflake.snowpark.context import get_active_session

st.title("Energy & Operational Analytics")

session = get_active_session()
db = (session.get_current_database() or "KAMESHS_STREETLIGHTS").strip('"')
cld_db = f"{db}_CLD"

# Energy consumption over time
st.subheader("Energy Consumption Over Time")
energy_time_df = session.sql(f"""
    SELECT
        DATE_TRUNC('month', "date") AS month,
        SUM("kwh") AS total_kwh
    FROM {cld_db}."streetlights"."energy_consumption"
    GROUP BY month
    ORDER BY month
""").to_pandas()

if not energy_time_df.empty:
    fig = px.line(
        energy_time_df,
        x="MONTH",
        y="TOTAL_KWH",
        title="Monthly Energy Consumption",
        labels={"MONTH": "Month", "TOTAL_KWH": "Total kWh"},
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No energy consumption data available.")

# Neighborhood comparison
st.subheader("Energy Consumption by Neighborhood")
neighborhood_df = session.sql(f"""
    SELECT
        sl."neighborhood" AS neighborhood,
        SUM(ec."kwh")            AS total_kwh,
        COUNT(DISTINCT sl."id")  AS light_count
    FROM {cld_db}."streetlights"."energy_consumption" ec
    JOIN {cld_db}."streetlights"."street_lights" sl
        ON ec."light_id" = sl."id"
    GROUP BY sl."neighborhood"
    ORDER BY total_kwh DESC
""").to_pandas()

if not neighborhood_df.empty:
    fig = px.bar(
        neighborhood_df,
        x="NEIGHBORHOOD",
        y="TOTAL_KWH",
        color="LIGHT_COUNT",
        color_continuous_scale="Blues",
        title="Total Energy by Neighborhood",
        labels={"NEIGHBORHOOD": "Neighborhood", "TOTAL_KWH": "Total kWh", "LIGHT_COUNT": "Lights"},
    )
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No neighborhood energy data available.")

# Operational status breakdown
st.subheader("Operational Status Breakdown")
status_df = session.sql(f"""
    SELECT
        "status"    AS status,
        COUNT(*) AS count
    FROM {cld_db}."streetlights"."street_lights"
    GROUP BY "status"
    ORDER BY count DESC
""").to_pandas()

if not status_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        fig_pie = px.pie(
            status_df,
            names="STATUS",
            values="COUNT",
            title="Status Distribution",
            color="STATUS",
            color_discrete_map={
                "operational": "#2ecc71",
                "faulty": "#e74c3c",
                "maintenance_required": "#f39c12",
            },
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        st.dataframe(status_df, use_container_width=True)

st.divider()

# Seasonal maintenance patterns (mirrors origin/cdc)
st.subheader("Seasonal Maintenance Patterns")
seasonal_df = session.sql(f"""
    SELECT
        we."season" AS season,
        COUNT(*)        AS request_count,
        AVG(mr."cost")  AS avg_cost
    FROM {cld_db}."streetlights"."maintenance_records" mr
    JOIN {cld_db}."streetlights"."weather_enrichment" we
        ON mr."date" = we."date"
    GROUP BY we."season"
    ORDER BY request_count DESC
""").to_pandas()

if not seasonal_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(
            seasonal_df,
            x="SEASON",
            y="REQUEST_COUNT",
            title="Maintenance Requests by Season",
            labels={"SEASON": "Season", "REQUEST_COUNT": "Requests"},
            color="SEASON",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(
            seasonal_df,
            x="SEASON",
            y="AVG_COST",
            title="Average Maintenance Cost by Season",
            labels={"SEASON": "Season", "AVG_COST": "Avg Cost (₹)"},
            color="SEASON",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No seasonal data available.")
