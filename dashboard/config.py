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

"""
Configuration for Streamlit Dashboard
PostGIS and Snowflake connection parameters and app settings
"""

import streamlit as st

# PostgreSQL / PostGIS Connection
# Try to load from Streamlit secrets first, fallback to defaults
try:
    POSTGIS_CONFIG = {
        "host": st.secrets["postgres"]["host"],
        "port": st.secrets["postgres"]["port"],
        "database": st.secrets["postgres"]["database"],
        "user": st.secrets["postgres"]["user"],
        "password": st.secrets["postgres"]["password"]
    }
except (KeyError, FileNotFoundError):
    # Fallback to environment variables or defaults if secrets not available
    import os
    POSTGIS_CONFIG = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "database": os.getenv("POSTGRES_DATABASE", "streetlights"),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", "password")
    }

# Snowflake Connection for ML Predictions
# Try to load from Streamlit secrets first, fallback to defaults
try:
    SNOWFLAKE_CONFIG = {
        "account": st.secrets["snowflake"]["account"],
        "user": st.secrets["snowflake"]["user"],
        "password": st.secrets["snowflake"]["password"],
        "warehouse": st.secrets["snowflake"]["warehouse"],
        "database": st.secrets["snowflake"]["database"],
        "schema": st.secrets["snowflake"]["schema"]
    }
    SNOWFLAKE_ENABLED = True
except (KeyError, FileNotFoundError):
    # Fallback to environment variables or defaults if secrets not available
    import os
    SNOWFLAKE_CONFIG = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
        "user": os.getenv("SNOWFLAKE_USER", ""),
        "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "STREETLIGHTS_DEMO"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "ANALYTICS")
    }
    # Only enable Snowflake if credentials are provided
    SNOWFLAKE_ENABLED = bool(SNOWFLAKE_CONFIG["account"] and SNOWFLAKE_CONFIG["user"])

# Streamlit Page Configuration
PAGE_CONFIG = {
    "page_title": "Street Lights Maintenance Dashboard",
    "page_icon": "💡",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Map Configuration
MAP_CONFIG = {
    "center": [12.9716, 77.5946],  # Bengaluru center
    "zoom": 11,
    "tiles": "OpenStreetMap"
}

# Color Scheme for Light Status
STATUS_COLORS = {
    "operational": "#2ecc71",      # Green
    "maintenance_required": "#f39c12",  # Yellow/Orange
    "faulty": "#e74c3c",           # Red
    "predicted_failure": "#ff6b6b"  # Light red for predictions
}

# Urgency Colors
URGENCY_COLORS = {
    "CRITICAL": "#c0392b",  # Dark red
    "HIGH": "#e67e22",      # Orange
    "MEDIUM": "#f39c12",    # Yellow
    "LOW": "#95a5a6"        # Gray
}

# Refresh Interval (seconds)
AUTO_REFRESH_INTERVAL = 30

# Query Limits
MAX_RESULTS = 1000

