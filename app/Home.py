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

st.set_page_config(page_title="Streetlights Intelligence", page_icon="💡", layout="wide")
st.title("Streetlights Intelligence Dashboard")
st.markdown("""
Welcome to the Streetlights Infrastructure Intelligence demo.

This application demonstrates:
- **Infrastructure Overview** — Spatial visualization of streetlight assets
- **Maintenance Search** — Natural language search via Cortex Search
- **Analytics** — Energy and operational insights via Semantic View
- **Forecasting** — ML-powered energy consumption predictions
- **Ask Agent** — Natural language Q&A via Intelligence Agent

Navigate using the sidebar pages.
""")
