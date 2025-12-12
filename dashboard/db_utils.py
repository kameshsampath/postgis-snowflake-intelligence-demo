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
Database utility functions for Streamlit Dashboard
Handles PostgreSQL/PostGIS and Snowflake connections and queries
"""

import psycopg2
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from config import POSTGIS_CONFIG, SNOWFLAKE_CONFIG, SNOWFLAKE_ENABLED

# Import Snowflake connector if available
try:
    import snowflake.connector as sf_connector
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    sf_connector = None
    SNOWFLAKE_AVAILABLE = False


@st.cache_resource
def get_sqlalchemy_engine():
    """
    Get SQLAlchemy engine for pandas queries (cached)
    Returns SQLAlchemy engine object
    """
    try:
        # Build SQLAlchemy connection string from config
        connection_string = (
            f"postgresql://{POSTGIS_CONFIG['user']}:{POSTGIS_CONFIG['password']}"
            f"@{POSTGIS_CONFIG['host']}:{POSTGIS_CONFIG['port']}/{POSTGIS_CONFIG['database']}"
        )
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        st.error(f"Database engine creation failed: {e}")
        return None


@st.cache_resource
def get_connection():
    """
    Get PostgreSQL connection for write operations (cached)
    Returns psycopg2 connection object
    """
    try:
        conn = psycopg2.connect(**POSTGIS_CONFIG)
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None


def execute_query(query, params=None):
    """
    Execute SQL query and return DataFrame using SQLAlchemy engine
    """
    engine = get_sqlalchemy_engine()
    if engine is None:
        return pd.DataFrame()
    
    try:
        df = pd.read_sql(query, engine, params=params)
        return df
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)  # Cache for 60 seconds
def get_all_lights():
    """Get all street lights with enrichment"""
    query = """
    SELECT 
        light_id, longitude, latitude, status,
        neighborhood_name, wattage,
        season, failure_risk_score, predicted_failure_date,
        maintenance_urgency, age_months, days_since_maintenance
    FROM streetlights.street_lights_enriched
    ORDER BY light_id
    """
    return execute_query(query)


@st.cache_data(ttl=60)
def get_neighborhoods():
    """Get all neighborhoods with boundaries"""
    query = """
    SELECT 
        neighborhood_id, name, population,
        ST_AsGeoJSON(boundary) as boundary_geojson
    FROM streetlights.neighborhoods
    ORDER BY name
    """
    return execute_query(query)


@st.cache_data(ttl=60)
def get_suppliers():
    """Get all suppliers"""
    query = """
    SELECT 
        supplier_id, name, 
        ST_X(location) as longitude,
        ST_Y(location) as latitude,
        service_radius_km, avg_response_hours,
        specialization, contact_phone
    FROM streetlights.suppliers
    ORDER BY name
    """
    return execute_query(query)


@st.cache_data(ttl=30)
def get_faulty_lights_with_supplier():
    """Get faulty lights with nearest supplier"""
    query = """
    SELECT 
        l.light_id,
        ST_X(l.location) as longitude,
        ST_Y(l.location) as latitude,
        l.status,
        n.name as neighborhood,
        s.name as nearest_supplier,
        s.specialization,
        ROUND(
            ST_Distance(s.location::geography, l.location::geography)::numeric / 1000, 
            2
        ) as distance_km,
        s.avg_response_hours,
        s.contact_phone
    FROM streetlights.street_lights l
    LEFT JOIN streetlights.neighborhoods n ON l.neighborhood_id = n.neighborhood_id
    CROSS JOIN LATERAL (
        SELECT supplier_id, name, specialization, location, avg_response_hours, contact_phone
        FROM streetlights.suppliers
        ORDER BY location <-> l.location
        LIMIT 1
    ) s
    WHERE l.status = 'faulty'
    ORDER BY distance_km
    """
    return execute_query(query)


@st.cache_data(ttl=60)
def get_predicted_failures(days_ahead=30):
    """Get lights predicted to fail soon"""
    query = """
    SELECT 
        light_id, longitude, latitude, status,
        neighborhood_name, 
        predicted_failure_date,
        failure_risk_score,
        maintenance_urgency,
        age_months, days_since_maintenance,
        season
    FROM streetlights.street_lights_enriched
    WHERE predicted_failure_date IS NOT NULL
      AND predicted_failure_date <= CURRENT_DATE + INTERVAL '%s days'
      AND status != 'faulty'
    ORDER BY predicted_failure_date
    """ % days_ahead
    return execute_query(query)


@st.cache_data(ttl=120)
def get_neighborhood_stats():
    """Get aggregated stats per neighborhood"""
    query = """
    SELECT 
        n.name as neighborhood,
        COUNT(l.light_id) as total_lights,
        COUNT(CASE WHEN l.status = 'operational' THEN 1 END) as operational,
        COUNT(CASE WHEN l.status = 'maintenance_required' THEN 1 END) as maintenance_required,
        COUNT(CASE WHEN l.status = 'faulty' THEN 1 END) as faulty,
        ROUND(
            COUNT(CASE WHEN l.status = 'faulty' THEN 1 END) * 100.0 / 
            NULLIF(COUNT(l.light_id), 0), 
            2
        ) as faulty_percentage
    FROM streetlights.neighborhoods n
    LEFT JOIN streetlights.street_lights l ON ST_Within(l.location, n.boundary)
    GROUP BY n.name
    ORDER BY faulty DESC, total_lights DESC
    """
    return execute_query(query)


@st.cache_data(ttl=120)
def get_seasonal_patterns():
    """Get maintenance patterns by season"""
    query = """
    SELECT 
        season,
        COUNT(*) as request_count,
        AVG(resolution_hours) as avg_resolution_hours
    FROM streetlights.maintenance_requests_enriched
    WHERE resolved_at IS NOT NULL
    GROUP BY season
    ORDER BY CASE season
        WHEN 'monsoon' THEN 1
        WHEN 'summer' THEN 2
        WHEN 'winter' THEN 3
    END
    """
    return execute_query(query)


@st.cache_data(ttl=60)
def get_supplier_coverage():
    """Analyze supplier coverage"""
    query = """
    WITH light_supplier_distance AS (
        SELECT 
            l.light_id,
            MIN(ST_Distance(s.location::geography, l.location::geography) / 1000) as nearest_supplier_km
        FROM streetlights.street_lights l
        CROSS JOIN streetlights.suppliers s
        GROUP BY l.light_id
    )
    SELECT 
        COUNT(*) as total_lights,
        COUNT(CASE WHEN nearest_supplier_km <= 5 THEN 1 END) as within_5km,
        COUNT(CASE WHEN nearest_supplier_km <= 10 THEN 1 END) as within_10km,
        COUNT(CASE WHEN nearest_supplier_km > 10 THEN 1 END) as beyond_10km,
        ROUND(AVG(nearest_supplier_km)::numeric, 2) as avg_distance_km
    FROM light_supplier_distance
    """
    return execute_query(query)


@st.cache_data(ttl=60)
def get_neighborhood_supplier_distance():
    """Get distance from each neighborhood center to nearest supplier"""
    query = """
    WITH neighborhood_centers AS (
        SELECT 
            neighborhood_id,
            name,
            ST_Centroid(boundary) as center
        FROM streetlights.neighborhoods
    ),
    neighborhood_supplier_dist AS (
        SELECT 
            nc.neighborhood_id,
            nc.name,
            s.name as nearest_supplier,
            s.specialization,
            ROUND(
                MIN(ST_Distance(nc.center::geography, s.location::geography))::numeric / 1000,
                2
            ) as distance_km
        FROM neighborhood_centers nc
        CROSS JOIN streetlights.suppliers s
        GROUP BY nc.neighborhood_id, nc.name, s.name, s.specialization
    )
    SELECT 
        nsd.name as neighborhood,
        nsd.nearest_supplier,
        nsd.specialization,
        nsd.distance_km,
        COUNT(l.light_id) as lights_in_neighborhood
    FROM neighborhood_supplier_dist nsd
    JOIN streetlights.neighborhoods n ON nsd.neighborhood_id = n.neighborhood_id
    LEFT JOIN streetlights.street_lights l ON ST_Within(l.location, n.boundary)
    WHERE nsd.distance_km = (
        SELECT MIN(distance_km)
        FROM neighborhood_supplier_dist
        WHERE neighborhood_id = nsd.neighborhood_id
    )
    GROUP BY nsd.neighborhood_id, nsd.name, nsd.nearest_supplier, nsd.specialization, nsd.distance_km
    ORDER BY nsd.distance_km DESC
    """
    return execute_query(query)


def simulate_light_failure(light_id=None):
    """
    Simulate a light failure for demo purposes
    If no light_id provided, pick a random operational light
    """
    conn = get_connection()
    if conn is None:
        return False, "No database connection"
    
    try:
        cursor = conn.cursor()
        
        if light_id is None:
            # Pick random operational light
            cursor.execute("""
                SELECT light_id FROM streetlights.street_lights 
                WHERE status = 'operational' 
                ORDER BY RANDOM() 
                LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                light_id = result[0]
            else:
                return False, "No operational lights found"
        
        # Update light to faulty
        cursor.execute("""
            UPDATE streetlights.street_lights
            SET status = 'faulty', last_maintenance = NOW()
            WHERE light_id = %s
        """, (light_id,))
        
        conn.commit()
        cursor.close()
        
        # Clear cache to show updated data
        st.cache_data.clear()
        
        return True, f"Light {light_id} set to faulty"
        
    except Exception as e:
        return False, f"Failed to simulate failure: {e}"


