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

import numpy as np
import plotly.express as px
import pydeck as pdk
import streamlit as st

from snowflake.snowpark.context import get_active_session

st.title("Faulty Lights Analysis")
st.markdown(
    "Click a red dot on the map — or pick a pole from the list — "
    "to see which grid zone it stresses and which technician to dispatch."
)

session = get_active_session()
db = (session.get_current_database() or "KAMESHS_STREETLIGHTS").strip('"')
cld_db = f"{db}_CLD"

# ── data loading ──────────────────────────────────────────────────────────────
faulty_df = session.sql(f"""
    SELECT
        sl."id"            AS light_id,
        sl."pole_id"       AS pole_id,
        sl."neighborhood"  AS neighborhood,
        sl."latitude"      AS lat,
        sl."longitude"     AS lon,
        sl."wattage"       AS wattage,
        sl."light_type"    AS light_type,
        COUNT(mr."id")              AS maintenance_count,
        MAX(mr."date")              AS last_maintenance,
        AVG(mr."cost")              AS avg_cost,
        MAX(mr."type")              AS last_type
    FROM {cld_db}."streetlights"."street_lights" sl
    LEFT JOIN {cld_db}."streetlights"."maintenance_records" mr
        ON mr."light_id" = sl."id"
    WHERE sl."status" = 'faulty'
    GROUP BY sl."id", sl."pole_id", sl."neighborhood",
             sl."latitude", sl."longitude", sl."wattage", sl."light_type"
    ORDER BY sl."neighborhood", sl."id"
""").to_pandas()

zones_df = session.sql(f"""
    SELECT
        "zone_id"         AS zone_id,
        "zone_name"       AS zone_name,
        "capacity_kw"     AS capacity_kw,
        "current_load_kw" AS current_load_kw,
        ROUND(100.0 * "current_load_kw" / NULLIF("capacity_kw", 0), 1) AS util_pct,
        "latitude"        AS lat,
        "longitude"       AS lon
    FROM {cld_db}."streetlights"."power_grid_zones"
    ORDER BY util_pct DESC
""").to_pandas()


def _zone_color(u):
    if u is None or (isinstance(u, float) and np.isnan(u)):
        return [149, 165, 166]
    if u > 80:
        return [231, 76, 60]
    if u > 50:
        return [243, 156, 18]
    return [46, 204, 113]


zones_df["color"] = zones_df["UTIL_PCT"].apply(_zone_color)

total_lights_df = session.sql(f"""
    SELECT COUNT(*) AS total FROM {cld_db}."streetlights"."street_lights"
""").to_pandas()
total_lights = int(total_lights_df["TOTAL"].iloc[0])
total_faulty = len(faulty_df)
faulty_pct = round(100.0 * total_faulty / total_lights, 2) if total_lights else 0
avg_cost = faulty_df["AVG_COST"].mean() if not faulty_df.empty else 0

# ── metrics ───────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Faulty Lights", f"{total_faulty:,}")
col2.metric("% of Total", f"{faulty_pct:.2f}%", delta_color="inverse")
col3.metric("Avg Maintenance Cost", f"₹{avg_cost:,.2f}" if avg_cost else "N/A")

st.divider()

# ── filters ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    neighborhoods = sorted(faulty_df["NEIGHBORHOOD"].dropna().unique().tolist())
    selected_nh = st.multiselect("Filter by Neighborhood", neighborhoods, default=[])
with col2:
    max_cost = float(faulty_df["AVG_COST"].max()) if not faulty_df.empty else 2000.0
    cost_filter = st.slider("Max Avg Maintenance Cost (₹)", 0.0, max_cost, max_cost, step=50.0)

filtered_df = faulty_df.copy()
if selected_nh:
    filtered_df = filtered_df[filtered_df["NEIGHBORHOOD"].isin(selected_nh)]
filtered_df = filtered_df[filtered_df["AVG_COST"].fillna(0) <= cost_filter]

st.caption(f"Showing {len(filtered_df):,} of {total_faulty:,} faulty lights")

# ── haversine enrichment ──────────────────────────────────────────────────────


