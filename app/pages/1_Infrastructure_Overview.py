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

st.set_page_config(page_title="Infrastructure Overview", page_icon="🗺️", layout="wide")
st.title("Infrastructure Overview")

session = get_active_session()

# Summary metrics
metrics_df = session.sql("""
    SELECT
        COUNT(*) AS total_lights,
        ROUND(
            100.0 * SUM(CASE WHEN "status" = 'active' THEN 1 ELSE 0 END)
            / COUNT(*), 1
        ) AS active_pct,
        ROUND(AVG("wattage"), 1) AS avg_wattage
    FROM "streetlights"."street_lights"
""").to_pandas()

col1, col2, col3 = st.columns(3)
col1.metric("Total Streetlights", int(metrics_df["TOTAL_LIGHTS"].iloc[0]))
col2.metric("Active %", f"{metrics_df['ACTIVE_PCT'].iloc[0]}%")
col3.metric("Avg Wattage", f"{metrics_df['AVG_WATTAGE'].iloc[0]} W")

# Map visualization
st.subheader("Streetlight Locations")
map_df = session.sql("""
    SELECT
        "latitude" AS lat,
        "longitude" AS lon,
        "light_id",
        "status"
    FROM "streetlights"."street_lights"
    WHERE "latitude" IS NOT NULL AND "longitude" IS NOT NULL
""").to_pandas()

st.map(map_df, latitude="lat", longitude="lon")

# Data table
st.subheader("Streetlight Details")
details_df = session.sql("""
    SELECT
        "light_id",
        "neighborhood_id",
        "status",
        "light_type",
        "wattage",
        "installation_date"
    FROM "streetlights"."street_lights"
    ORDER BY "light_id"
    LIMIT 100
""").to_pandas()

st.dataframe(details_df, use_container_width=True)