def trigger_scheduled_maintenance(count=5):
    """
    Set random operational lights to maintenance_required status
    """
    conn = get_connection()
    if conn is None:
        return False, "No database connection"
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE streetlights.street_lights
            SET status = 'maintenance_required'
            WHERE light_id IN (
                SELECT light_id FROM streetlights.street_lights 
                WHERE status = 'operational' 
                ORDER BY RANDOM() 
                LIMIT %s
            )
        """, (count,))
        
        affected = cursor.rowcount
        conn.commit()
        cursor.close()
        
        # Clear cache
        st.cache_data.clear()
        
        return True, f"{affected} lights set to maintenance_required"
        
    except Exception as e:
        return False, f"Failed to trigger maintenance: {e}"


# =============================================================================
# SNOWFLAKE CONNECTION AND QUERIES
# =============================================================================

@st.cache_resource
def get_snowflake_connection():
    """
    Get Snowflake connection for ML prediction queries (cached)
    Returns snowflake.connector connection object
    """
    if not SNOWFLAKE_AVAILABLE:
        st.warning("Snowflake connector not installed. Install with: pip install snowflake-connector-python")
        return None
    
    if not SNOWFLAKE_ENABLED:
        return None
    
    try:
        conn = sf_connector.connect(
            account=SNOWFLAKE_CONFIG["account"],
            user=SNOWFLAKE_CONFIG["user"],
            password=SNOWFLAKE_CONFIG["password"],
            warehouse=SNOWFLAKE_CONFIG["warehouse"],
            database=SNOWFLAKE_CONFIG["database"],
            schema=SNOWFLAKE_CONFIG["schema"]
        )
        return conn
    except Exception as e:
        st.error(f"Snowflake connection failed: {e}")
        return None


def execute_snowflake_query(query, params=None):
    """
    Execute SQL query on Snowflake and return DataFrame
    """
    conn = get_snowflake_connection()
    if conn is None:
        return pd.DataFrame()
    
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Fetch all results
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        cursor.close()
        
        return pd.DataFrame(data, columns=columns)
    except Exception as e:
        st.error(f"Snowflake query failed: {e}")
        return pd.DataFrame()


def is_snowflake_available():
    """Check if Snowflake connection is available and working"""
    return SNOWFLAKE_AVAILABLE and SNOWFLAKE_ENABLED and get_snowflake_connection() is not None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_snowflake_forecast_30d():
    """
    Get 30-day bulb failure forecast from Snowflake ML model
    """
    query = """
    SELECT 
        FORECAST_DATE,
        PREDICTED_FAILURES,
        LOWER_BOUND,
        UPPER_BOUND,
        SEASON,
        DAY_OF_WEEK,
        PRIORITY,
        STAFFING_RECOMMENDATION,
        BULBS_TO_STOCK
    FROM BULB_REPLACEMENT_SCHEDULE
    ORDER BY FORECAST_DATE
    """
    return execute_snowflake_query(query)


@st.cache_data(ttl=300)
def get_snowflake_forecast_90d():
    """
    Get 90-day bulb failure forecast from Snowflake ML model
    """
    query = """
    SELECT 
        FORECAST_DATE,
        PREDICTED_FAILURES,
        LOWER_BOUND,
        UPPER_BOUND,
        WEEK_START,
        MONTH_START,
        SEASON
    FROM BULB_FAILURE_FORECAST_90D
    ORDER BY FORECAST_DATE
    """
    return execute_snowflake_query(query)


@st.cache_data(ttl=300)
def get_snowflake_weekly_forecast():
    """
    Get weekly forecast summary from Snowflake
    """
    query = """
    SELECT 
        WEEK_START,
        TOTAL_PREDICTED_FAILURES,
        TOTAL_LOWER_BOUND,
        TOTAL_UPPER_BOUND,
        AVG_DAILY_FAILURES,
        PEAK_DAY_FAILURES,
        PRIMARY_SEASON
    FROM WEEKLY_BULB_FORECAST
    ORDER BY WEEK_START
    """
    return execute_snowflake_query(query)


@st.cache_data(ttl=300)
def get_snowflake_forecast_metrics():
    """
    Get key forecast metrics for dashboard cards from Snowflake
    """
    query = """
    SELECT 
        'FORECAST_NEXT_7_DAYS' AS metric,
        SUM(PREDICTED_FAILURES)::VARCHAR AS value,
        'Expected bulb failures in next 7 days' AS description
    FROM BULB_REPLACEMENT_SCHEDULE
    WHERE FORECAST_DATE <= DATEADD('day', 7, CURRENT_DATE())
    
    UNION ALL
    
    SELECT 'FORECAST_NEXT_30_DAYS', SUM(PREDICTED_FAILURES)::VARCHAR, 'Expected bulb failures in next 30 days'
    FROM BULB_REPLACEMENT_SCHEDULE
    
    UNION ALL
    
    SELECT 'HIGH_PRIORITY_DAYS', COUNT(*)::VARCHAR, 'Days requiring extra staffing (next 30 days)'
    FROM BULB_REPLACEMENT_SCHEDULE WHERE PRIORITY = 'HIGH'
    
    UNION ALL
    
    SELECT 'BULBS_TO_ORDER_30D', SUM(BULBS_TO_STOCK)::VARCHAR, 'Recommended bulb inventory for next 30 days'
    FROM BULB_REPLACEMENT_SCHEDULE
    """
    return execute_snowflake_query(query)


@st.cache_data(ttl=300)
def get_snowflake_seasonal_forecast():
    """
    Get seasonal risk comparison from Snowflake
    """
    query = """
    SELECT 
        SEASON,
        COUNT(*) AS FORECAST_DAYS,
        SUM(PREDICTED_FAILURES) AS TOTAL_FAILURES,
        ROUND(AVG(PREDICTED_FAILURES), 2) AS AVG_DAILY_FAILURES,
        MAX(PREDICTED_FAILURES) AS PEAK_DAY_FAILURES,
        CASE 
            WHEN AVG(PREDICTED_FAILURES) > 3 THEN 'HIGH RISK'
            WHEN AVG(PREDICTED_FAILURES) > 2 THEN 'MEDIUM RISK'
            ELSE 'LOW RISK'
        END AS SEASONAL_RISK
    FROM BULB_FAILURE_FORECAST_90D
    GROUP BY SEASON
    ORDER BY AVG_DAILY_FAILURES DESC
    """
    return execute_snowflake_query(query)


@st.cache_data(ttl=300)
def get_snowflake_monthly_budget():
    """
    Get monthly budget forecast from Snowflake
    """
    query = """
    WITH forecast_costs AS (
        SELECT 
            DATE_TRUNC('month', FORECAST_DATE)::DATE AS MONTH,
            SUM(PREDICTED_FAILURES) AS PREDICTED_FAILURES,
            CEIL(SUM(UPPER_BOUND) * 1.2) AS BULBS_NEEDED
        FROM BULB_FAILURE_FORECAST_90D
        GROUP BY DATE_TRUNC('month', FORECAST_DATE)
    )
    SELECT 
        MONTH,
        PREDICTED_FAILURES AS JOBS,
        BULBS_NEEDED,
        BULBS_NEEDED * 1000 AS MATERIAL_COST_INR,
        PREDICTED_FAILURES * 500 AS LABOR_COST_INR,
        PREDICTED_FAILURES * 150 AS TRANSPORT_COST_INR,
        PREDICTED_FAILURES * 100 AS OVERHEAD_COST_INR,
        (BULBS_NEEDED * 1000) + 
        (PREDICTED_FAILURES * 500) + 
        (PREDICTED_FAILURES * 150) + 
        (PREDICTED_FAILURES * 100) AS TOTAL_MONTHLY_BUDGET_INR
    FROM forecast_costs
    ORDER BY MONTH
    """
    return execute_snowflake_query(query)


# =============================================================================
# ALL ISSUES FORECAST QUERIES (Total Maintenance Workload)
# =============================================================================

@st.cache_data(ttl=300)
def get_snowflake_all_issues_forecast_30d():
    """
    Get 30-day all issues (total maintenance) forecast from Snowflake ML model
    """
    query = """
    SELECT 
        FORECAST_DATE,
        PREDICTED_REQUESTS,
        LOWER_BOUND,
        UPPER_BOUND,
        SEASON,
        DAY_OF_WEEK,
        WORKLOAD_LEVEL,
        STAFFING_RECOMMENDATION,
        BULBS_TO_STOCK,
        WIRING_KITS_TO_STOCK,
        POLES_TO_STOCK,
        UNCERTAINTY_RANGE
    FROM MAINTENANCE_SCHEDULE
    ORDER BY FORECAST_DATE
    """
    return execute_snowflake_query(query)


@st.cache_data(ttl=300)
def get_snowflake_all_issues_forecast_90d():
    """
    Get 90-day all issues forecast from Snowflake ML model
    """
    query = """
    SELECT 
        FORECAST_DATE,
        PREDICTED_REQUESTS,
        LOWER_BOUND,
        UPPER_BOUND,
        WEEK_START,
        MONTH_START,
        SEASON
    FROM ALL_ISSUES_FORECAST_90D
    ORDER BY FORECAST_DATE
    """
    return execute_snowflake_query(query)


@st.cache_data(ttl=300)
def get_snowflake_weekly_all_issues_forecast():
    """
    Get weekly all issues forecast summary from Snowflake
    """
    query = """
    SELECT 
        WEEK_START,
        TOTAL_PREDICTED_REQUESTS,
        TOTAL_LOWER_BOUND,
        TOTAL_UPPER_BOUND,
        AVG_DAILY_REQUESTS,
        PEAK_DAY_REQUESTS,
        PRIMARY_SEASON
    FROM WEEKLY_MAINTENANCE_FORECAST
    ORDER BY WEEK_START
    """
    return execute_snowflake_query(query)


@st.cache_data(ttl=300)
def get_snowflake_forecast_comparison():
    """
    Get comparison between bulb failures and all issues forecast
    """
    query = """
    SELECT 
        FORECAST_DATE,
        BULB_FAILURES,
        ALL_ISSUES,
        OTHER_ISSUES,
        BULB_PERCENTAGE,
        SEASON,
        OVERALL_WORKLOAD
    FROM FORECAST_COMPARISON
    ORDER BY FORECAST_DATE
    """
    return execute_snowflake_query(query)


@st.cache_data(ttl=300)
def get_snowflake_all_issues_metrics():
    """
    Get key all issues forecast metrics for dashboard cards
    """
    query = """
    SELECT 
        'TOTAL_REQUESTS_NEXT_7_DAYS' AS metric,
        SUM(PREDICTED_REQUESTS)::VARCHAR AS value,
        'Expected total maintenance requests in next 7 days' AS description
    FROM MAINTENANCE_SCHEDULE
    WHERE FORECAST_DATE <= DATEADD('day', 7, CURRENT_DATE())
    
    UNION ALL
    
    SELECT 'TOTAL_REQUESTS_NEXT_30_DAYS', SUM(PREDICTED_REQUESTS)::VARCHAR, 'Expected total maintenance requests in next 30 days'
    FROM MAINTENANCE_SCHEDULE
    
    UNION ALL
    
    SELECT 'HIGH_WORKLOAD_DAYS', COUNT(*)::VARCHAR, 'Days with high workload (next 30 days)'
    FROM MAINTENANCE_SCHEDULE WHERE WORKLOAD_LEVEL = 'HIGH'
    
    UNION ALL
    
    SELECT 'TOTAL_PARTS_NEEDED', 
           (SUM(BULBS_TO_STOCK) + SUM(WIRING_KITS_TO_STOCK) + SUM(POLES_TO_STOCK))::VARCHAR, 
           'Total parts to stock for next 30 days'
    FROM MAINTENANCE_SCHEDULE
    """
    return execute_snowflake_query(query)


@st.cache_data(ttl=300)
def get_snowflake_issue_type_distribution():
    """
    Get historical issue type distribution from Snowflake
    """
    query = """
    SELECT 
        ISSUE_TYPE,
        TOTAL_COUNT,
        PERCENTAGE,
        FIRST_REPORTED,
        LAST_REPORTED,
        UNIQUE_LIGHTS
    FROM ML_ISSUE_TYPE_DISTRIBUTION
    ORDER BY TOTAL_COUNT DESC
    """
    return execute_snowflake_query(query)


@st.cache_data(ttl=300)
def get_snowflake_all_issues_monthly_budget():
    """
    Get monthly budget forecast for all issues from Snowflake
    """
    query = """
    WITH forecast_costs AS (
        SELECT 
            DATE_TRUNC('month', FORECAST_DATE)::DATE AS MONTH,
            SUM(PREDICTED_REQUESTS) AS PREDICTED_REQUESTS,
            CEIL(SUM(BULBS_TO_STOCK)) AS BULBS_NEEDED,
            CEIL(SUM(WIRING_KITS_TO_STOCK)) AS WIRING_KITS_NEEDED,
            CEIL(SUM(POLES_TO_STOCK)) AS POLES_NEEDED
        FROM MAINTENANCE_SCHEDULE
        GROUP BY DATE_TRUNC('month', FORECAST_DATE)
    )
    SELECT 
        MONTH,
        PREDICTED_REQUESTS AS TOTAL_JOBS,
        BULBS_NEEDED,
        WIRING_KITS_NEEDED,
        POLES_NEEDED,
        -- Cost breakdown (INR)
        BULBS_NEEDED * 1000 AS BULB_COST_INR,
        WIRING_KITS_NEEDED * 2000 AS WIRING_COST_INR,
        POLES_NEEDED * 15000 AS POLE_COST_INR,
        PREDICTED_REQUESTS * 500 AS LABOR_COST_INR,
        PREDICTED_REQUESTS * 150 AS TRANSPORT_COST_INR,
        -- Total
        (BULBS_NEEDED * 1000) + 
        (WIRING_KITS_NEEDED * 2000) + 
        (POLES_NEEDED * 15000) + 
        (PREDICTED_REQUESTS * 500) + 
        (PREDICTED_REQUESTS * 150) AS TOTAL_MONTHLY_BUDGET_INR
    FROM forecast_costs
    ORDER BY MONTH
    """
    return execute_snowflake_query(query)


