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
import plotly.graph_objects as go
import streamlit as st

from snowflake.snowpark.context import get_active_session

st.title("Energy Forecast")
st.markdown("ML-powered predictions using Snowflake ML Forecast.")

session = get_active_session()
db = (session.get_current_database() or "KAMESHS_STREETLIGHTS").strip('"')
cld_db = f"{db}_CLD"

# Guard: check if ENERGY_FORECAST model has been trained
try:
    show_rows = session.sql(f"SHOW SNOWFLAKE.ML.FORECAST IN SCHEMA {db}.PUBLIC").collect()
    model_names = [r["name"].upper() for r in show_rows]
    if "ENERGY_FORECAST" not in model_names:
        st.info(
            "The ML Forecast model has not been trained yet. "
            "Run `$streetlights-demo app` (or `$streetlights-demo step 8`) to train it."
        )
        st.stop()
except Exception:
    st.info(
        "ML Forecast model unavailable. "
        "Run `$streetlights-demo app` (or `$streetlights-demo step 8`) to train it."
    )
    st.stop()

# Forecast parameters
forecast_days = st.slider("Forecast horizon (days):", min_value=7, max_value=90, value=30)

if st.button("Generate Forecast"):
    with st.spinner("Running forecast model..."):
        try:
            forecast_df = session.sql(f"""
                CALL {db}.PUBLIC.energy_forecast!FORECAST(
                    FORECASTING_PERIODS => {forecast_days},
                    CONFIG_OBJECT => {{'prediction_interval': 0.95}}
                )
            """).to_pandas()
        except Exception as e:
            err = str(e)
            if "exogenous" in err.lower():
                st.warning(
                    "The forecast model was trained with exogenous features "
                    "(location columns). Retrain it with the updated SQL: "
                    "run `$streetlights-demo step 8`."
                )
            else:
                st.error(f"Forecast error: {err}")
            st.stop()

    if not forecast_df.empty:
        # Aggregate multi-series (per light_id) to overall trend
        agg = (
            forecast_df.groupby("TS")
            .agg(
                FORECAST=("FORECAST", "mean"),
                LOWER_BOUND=("LOWER_BOUND", "mean"),
                UPPER_BOUND=("UPPER_BOUND", "mean"),
            )
            .reset_index()
            .sort_values("TS")
        )

        st.subheader("Predicted Energy Consumption")
        fig = go.Figure(
            [
                go.Scatter(
                    x=agg["TS"],
                    y=agg["UPPER_BOUND"],
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                ),
                go.Scatter(
                    x=agg["TS"],
                    y=agg["LOWER_BOUND"],
                    mode="lines",
                    fill="tonexty",
                    fillcolor="rgba(99,110,250,0.15)",
                    line=dict(width=0),
                    name="95% interval",
                ),
                go.Scatter(
                    x=agg["TS"],
                    y=agg["FORECAST"],
                    mode="lines",
                    line=dict(color="#636efa", width=2),
                    name="Forecast",
                ),
            ]
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Avg kWh",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Forecast Data")
        st.dataframe(forecast_df, use_container_width=True)
    else:
        st.warning("Forecast model returned no results.")

# Historical actuals
st.subheader("Recent Actual Consumption")
actuals_df = session.sql(f"""
    SELECT
        "date"     AS ts,
        SUM("kwh") AS actual_kwh
    FROM {cld_db}."streetlights"."energy_consumption"
    WHERE "date" >= DATEADD('day', -90, CURRENT_DATE())
    GROUP BY "date"
    ORDER BY ts
""").to_pandas()

if not actuals_df.empty:
    fig_actuals = px.line(
        actuals_df,
        x="TS",
        y="ACTUAL_KWH",
        title="Last 90 Days — Total Energy Consumption",
        labels={"TS": "Date", "ACTUAL_KWH": "kWh"},
    )
    st.plotly_chart(fig_actuals, use_container_width=True)