def _nearest_zone(lat, lon, z_df):
    """Return (zone_name, dist_km, util_pct) for the closest power grid zone."""
    R = 6371.0
    lat1 = np.radians(lat)
    lon1 = np.radians(lon)
    lat2 = np.radians(z_df["LAT"].values)
    lon2 = np.radians(z_df["LON"].values)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    dist = 2 * R * np.arcsin(np.sqrt(a))
    idx = int(np.argmin(dist))
    return (
        z_df["ZONE_NAME"].iloc[idx],
        round(float(dist[idx]), 2),
        float(z_df["UTIL_PCT"].iloc[idx]),
    )


if not zones_df.empty and not filtered_df.empty:
    enriched = filtered_df.apply(
        lambda r: _nearest_zone(r["LAT"], r["LON"], zones_df),
        axis=1,
        result_type="expand",
    )
    enriched.columns = ["NEAREST_ZONE", "ZONE_DIST_KM", "ZONE_UTIL_PCT"]
    filtered_df = filtered_df.join(enriched)
else:
    filtered_df["NEAREST_ZONE"] = "N/A"
    filtered_df["ZONE_DIST_KM"] = None
    filtered_df["ZONE_UTIL_PCT"] = None

# ── recommended technician per neighborhood ───────────────────────────────────
rec_tech_df = session.sql(f"""
    SELECT neighborhood, technician
    FROM (
        SELECT
            sl."neighborhood"  AS neighborhood,
            mr."technician"    AS technician,
            COUNT(*)           AS n,
            ROW_NUMBER() OVER (
                PARTITION BY sl."neighborhood" ORDER BY COUNT(*) DESC
            ) AS rn
        FROM {cld_db}."streetlights"."maintenance_records" mr
        JOIN {cld_db}."streetlights"."street_lights" sl
            ON mr."light_id" = sl."id"
        GROUP BY sl."neighborhood", mr."technician"
    ) t WHERE rn = 1
""").to_pandas()

tech_map = dict(zip(rec_tech_df["NEIGHBORHOOD"], rec_tech_df["TECHNICIAN"]))
filtered_df["REC_TECHNICIAN"] = filtered_df["NEIGHBORHOOD"].map(tech_map).fillna("Unassigned")

# ── overview map ──────────────────────────────────────────────────────────────
st.subheader("Faulty Lights & Power Grid Zones")
st.caption(
    "**Red** = faulty lights  |  Zone dots colored by grid load  |  "
    "Lines connect each light to its nearest zone  |  Click a red dot to inspect"
)

map_df = filtered_df.dropna(subset=["LAT", "LON"]).copy()

if not map_df.empty:
    zone_coords = zones_df[["ZONE_NAME", "LAT", "LON"]].rename(
        columns={"ZONE_NAME": "NEAREST_ZONE", "LAT": "ZONE_LAT", "LON": "ZONE_LON"}
    )
    map_df = map_df.merge(zone_coords, on="NEAREST_ZONE", how="left")

    # deck.gl tooltip needs plain JS objects — Arrow StructRows break {field} substitution.
    # Convert to list[dict] (JSON) so object["pole_id"] resolves correctly in the tooltip.
    pdk_map = map_df.rename(columns=str.lower).to_dict("records")
    pdk_zones = zones_df.rename(columns=str.lower).to_dict("records")

    view = pdk.ViewState(
        latitude=map_df["LAT"].mean(),
        longitude=map_df["LON"].mean(),
        zoom=11,
        pitch=0,
    )
    lines_layer = pdk.Layer(
        "LineLayer",
        data=pdk_map,
        get_source_position=["lon", "lat"],
        get_target_position=["zone_lon", "zone_lat"],
        get_color=[231, 76, 60, 60],
        get_width=1,
    )
    zones_layer = pdk.Layer(
        "ScatterplotLayer",
        id="zones",
        data=pdk_zones,
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius=200,
        pickable=True,
        auto_highlight=True,
    )
    lights_layer = pdk.Layer(
        "ScatterplotLayer",
        id="lights",
        data=pdk_map,
        get_position=["lon", "lat"],
        get_fill_color=[231, 76, 60],
        get_radius=50,
        pickable=True,
        auto_highlight=True,
    )
    st.pydeck_chart(
        pdk.Deck(
            layers=[lines_layer, zones_layer, lights_layer],
            initial_view_state=view,
            tooltip={"html": "<b>{pole_id}</b>  ·  {neighborhood}"},
        ),
    )
    st.caption(
        "Zone dots: "
        '<span style="color:#2ecc71">●</span> &lt;50% load &nbsp;&nbsp;'
        '<span style="color:#f39c12">●</span> 50–80% load &nbsp;&nbsp;'
        '<span style="color:#e74c3c">●</span> &gt;80% load',
        unsafe_allow_html=True,
    )
