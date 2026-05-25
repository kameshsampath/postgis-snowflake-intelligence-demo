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

import pydeck as pdk
import streamlit as st

from snowflake.snowpark.context import get_active_session

st.title("Neighborhood Overview")
st.markdown("Interactive map showing all streetlights color-coded by operational status.")

session = get_active_session()
db = (session.get_current_database() or "KAMESHS_STREETLIGHTS").strip('"')
cld_db = f"{db}_CLD"

STATUS_COLORS = {
    "operational": [46, 204, 113],
    "faulty": [231, 76, 60],
    "maintenance_required": [243, 156, 18],
}

ALL_STATUSES = ["operational", "faulty", "maintenance_required"]

# Load all lights
all_df = session.sql(f"""
    SELECT
        "id"           AS light_id,
        "pole_id"      AS pole_id,
        "latitude"     AS lat,
        "longitude"    AS lon,
        "status"       AS status,
        "neighborhood" AS neighborhood,
        "wattage"      AS wattage,
        "light_type"   AS light_type
    FROM {cld_db}."streetlights"."street_lights"
    WHERE "latitude" IS NOT NULL AND "longitude" IS NOT NULL
""").to_pandas()

# Summary metrics
total = len(all_df)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Lights", f"{total:,}")
col2.metric(
    "Operational",
    f"{len(all_df[all_df['STATUS'] == 'operational']):,}",
    f"{100*len(all_df[all_df['STATUS']=='operational'])/total:.1f}%",
)
col3.metric(
    "Faulty",
    f"{len(all_df[all_df['STATUS'] == 'faulty']):,}",
    f"{100*len(all_df[all_df['STATUS']=='faulty'])/total:.1f}%",
    delta_color="inverse",
)
col4.metric(
    "Maintenance Required",
    f"{len(all_df[all_df['STATUS'] == 'maintenance_required']):,}",
)

st.divider()

# Filters
col1, col2 = st.columns(2)
with col1:
    neighborhoods = sorted(all_df["NEIGHBORHOOD"].dropna().unique().tolist())
    selected_nh = st.multiselect("Filter by Neighborhood", neighborhoods, default=[])

with col2:
    selected_status = st.multiselect(
        "Filter by Status",
        ALL_STATUSES,
        default=ALL_STATUSES,
        format_func=lambda s: s.replace("_", " ").title(),
    )

# Apply filters
filtered_df = all_df.copy()
if selected_nh:
    filtered_df = filtered_df[filtered_df["NEIGHBORHOOD"].isin(selected_nh)]
if selected_status:
    filtered_df = filtered_df[filtered_df["STATUS"].isin(selected_status)]

st.caption(f"Showing {len(filtered_df):,} of {total:,} lights")

# Color map
filtered_df["color"] = filtered_df["STATUS"].map(lambda s: STATUS_COLORS.get(s, [149, 165, 166]))

# Power grid zones
zones_df = session.sql(f"""
    SELECT
        "zone_name"          AS zone_name,
        ROUND(
            100.0 * "current_load_kw" / NULLIF("capacity_kw", 0), 1
        )                    AS util_pct,
        "latitude"           AS lat,
        "longitude"          AS lon
    FROM {cld_db}."streetlights"."power_grid_zones"
""").to_pandas()

zones_df["color"] = zones_df["UTIL_PCT"].apply(
    lambda u: [231, 76, 60] if u > 80 else ([243, 156, 18] if u > 50 else [46, 204, 113])
)

# deck.gl tooltip needs plain JS objects — Arrow StructRows break {field} substitution.
# Convert to list[dict] (JSON) so object["pole_id"] resolves correctly in the tooltip.
pdk_lights = filtered_df.rename(columns=str.lower).to_dict("records")
pdk_zones = zones_df.rename(columns=str.lower).to_dict("records")

# Map
layer = pdk.Layer(
    "ScatterplotLayer",
    data=pdk_lights,
    get_position=["lon", "lat"],
    get_fill_color="color",
    get_radius=40,
    pickable=True,
    auto_highlight=True,
)

zones_layer = pdk.Layer(
    "ScatterplotLayer",
    data=pdk_zones,
    get_position=["lon", "lat"],
    get_fill_color="color",
    get_radius=200,
    pickable=True,
    auto_highlight=True,
)

view = pdk.ViewState(
    latitude=filtered_df["LAT"].mean() if not filtered_df.empty else all_df["LAT"].mean(),
    longitude=filtered_df["LON"].mean() if not filtered_df.empty else all_df["LON"].mean(),
    zoom=11,
    pitch=0,
)

st.pydeck_chart(
    pdk.Deck(
        layers=[layer, zones_layer],
        initial_view_state=view,
        tooltip={"html": "<b>{pole_id}</b>  ·  {status}  ·  {neighborhood}"},
    )
)

# Zone legend
st.caption(
    "Zone dots: "
    '<span style="color:#2ecc71">●</span> &lt;50% load &nbsp;&nbsp;'
    '<span style="color:#f39c12">●</span> 50–80% load &nbsp;&nbsp;'
    '<span style="color:#e74c3c">●</span> &gt;80% load',
    unsafe_allow_html=True,
)

# Legend
st.markdown(
    " &nbsp;&nbsp; ".join(
        [
            '<span style="color:#2ecc71">●</span> Operational',
            '<span style="color:#e74c3c">●</span> Faulty',
            '<span style="color:#f39c12">●</span> Maintenance Required',
        ]
    ),
    unsafe_allow_html=True,
)

st.divider()

# Neighborhood stats table
st.subheader("Neighborhood Statistics")
stats_df = session.sql(f"""
    SELECT
        "neighborhood"  AS neighborhood,
        COUNT(*)                                                              AS total_lights,
        SUM(CASE WHEN "status" = 'operational'          THEN 1 ELSE 0 END)  AS operational,
        SUM(CASE WHEN "status" = 'faulty'               THEN 1 ELSE 0 END)  AS faulty,
        SUM(CASE WHEN "status" = 'maintenance_required' THEN 1 ELSE 0 END)
            AS maintenance_required,
        ROUND(
            100.0 * SUM(CASE WHEN "status" = 'faulty' THEN 1 ELSE 0 END) / COUNT(*), 1
        )                                                                     AS faulty_pct
    FROM {cld_db}."streetlights"."street_lights"
    GROUP BY "neighborhood"
    ORDER BY faulty_pct DESC
""").to_pandas()

st.dataframe(
    stats_df.style.background_gradient(subset=["FAULTY_PCT"], cmap="Reds").format(
        {"FAULTY_PCT": "{:.1f}%"}
    ),
    use_container_width=True,
)
