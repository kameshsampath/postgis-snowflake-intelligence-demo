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

st.set_page_config(page_title="Forecasting", page_icon="🔮", layout="wide")
st.title("Energy Consumption Forecasting")
st.markdown("ML-powered predictions using Snowflake FORECAST models.")

session = get_active_session()
db = session.get_current_database()

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
        forecast_df = session.sql(f"""
            CALL {db}.PUBLIC.energy_forecast!FORECAST(
                FORECASTING_PERIODS => {forecast_days},
                CONFIG_OBJECT => {{'prediction_interval': 0.95}}
            )
        """).to_pandas()

    if not forecast_df.empty:
        st.subheader("Predicted Energy Consumption")
        st.line_chart(
            forecast_df.set_index("TS")[["FORECAST", "LOWER", "UPPER"]],
        )

        st.subheader("Forecast Data")
        st.dataframe(forecast_df, use_container_width=True)
    else:
        st.warning("Forecast model returned no results.")

# Historical vs recent actuals
st.subheader("Recent Actual Consumption")
actuals_df = session.sql("""
    SELECT
        "reading_date" AS ts,
        SUM("kwh_consumed") AS actual_kwh
    FROM "streetlights"."energy_consumption"
    WHERE "reading_date" >= DATEADD('day', -90, CURRENT_DATE())
    GROUP BY "reading_date"
    ORDER BY ts
""").to_pandas()

if not actuals_df.empty:
    st.line_chart(actuals_df.set_index("TS")["ACTUAL_KWH"])