else:
    st.info("No faulty lights match the selected filters.")

# ── neighborhood chart ────────────────────────────────────────────────────────
st.divider()
st.subheader("Faulty Lights by Neighborhood")
if not filtered_df.empty:
    nh_counts = (
        filtered_df.groupby("NEIGHBORHOOD")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    fig = px.bar(
        nh_counts,
        x="NEIGHBORHOOD",
        y="count",
        title="Faulty Lights Count by Neighborhood",
        labels={"NEIGHBORHOOD": "Neighborhood", "count": "Faulty Lights"},
        color="count",
        color_continuous_scale="Reds",
    )
    fig.update_layout(xaxis_tickangle=-35, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

# ── light inspector ───────────────────────────────────────────────────────────
st.divider()
st.subheader("Light Inspector")
st.caption("Click a row to inspect that pole and get a Snowflake Intelligence query suggestion.")

selected_pole = None

if not filtered_df.empty:
    selector_cols = ["POLE_ID", "NEIGHBORHOOD"]
    if "NEAREST_ZONE" in filtered_df.columns:
        selector_cols += ["NEAREST_ZONE", "ZONE_UTIL_PCT"]
    selector_df = (
        filtered_df[selector_cols]
        .drop_duplicates(subset=["POLE_ID"])
        .sort_values("POLE_ID")
        .reset_index(drop=True)
    )
    pole_event = st.dataframe(
        selector_df,
        on_select="rerun",
        selection_mode="single-row",
        use_container_width=True,
        hide_index=True,
    )
    if pole_event.selection["rows"]:
        selected_pole = str(selector_df.iloc[pole_event.selection["rows"][0]]["POLE_ID"])

if selected_pole:
    matches = filtered_df[filtered_df["POLE_ID"] == selected_pole]
    if matches.empty:
        st.warning(f"Pole {selected_pole} is not in the current filter set.")
    else:
        row = matches.iloc[0]
        neighborhood = str(row["NEIGHBORHOOD"])
        rec_tech = str(row["REC_TECHNICIAN"])
        zone_name = str(row.get("NEAREST_ZONE", "N/A"))
        zone_dist = row.get("ZONE_DIST_KM")
        zone_util = row.get("ZONE_UTIL_PCT")

        st.code(selected_pole, language=None)
        st.caption("Copy this pole ID to use in Snowflake Intelligence queries")

        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Neighborhood", neighborhood)
        zone_label = zone_name + (f"  ({zone_dist} km)" if zone_dist else "")
        mc2.metric("Nearest Zone", zone_label)
        if zone_util is not None:
            mc3.metric(
                "Zone Load",
                f"{zone_util:.1f}%",
                delta_color="inverse" if zone_util > 80 else "normal",
            )

        st.success(f"Recommended Technician: **{rec_tech}**")

        # Technician work history in the same neighborhood
        safe_tech = rec_tech.replace("'", "''")
        safe_nh = neighborhood.replace("'", "''")
        hist_df = session.sql(f"""
            SELECT
                sl."latitude"   AS lat,
                sl."longitude"  AS lon,
                sl."pole_id"    AS pole_id,
                mr."date"       AS maint_date,
                mr."type"       AS maint_type,
                mr."cost"       AS cost
            FROM {cld_db}."streetlights"."maintenance_records" mr
            JOIN {cld_db}."streetlights"."street_lights" sl
                ON mr."light_id" = sl."id"
            WHERE mr."technician"   = '{safe_tech}'
              AND sl."neighborhood" = '{safe_nh}'
            ORDER BY mr."date" DESC
            LIMIT 50
        """).to_pandas()

        # 4-layer detail map
        sel_lat = float(row["LAT"])
        sel_lon = float(row["LON"])
        zone_row = zones_df[zones_df["ZONE_NAME"] == zone_name]
        zone_lat = float(zone_row["LAT"].iloc[0]) if not zone_row.empty else sel_lat
        zone_lon = float(zone_row["LON"].iloc[0]) if not zone_row.empty else sel_lon

        # Plain JS objects (list[dict]) for tooltip {field} substitution — see Arrow note above
        pdk_zone_pin = zone_row.rename(columns=str.lower).to_dict("records")
        pdk_hist = (
            hist_df.dropna(subset=["LAT", "LON"]).rename(columns=str.lower).to_dict("records")
            if not hist_df.empty
            else []
        )

        conn_data = [{"sx": sel_lon, "sy": sel_lat, "tx": zone_lon, "ty": zone_lat}]
        detail_view = pdk.ViewState(latitude=sel_lat, longitude=sel_lon, zoom=13, pitch=0)
        conn_layer = pdk.Layer(
            "LineLayer",
            data=conn_data,
            get_source_position=["sx", "sy"],
            get_target_position=["tx", "ty"],
            get_color=[231, 76, 60],
            get_width=3,
        )
        zone_pin = pdk.Layer(
            "ScatterplotLayer",
            data=pdk_zone_pin,
            get_position=["lon", "lat"],
            get_fill_color="color",
            get_radius=250,
            pickable=True,
        )
        hist_layer = pdk.Layer(
            "ScatterplotLayer",
            data=pdk_hist,
            get_position=["lon", "lat"],
            get_fill_color=[46, 204, 113],
            get_radius=35,
            pickable=True,
        )
        selected_layer = pdk.Layer(
            "ScatterplotLayer",
            data=[{"lon": sel_lon, "lat": sel_lat, "pole_id": selected_pole}],
            get_position=["lon", "lat"],
            get_fill_color=[231, 76, 60],
            get_radius=60,
            pickable=True,
        )
        st.pydeck_chart(
            pdk.Deck(
                layers=[conn_layer, zone_pin, hist_layer, selected_layer],
                initial_view_state=detail_view,
                tooltip={"html": "<b>{pole_id}</b>  ·  {maint_type}  ·  ₹{cost}"},
            )
        )
        st.caption(
            f"**Green dots** = {rec_tech}'s previous jobs in {neighborhood}  "
            f"|  **Red dot** = {selected_pole}  "
            f"|  **Zone dot** = {zone_name}"
        )

        if not hist_df.empty:
            st.dataframe(
                hist_df[["POLE_ID", "MAINT_DATE", "MAINT_TYPE", "COST"]].rename(
                    columns={
                        "POLE_ID": "Pole",
                        "MAINT_DATE": "Date",
                        "MAINT_TYPE": "Type",
                        "COST": "Cost (₹)",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

        st.divider()
        st.markdown("**Try this with Snowflake Intelligence:**")
        si_q = (
            f"Who has the most experience fixing faulty lights in {neighborhood}? "
            f"Show their recent repair history and the grid zones they have worked near."
        )
        st.code(si_q, language=None)
        st.caption("Paste into Snowflake Intelligence →")

# ── detail table ──────────────────────────────────────────────────────────────
st.divider()
st.subheader("Faulty Lights Detail")
if not filtered_df.empty:
    cols = [
        "POLE_ID",
        "NEIGHBORHOOD",
        "LIGHT_TYPE",
        "WATTAGE",
        "MAINTENANCE_COUNT",
        "LAST_MAINTENANCE",
        "AVG_COST",
        "LAST_TYPE",
    ]
    if "NEAREST_ZONE" in filtered_df.columns:
        cols += ["NEAREST_ZONE", "ZONE_DIST_KM", "ZONE_UTIL_PCT", "REC_TECHNICIAN"]
    display_df = filtered_df[cols].copy()
    st.dataframe(
        display_df.style.background_gradient(subset=["AVG_COST"], cmap="Reds"),
        use_container_width=True,
    )
else:
    st.info("No data to display.")
