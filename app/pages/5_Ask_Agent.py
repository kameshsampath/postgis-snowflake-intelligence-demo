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

st.set_page_config(page_title="Ask Agent", page_icon="🤖", layout="wide")
st.title("Ask the Streetlights Agent")
st.markdown("Ask questions about streetlight infrastructure in natural language.")

session = get_active_session()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about streetlights..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            safe_prompt = prompt.replace("'", "''")
            result_df = session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.AGENT(
                    '"streetlights"."streetlights_agent"',
                    '{safe_prompt}'
                ) AS response
            """).to_pandas()

            if not result_df.empty and result_df["RESPONSE"].iloc[0]:
                response_raw = result_df["RESPONSE"].iloc[0]
                try:
                    response_json = json.loads(response_raw)
                    response_text = response_json.get("message", response_raw)
                except (json.JSONDecodeError, TypeError):
                    response_text = str(response_raw)

                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            else:
                error_msg = "I couldn't get a response. Please try again."
                st.warning(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
