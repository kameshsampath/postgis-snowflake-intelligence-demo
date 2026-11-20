# Copyright 2025 Kamesh Sampath <kamesh.sampath@hotmail.com>
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Streamlit app for Databricks Apps — PostGIS Data Intelligence Demo (DBX path).
# Connects to the demo SQL warehouse with the app's service principal
# (oauth-m2m; DATABRICKS_CLIENT_ID/SECRET are injected into Databricks Apps).

import os

import pandas as pd
import streamlit as st

CATALOG = os.environ.get("DEMO_CATALOG", "pgdemo_streetlights")
SCHEMA = "streetlights"
WAREHOUSE_HTTP_PATH = os.environ.get("DATABRICKS_WAREHOUSE_HTTP_PATH", "")

st.set_page_config(
    page_title="Streetlights Intelligence (Databricks)", page_icon="💡", layout="wide"
)
st.title("Streetlights Intelligence Dashboard — Databricks")
st.caption("PostGIS Data Intelligence Demo · Lakebase + Unity Catalog + Genie")


def query(sql: str) -> pd.DataFrame:
    import databricks.sql as dbsql

    with dbsql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"],
        http_path=WAREHOUSE_HTTP_PATH,
        auth_type="oauth-m2m",
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d[0] for d in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=cols)


if not WAREHOUSE_HTTP_PATH:
    st.warning(
        "DATABRICKS_WAREHOUSE_HTTP_PATH is not set. In Databricks Apps, add the SQL "
        "warehouse as an app resource (see databricks.yml resources.apps) and set the "
        "http path, e.g. /sql/1.0/warehouses/<id>."
    )
    st.stop()

tab_overview, tab_map, tab_forecast = st.tabs(["Overview", "Neighborhood map", "Forecast"])

with tab_overview:
    st.subheader("KPIs")
    st.dataframe(query(f"SELECT * FROM {CATALOG}.{SCHEMA}.app_kpi_dashboard"))

with tab_map:
    st.subheader("Neighborhoods")
    df = query(f"SELECT * FROM {CATALOG}.{SCHEMA}.app_neighborhood_map")
    st.map(df.rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]])
    st.dataframe(df)

with tab_forecast:
    st.subheader("Energy forecast (ai_forecast)")
    st.dataframe(query(f"SELECT * FROM {CATALOG}.{SCHEMA}.energy_forecast ORDER BY date"))
