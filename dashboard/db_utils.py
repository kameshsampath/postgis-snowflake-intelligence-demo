"""
Database utility functions for Streamlit Dashboard
Handles PostgreSQL/PostGIS connections and queries
"""

import psycopg2
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from config import POSTGIS_CONFIG


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


