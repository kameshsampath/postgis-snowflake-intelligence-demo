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

pg = st.navigation(
    [
        st.Page("views/overview.py", title="Home", icon="💡", default=True),
        st.Page("views/1_infrastructure_overview.py", title="Neighborhood Overview", icon="🏘️"),
        st.Page("views/2_faulty_lights.py", title="Faulty Lights", icon="🔴"),
        st.Page("views/3_analytics.py", title="Analytics", icon="📊"),
        st.Page("views/4_forecasting.py", title="Energy Forecast", icon="🔮"),
    ]
)
pg.run()
