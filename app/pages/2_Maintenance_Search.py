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

import json

import streamlit as st

from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Maintenance Search", page_icon="🔍", layout="wide")
st.title("Maintenance Search")
st.markdown("Search maintenance records using natural language powered by Cortex Search.")

session = get_active_session()

query = st.text_input(
    "Search maintenance records:",
    placeholder="e.g., LED replacements in downtown",
)

if query:
    results_df = session.sql(f"""
        SELECT PARSE_JSON(
            SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                'streetlights.maintenance_search_service',
                '{query.replace("'", "''")}'
            )
        ) AS results
    """).to_pandas()

    if not results_df.empty and results_df["RESULTS"].iloc[0]:
        results = json.loads(results_df["RESULTS"].iloc[0])
        if "results" in results and results["results"]:
            st.success(f"Found {len(results['results'])} matching records")
            for i, result in enumerate(results["results"], 1):
                with st.expander(f"Result {i} — Score: {result.get('score', 'N/A'):.3f}"):
                    for key, value in result.items():
                        if key != "score":
                            st.markdown(f"**{key}:** {value}")
        else:
            st.info("No matching records found.")
    else:
        st.info("No results returned.")
