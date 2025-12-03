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
Street Lights Maintenance Dashboard
Multi-page Streamlit application for PostGIS demo
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium
from datetime import date, timedelta
import folium

# Import local modules
from config import PAGE_CONFIG, STATUS_COLORS, URGENCY_COLORS
from db_utils import (
    get_all_lights, get_neighborhoods, get_suppliers,
    get_faulty_lights_with_supplier, get_predicted_failures,
    get_neighborhood_stats, get_seasonal_patterns,
    get_supplier_coverage, get_neighborhood_supplier_distance,
    simulate_light_failure, trigger_scheduled_maintenance,
    # Snowflake ML functions - Bulb Failures
    is_snowflake_available, get_snowflake_forecast_30d,
    get_snowflake_forecast_90d, get_snowflake_weekly_forecast,
    get_snowflake_forecast_metrics, get_snowflake_seasonal_forecast,
    get_snowflake_monthly_budget,
    # Snowflake ML functions - All Issues
    get_snowflake_all_issues_forecast_30d, get_snowflake_all_issues_forecast_90d,
    get_snowflake_weekly_all_issues_forecast, get_snowflake_forecast_comparison,
    get_snowflake_all_issues_metrics, get_snowflake_issue_type_distribution,
    get_snowflake_all_issues_monthly_budget
)
from map_utils import (
    create_base_map, add_neighborhoods_layer, add_lights_layer,
    add_suppliers_layer, add_predicted_failures_layer,
    create_legend_html, add_fullscreen_control,
    add_neighborhood_supplier_lines
)

# Configure page
st.set_page_config(**PAGE_CONFIG)

# Custom CSS
st.markdown("""
<style>
    .big-metric {
        font-size: 24px;
        font-weight: bold;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("💡 Street Lights Dashboard")
st.sidebar.markdown("---")

# Page selection
page = st.sidebar.radio(
    "Navigation",
    ["🏘️ Neighborhood Overview", 
     "🔴 Faulty Lights Analysis",
     "🔮 Predictive Maintenance",
     "🏭 Supplier Coverage",
     "🎮 Live Demo Controls"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "This dashboard visualizes street lights maintenance data "
    "from PostGIS database with spatial enrichment."
)

# Main content based on page selection
if page == "🏘️ Neighborhood Overview":
    st.title("🏘️ Neighborhood Overview")
    st.markdown("Interactive map showing all neighborhoods, street lights, and suppliers")
    
    # Load data
    with st.spinner("Loading data..."):
        lights_df = get_all_lights()
        neighborhoods_df = get_neighborhoods()
        suppliers_df = get_suppliers()
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    total_lights = len(lights_df)
    operational = len(lights_df[lights_df['status'] == 'operational'])
    faulty = len(lights_df[lights_df['status'] == 'faulty'])
    maintenance = len(lights_df[lights_df['status'] == 'maintenance_required'])
    
    col1.metric("Total Lights", f"{total_lights:,}")
    col2.metric("Operational", f"{operational:,}", f"{operational*100/total_lights:.1f}%")
    col3.metric("Faulty", f"{faulty:,}", f"-{faulty*100/total_lights:.1f}%", delta_color="inverse")
    col4.metric("Maintenance Required", f"{maintenance:,}")
    
    st.markdown("---")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        selected_neighborhoods = st.multiselect(
            "Filter by Neighborhood",
            options=neighborhoods_df['name'].tolist() if not neighborhoods_df.empty else [],
            default=[]
        )
    
    with col2:
        show_layers = st.multiselect(
            "Map Layers",
            options=["Neighborhoods", "Lights", "Suppliers"],
            default=["Neighborhoods", "Lights", "Suppliers"]
        )
    
    # Filter lights if neighborhoods selected
    if selected_neighborhoods:
        lights_df = lights_df[lights_df['neighborhood_name'].isin(selected_neighborhoods)]
    
    # Create map
    m = create_base_map()
    
    if "Neighborhoods" in show_layers and not neighborhoods_df.empty:
        m = add_neighborhoods_layer(m, neighborhoods_df)
    
    if "Lights" in show_layers and not lights_df.empty:
        m = add_lights_layer(m, lights_df)
    
    if "Suppliers" in show_layers and not suppliers_df.empty:
        m = add_suppliers_layer(m, suppliers_df)
    
    m = add_fullscreen_control(m)
    
    # Add legend
    legend_items = []
    if "Lights" in show_layers:
        legend_items.extend([
            ("Operational", STATUS_COLORS['operational'], 'circle'),
            ("Maintenance Required", STATUS_COLORS['maintenance_required'], 'circle'),
            ("Faulty", STATUS_COLORS['faulty'], 'circle')
        ])
    if "Suppliers" in show_layers:
        legend_items.append(("Supplier", "#3498db", 'marker'))
    
    if legend_items:
        m.get_root().html.add_child(folium.Element(create_legend_html(legend_items)))
    
    # Display map
    st_folium(m, width=1400, height=600)
    
    # Stats table
    st.markdown("### Neighborhood Statistics")
    stats_df = get_neighborhood_stats()
    if not stats_df.empty:
        st.dataframe(
            stats_df.style.background_gradient(subset=['faulty_percentage'], cmap='Reds')
                          .format({'faulty_percentage': '{:.2f}%'}),
            width='stretch'
        )

elif page == "🔴 Faulty Lights Analysis":
    st.title("🔴 Faulty Lights Analysis")
    st.markdown("Analysis of currently faulty lights with nearest suppliers")
    
    # Load data
    with st.spinner("Loading faulty lights data..."):
        faulty_df = get_faulty_lights_with_supplier()
        all_lights = get_all_lights()
        neighborhoods_df = get_neighborhoods()
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    total_faulty = len(faulty_df)
    total_lights = len(all_lights)
    faulty_pct = (total_faulty / total_lights * 100) if total_lights > 0 else 0
    
    col1.metric("Faulty Lights", f"{total_faulty:,}")
    col2.metric("Percentage", f"{faulty_pct:.2f}%", delta_color="inverse")
    col3.metric("Avg Distance to Supplier", 
                f"{faulty_df['distance_km'].mean():.2f} km" if not faulty_df.empty else "N/A")
    
    st.markdown("---")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        neighborhoods = faulty_df['neighborhood'].unique().tolist() if not faulty_df.empty else []
        selected_nh = st.multiselect("Filter by Neighborhood", neighborhoods, default=[])
    
    with col2:
        max_distance = st.slider("Max Distance to Supplier (km)", 0.0, 20.0, 20.0, 0.5)
    
    # Apply filters
    filtered_df = faulty_df.copy()
    if selected_nh:
        filtered_df = filtered_df[filtered_df['neighborhood'].isin(selected_nh)]
    filtered_df = filtered_df[filtered_df['distance_km'] <= max_distance]
    
    # Map
    st.markdown("### Faulty Lights Map")
    m = create_base_map()
    m = add_neighborhoods_layer(m, neighborhoods_df)
    
    if not filtered_df.empty:
        # Convert to format expected by add_lights_layer
        map_df = filtered_df.rename(columns={'neighborhood': 'neighborhood_name'})
        m = add_lights_layer(m, map_df, show_status_legend=False)
    
    m = add_fullscreen_control(m)
    st_folium(m, width=1400, height=500)
    
    # Table
    st.markdown("### Faulty Lights with Nearest Supplier")
    if not filtered_df.empty:
        display_df = filtered_df[[
            'light_id', 'neighborhood', 'nearest_supplier', 
            'specialization', 'distance_km', 'avg_response_hours', 'contact_phone'
        ]].copy()
        
        st.dataframe(
            display_df.style.background_gradient(subset=['distance_km'], cmap='YlOrRd'),
            width='stretch'
        )
        
        # Bar chart: Faulty lights per neighborhood
        st.markdown("### Faulty Lights by Neighborhood")
        nh_counts = filtered_df.groupby('neighborhood').size().reset_index(name='count')
        nh_counts = nh_counts.sort_values('count', ascending=False)
        
        fig = px.bar(nh_counts, x='neighborhood', y='count',
                     title="Faulty Lights Count by Neighborhood",
                     labels={'count': 'Number of Faulty Lights', 'neighborhood': 'Neighborhood'})
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No faulty lights match the selected filters")

elif page == "🔮 Predictive Maintenance":
    st.title("🔮 Predictive Maintenance")
    
    # Check if Snowflake is available
    snowflake_connected = is_snowflake_available()
    
    if snowflake_connected:
        # Forecast Type Selector
        forecast_type = st.radio(
            "Select Forecast Type",
            options=["💡 Bulb Failures", "🔧 All Maintenance Issues"],
            horizontal=True,
            help="Choose between bulb failure predictions or total maintenance workload"
        )
        
        if forecast_type == "💡 Bulb Failures":
            st.markdown("**Bulb Failure Forecasts** powered by Snowflake ML")
            st.caption("Predictions for bulb replacement needs based on historical failure patterns")
        else:
            st.markdown("**All Maintenance Issues Forecast** powered by Snowflake ML")
            st.caption("Total maintenance workload predictions including all issue types")
        
        # Load Snowflake forecast data based on selection
        with st.spinner("Loading Snowflake ML predictions..."):
            if forecast_type == "💡 Bulb Failures":
                forecast_30d = get_snowflake_forecast_30d()
                forecast_metrics = get_snowflake_forecast_metrics()
            else:
                forecast_30d = get_snowflake_all_issues_forecast_30d()
                forecast_metrics = get_snowflake_all_issues_metrics()
            neighborhoods_df = get_neighborhoods()
        
        # Check if ML model has been trained (forecast tables are empty)
        if forecast_30d.empty and forecast_metrics.empty:
            st.warning("⚠️ **ML Model Not Trained Yet**")
            st.info(
                """
                The Snowflake ML forecast models need to be trained before predictions are available.
                
                **Please run the following SQL scripts in Snowflake (in order):**
                
                1. `snowflake/08_ml_training_view.sql` - Creates the training data views
                2. `snowflake/09_ml_model_training.sql` - Trains BOTH forecast models and generates predictions
                
                **Quick steps:**
                ```sql
                -- Connect to Snowflake and run:
                USE DATABASE STREETLIGHTS_DEMO;
                USE SCHEMA ANALYTICS;
                
                -- Then execute the scripts above
                ```
                
                After training completes (2-5 minutes for both models), refresh this page to see the predictions.
                """
            )
            st.markdown("---")
            st.markdown("### 📚 What the ML Models Do")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                **💡 Bulb Failure Model:**
                - Predicts daily bulb replacements needed
                - Optimizes bulb inventory
                - ~50% of all maintenance requests
                """)
            with col2:
                st.markdown("""
                **🔧 All Issues Model:**
                - Predicts total maintenance workload
                - Includes: bulb, wiring, pole, power, sensors
                - Full staffing and budget planning
                """)
            st.stop()  # Stop rendering the rest of the page
        
        # Key Metrics from Snowflake
        st.markdown("### 📊 Forecast Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        if not forecast_metrics.empty:
            metrics_dict = dict(zip(forecast_metrics['METRIC'], forecast_metrics['VALUE']))
            
            if forecast_type == "💡 Bulb Failures":
                col1.metric(
                    "Next 7 Days",
                    f"{metrics_dict.get('FORECAST_NEXT_7_DAYS', 'N/A')} failures",
                    help="Expected bulb failures in the next 7 days"
                )
                col2.metric(
                    "Next 30 Days",
                    f"{metrics_dict.get('FORECAST_NEXT_30_DAYS', 'N/A')} failures",
                    help="Expected bulb failures in the next 30 days"
                )
                col3.metric(
                    "High Priority Days",
                    f"{metrics_dict.get('HIGH_PRIORITY_DAYS', 'N/A')} days",
                    help="Days requiring extra staffing in next 30 days"
                )
                col4.metric(
                    "Bulbs to Order",
                    f"{metrics_dict.get('BULBS_TO_ORDER_30D', 'N/A')} units",
                    help="Recommended inventory for next 30 days"
                )
            else:
                col1.metric(
                    "Next 7 Days",
                    f"{metrics_dict.get('TOTAL_REQUESTS_NEXT_7_DAYS', 'N/A')} requests",
                    help="Expected total maintenance requests in the next 7 days"
                )
                col2.metric(
                    "Next 30 Days",
                    f"{metrics_dict.get('TOTAL_REQUESTS_NEXT_30_DAYS', 'N/A')} requests",
                    help="Expected total maintenance requests in the next 30 days"
                )
                col3.metric(
                    "High Workload Days",
                    f"{metrics_dict.get('HIGH_WORKLOAD_DAYS', 'N/A')} days",
                    help="Days with high workload in next 30 days"
                )
                col4.metric(
                    "Parts to Stock",
                    f"{metrics_dict.get('TOTAL_PARTS_NEEDED', 'N/A')} units",
                    help="Total parts (bulbs + wiring + poles) for next 30 days"
                )
        
        st.markdown("---")
        
        # Controls for filtering
        col1, col2 = st.columns(2)
        
        with col1:
            if forecast_type == "💡 Bulb Failures":
                priority_filter = st.multiselect(
                    "Filter by Priority",
                    options=["HIGH", "MEDIUM", "LOW"],
                    default=["HIGH", "MEDIUM"]
                )
            else:
                priority_filter = st.multiselect(
                    "Filter by Workload Level",
                    options=["HIGH", "MEDIUM", "LOW"],
                    default=["HIGH", "MEDIUM"]
                )
        
        with col2:
            view_mode = st.radio(
                "View Mode",
                options=["Daily Schedule", "Weekly Summary", "Monthly Budget", "Issue Breakdown"] if forecast_type == "🔧 All Maintenance Issues" else ["Daily Schedule", "Weekly Summary", "Monthly Budget"],
                horizontal=True
            )
        
        # Filter data based on forecast type
        filtered_forecast = forecast_30d.copy()
        if priority_filter and not filtered_forecast.empty:
            if forecast_type == "💡 Bulb Failures":
                filtered_forecast = filtered_forecast[filtered_forecast['PRIORITY'].isin(priority_filter)]
            else:
                filtered_forecast = filtered_forecast[filtered_forecast['WORKLOAD_LEVEL'].isin(priority_filter)]
        
        st.markdown("---")
        
        if view_mode == "Daily Schedule":
            if forecast_type == "💡 Bulb Failures":
                st.markdown("### 📅 Daily Bulb Replacement Schedule")
            else:
                st.markdown("### 📅 Daily Maintenance Schedule")
            
            if not filtered_forecast.empty:
                # Convert columns to proper format based on forecast type
                if forecast_type == "💡 Bulb Failures":
                    display_df = filtered_forecast[[
                        'FORECAST_DATE', 'PREDICTED_FAILURES', 'LOWER_BOUND', 'UPPER_BOUND',
                        'PRIORITY', 'STAFFING_RECOMMENDATION', 'BULBS_TO_STOCK', 'SEASON'
                    ]].copy()
                    priority_col = 'PRIORITY'
                else:
                    display_df = filtered_forecast[[
                        'FORECAST_DATE', 'PREDICTED_REQUESTS', 'LOWER_BOUND', 'UPPER_BOUND',
                        'WORKLOAD_LEVEL', 'STAFFING_RECOMMENDATION', 'BULBS_TO_STOCK', 
                        'WIRING_KITS_TO_STOCK', 'POLES_TO_STOCK', 'SEASON'
                    ]].copy()
                    priority_col = 'WORKLOAD_LEVEL'
                
                # Color code by priority/workload
                def highlight_priority(row):
                    priority_colors = {
                        'HIGH': '#e74c3c',
                        'MEDIUM': '#f39c12',
                        'LOW': '#27ae60'
                    }
                    color = priority_colors.get(row[priority_col], '#ffffff')
                    return [f'background-color: {color}; color: white' if col == priority_col 
                           else '' for col in row.index]
                
                st.dataframe(
                    display_df.style.apply(highlight_priority, axis=1),
                    width='stretch',
                    height=400
                )
                
                # Timeline chart
                if forecast_type == "💡 Bulb Failures":
                    st.markdown("### 📈 Bulb Failure Forecast Timeline")
                    y_col = 'PREDICTED_FAILURES'
                    y_label = 'Predicted Failures'
                    chart_title = "Snowflake ML Forecast: Daily Bulb Failures"
                else:
                    st.markdown("### 📈 Total Maintenance Forecast Timeline")
                    y_col = 'PREDICTED_REQUESTS'
                    y_label = 'Predicted Requests'
                    chart_title = "Snowflake ML Forecast: Daily Maintenance Requests"
                
                fig = go.Figure()
                
                # Add prediction line
                fig.add_trace(go.Scatter(
                    x=filtered_forecast['FORECAST_DATE'],
                    y=filtered_forecast[y_col],
                    mode='lines+markers',
                    name=y_label,
                    line=dict(color='#3498db', width=2),
                    marker=dict(size=8)
                ))
                
                # Add confidence interval
                fig.add_trace(go.Scatter(
                    x=pd.concat([filtered_forecast['FORECAST_DATE'], filtered_forecast['FORECAST_DATE'][::-1]]),
                    y=pd.concat([filtered_forecast['UPPER_BOUND'], filtered_forecast['LOWER_BOUND'][::-1]]),
                    fill='toself',
                    fillcolor='rgba(52, 152, 219, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='95% Confidence Interval'
                ))
                
                fig.update_layout(
                    title=chart_title,
                    xaxis_title="Date",
                    yaxis_title="Number of Failures",
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No forecast data available for selected filters")
        
        elif view_mode == "Weekly Summary":
            st.markdown("### 📊 Weekly Forecast Summary")
            
            if forecast_type == "💡 Bulb Failures":
                weekly_df = get_snowflake_weekly_forecast()
                y_col = 'TOTAL_PREDICTED_FAILURES'
                y_label = 'Total Failures'
            else:
                weekly_df = get_snowflake_weekly_all_issues_forecast()
                y_col = 'TOTAL_PREDICTED_REQUESTS'
                y_label = 'Total Requests'
            
            if not weekly_df.empty:
                # Weekly table
                st.dataframe(
                    weekly_df.style.background_gradient(subset=[y_col], cmap='YlOrRd'),
                    width='stretch'
                )
                
                # Weekly bar chart
                fig = px.bar(
                    weekly_df,
                    x='WEEK_START',
                    y=y_col,
                    color='PRIMARY_SEASON',
                    title=f"Weekly Predicted {y_label}",
                    labels={
                        y_col: y_label,
                        'WEEK_START': 'Week Starting',
                        'PRIMARY_SEASON': 'Season'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No weekly forecast data available")
        
        elif view_mode == "Monthly Budget":
            st.markdown("### 💰 Monthly Budget Forecast")
            
            if forecast_type == "💡 Bulb Failures":
                budget_df = get_snowflake_monthly_budget()
                
                if not budget_df.empty:
                    st.dataframe(
                        budget_df.style.format({
                            'MATERIAL_COST_INR': '₹{:,.0f}',
                            'LABOR_COST_INR': '₹{:,.0f}',
                            'TRANSPORT_COST_INR': '₹{:,.0f}',
                            'OVERHEAD_COST_INR': '₹{:,.0f}',
                            'TOTAL_MONTHLY_BUDGET_INR': '₹{:,.0f}'
                        }),
                        width='stretch'
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.bar(
                            budget_df,
                            x='MONTH',
                            y='TOTAL_MONTHLY_BUDGET_INR',
                            title="Monthly Budget Forecast (INR)",
                            labels={'TOTAL_MONTHLY_BUDGET_INR': 'Total Budget (₹)', 'MONTH': 'Month'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        total_costs = {
                            'Material': budget_df['MATERIAL_COST_INR'].sum(),
                            'Labor': budget_df['LABOR_COST_INR'].sum(),
                            'Transport': budget_df['TRANSPORT_COST_INR'].sum(),
                            'Overhead': budget_df['OVERHEAD_COST_INR'].sum()
                        }
                        fig = px.pie(
                            values=list(total_costs.values()),
                            names=list(total_costs.keys()),
                            title="Cost Distribution (Bulb Failures Only)"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No budget forecast data available")
            else:
                budget_df = get_snowflake_all_issues_monthly_budget()
                
                if not budget_df.empty:
                    st.dataframe(
                        budget_df.style.format({
                            'BULB_COST_INR': '₹{:,.0f}',
                            'WIRING_COST_INR': '₹{:,.0f}',
                            'POLE_COST_INR': '₹{:,.0f}',
                            'LABOR_COST_INR': '₹{:,.0f}',
                            'TRANSPORT_COST_INR': '₹{:,.0f}',
                            'TOTAL_MONTHLY_BUDGET_INR': '₹{:,.0f}'
                        }),
                        width='stretch'
                    )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = px.bar(
                            budget_df,
                            x='MONTH',
                            y='TOTAL_MONTHLY_BUDGET_INR',
                            title="Total Monthly Budget (All Issues)",
                            labels={'TOTAL_MONTHLY_BUDGET_INR': 'Total Budget (₹)', 'MONTH': 'Month'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        total_costs = {
                            'Bulbs': budget_df['BULB_COST_INR'].sum(),
                            'Wiring Kits': budget_df['WIRING_COST_INR'].sum(),
                            'Poles': budget_df['POLE_COST_INR'].sum(),
                            'Labor': budget_df['LABOR_COST_INR'].sum(),
                            'Transport': budget_df['TRANSPORT_COST_INR'].sum()
                        }
                        fig = px.pie(
                            values=list(total_costs.values()),
                            names=list(total_costs.keys()),
                            title="Cost Distribution (All Issues)"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No budget forecast data available")
        
        elif view_mode == "Issue Breakdown":
            st.markdown("### 📊 Issue Type Breakdown")
            
            # Show forecast comparison
            comparison_df = get_snowflake_forecast_comparison()
            issue_dist_df = get_snowflake_issue_type_distribution()
            
            if not comparison_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Forecast Comparison (30 Days)")
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=comparison_df['FORECAST_DATE'],
                        y=comparison_df['BULB_FAILURES'],
                        name='Bulb Failures',
                        marker_color='#3498db'
                    ))
                    fig.add_trace(go.Bar(
                        x=comparison_df['FORECAST_DATE'],
                        y=comparison_df['OTHER_ISSUES'],
                        name='Other Issues',
                        marker_color='#e74c3c'
                    ))
                    
                    fig.update_layout(
                        barmode='stack',
                        title="Daily Breakdown: Bulb Failures vs Other Issues",
                        xaxis_title="Date",
                        yaxis_title="Number of Issues"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("#### Historical Issue Distribution")
                    if not issue_dist_df.empty:
                        fig = px.pie(
                            issue_dist_df,
                            values='TOTAL_COUNT',
                            names='ISSUE_TYPE',
                            title="Issue Types (Historical Data)"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # Issue type details table
                st.markdown("#### Issue Type Details")
                if not issue_dist_df.empty:
                    st.dataframe(
                        issue_dist_df.style.background_gradient(subset=['PERCENTAGE'], cmap='Blues'),
                        width='stretch'
                    )
            else:
                st.info("No comparison data available")
        
        # Seasonal Analysis
        st.markdown("---")
        st.markdown("### 🌦️ Seasonal Risk Analysis")
        
        seasonal_df = get_snowflake_seasonal_forecast()
        if not seasonal_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    seasonal_df,
                    x='SEASON',
                    y='AVG_DAILY_FAILURES',
                    color='SEASONAL_RISK',
                    color_discrete_map={
                        'HIGH RISK': '#e74c3c',
                        'MEDIUM RISK': '#f39c12',
                        'LOW RISK': '#27ae60'
                    },
                    title="Average Daily Failures by Season",
                    labels={'AVG_DAILY_FAILURES': 'Avg Daily Failures', 'SEASON': 'Season'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.dataframe(
                    seasonal_df[['SEASON', 'TOTAL_FAILURES', 'AVG_DAILY_FAILURES', 'PEAK_DAY_FAILURES', 'SEASONAL_RISK']],
                    width='stretch'
                )
    
    else:
        # Fallback to PostGIS predictions when Snowflake is not available
        st.warning("⚠️ Snowflake ML not connected. Showing local PostGIS-based predictions.")
        st.caption("Configure Snowflake credentials in `.streamlit/secrets.toml` for ML-powered forecasts")
    st.markdown("Lights predicted to fail in the near future")
    
    # Controls
    col1, col2 = st.columns(2)
    
    with col1:
        days_ahead = st.slider("Prediction Window (days)", 7, 90, 30, 7)
    
    with col2:
        urgency_filter = st.multiselect(
            "Filter by Urgency",
            options=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
            default=["CRITICAL", "HIGH", "MEDIUM"]
        )
    
    # Load data
    with st.spinner("Loading predictions..."):
        predictions_df = get_predicted_failures(days_ahead)
        neighborhoods_df = get_neighborhoods()
    
    # Filter by urgency
    if urgency_filter:
        predictions_df = predictions_df[predictions_df['maintenance_urgency'].isin(urgency_filter)]
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    if not predictions_df.empty:
        critical = len(predictions_df[predictions_df['maintenance_urgency'] == 'CRITICAL'])
        high = len(predictions_df[predictions_df['maintenance_urgency'] == 'HIGH'])
        medium = len(predictions_df[predictions_df['maintenance_urgency'] == 'MEDIUM'])
        low = len(predictions_df[predictions_df['maintenance_urgency'] == 'LOW'])
        
        col1.metric("Critical", f"{critical:,}", delta_color="inverse")
        col2.metric("High", f"{high:,}", delta_color="inverse")
        col3.metric("Medium", f"{medium:,}")
        col4.metric("Low", f"{low:,}")
    else:
        col1.info("No predictions in selected window")
    
    st.markdown("---")
    
    # Map
    st.markdown("### Predicted Failures Map")
    m = create_base_map()
    m = add_neighborhoods_layer(m, neighborhoods_df)
    m = add_predicted_failures_layer(m, predictions_df)
    m = add_fullscreen_control(m)
    
    # Legend for urgency
    legend_items = [
        ("CRITICAL (0-7 days)", URGENCY_COLORS['CRITICAL']),
        ("HIGH (7-30 days)", URGENCY_COLORS['HIGH']),
        ("MEDIUM (30-60 days)", URGENCY_COLORS['MEDIUM']),
        ("LOW (60+ days)", URGENCY_COLORS['LOW'])
    ]
    m.get_root().html.add_child(folium.Element(create_legend_html(legend_items)))
    
    st_folium(m, width=1400, height=500)
    
    # Table
    st.markdown("### Prediction Details")
    if not predictions_df.empty:
        display_df = predictions_df[[
            'light_id', 'neighborhood_name', 'predicted_failure_date',
            'maintenance_urgency', 'failure_risk_score', 'season'
        ]].copy()
        
        # Color code urgency
        def highlight_urgency(row):
            color = URGENCY_COLORS.get(row['maintenance_urgency'], '#ffffff')
            return [f'background-color: {color}; color: white' if col == 'maintenance_urgency' 
                   else '' for col in row.index]
        
        st.dataframe(
            display_df.style.apply(highlight_urgency, axis=1),
            width='stretch'
        )
        
        # Timeline chart
        st.markdown("### Predicted Failures Timeline")
        timeline_df = predictions_df.groupby('predicted_failure_date').size().reset_index(name='count')
        timeline_df['predicted_failure_date'] = pd.to_datetime(timeline_df['predicted_failure_date'])
        
        fig = px.line(timeline_df, x='predicted_failure_date', y='count',
                     title=f"Predicted Failures Over Next {days_ahead} Days",
                     labels={'count': 'Number of Predicted Failures', 
                            'predicted_failure_date': 'Date'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Seasonal patterns
        st.markdown("### Seasonal Failure Patterns")
        seasonal_df = get_seasonal_patterns()
        if not seasonal_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(seasonal_df, x='season', y='request_count',
                           title="Historical Maintenance Requests by Season",
                           labels={'request_count': 'Number of Requests', 'season': 'Season'})
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(seasonal_df, x='season', y='avg_resolution_hours',
                           title="Average Resolution Time by Season",
                           labels={'avg_resolution_hours': 'Hours', 'season': 'Season'})
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No predictions match the selected criteria")

elif page == "🏭 Supplier Coverage":
    st.title("🏭 Supplier Coverage Analysis")
    st.markdown("Analysis of supplier locations and service coverage")
    
    # Load data
    with st.spinner("Loading supplier data..."):
        suppliers_df = get_suppliers()
        coverage_stats = get_supplier_coverage()
        neighborhoods_df = get_neighborhoods()
        all_lights = get_all_lights()
    
    # Metrics
    if not coverage_stats.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        stats = coverage_stats.iloc[0]
        col1.metric("Total Suppliers", len(suppliers_df))
        col2.metric("Lights within 5km", f"{stats['within_5km']:,}")
        col3.metric("Lights within 10km", f"{stats['within_10km']:,}")
        col4.metric("Avg Distance", f"{stats['avg_distance_km']:.2f} km")
    
    st.markdown("---")
    
    # Map
    st.markdown("### Supplier Coverage Map")
    
    # Add checkbox to show/hide connection lines
    show_connections = st.checkbox("Show Neighborhood-Supplier Connections", value=True)
    
    m = create_base_map()
    m = add_neighborhoods_layer(m, neighborhoods_df)
    m = add_suppliers_layer(m, suppliers_df)
    
    # Add connection lines if enabled
    if show_connections:
        neighborhood_dist = get_neighborhood_supplier_distance()
        if not neighborhood_dist.empty:
            m = add_neighborhood_supplier_lines(m, neighborhood_dist, neighborhoods_df, suppliers_df)
    
    # Add some sample lights to show coverage (use fixed seed to prevent flickering)
    sample_lights = all_lights.sample(min(500, len(all_lights)), random_state=42) if not all_lights.empty else pd.DataFrame()
    if not sample_lights.empty:
        m = add_lights_layer(m, sample_lights)
    
    m = add_fullscreen_control(m)
    
    # Add legend
    legend_items = [
        ("Operational", STATUS_COLORS['operational'], 'circle'),
        ("Maintenance Required", STATUS_COLORS['maintenance_required'], 'circle'),
        ("Faulty", STATUS_COLORS['faulty'], 'circle'),
        ("Supplier", "#3498db", 'marker')
    ]
    
    if show_connections:
        # Add a note about connection lines in the legend
        legend_items.append(("Connection (to nearest supplier)", "#e74c3c", 'line'))
    
    m.get_root().html.add_child(folium.Element(create_legend_html(legend_items)))
    
    st_folium(m, width=1400, height=500)
    
    # Supplier details table
    st.markdown("### Supplier Details")
    if not suppliers_df.empty:
        display_df = suppliers_df[[
            'name', 'specialization', 'service_radius_km', 
            'avg_response_hours', 'contact_phone'
        ]].copy()
        
        st.dataframe(display_df, width='stretch')
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Specialization distribution
            spec_counts = suppliers_df.groupby('specialization').size().reset_index(name='count')
            fig = px.pie(spec_counts, values='count', names='specialization',
                        title="Supplier Specialization Distribution")
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            # Service radius distribution
            fig = px.histogram(suppliers_df, x='service_radius_km', nbins=10,
                             title="Service Radius Distribution",
                             labels={'service_radius_km': 'Service Radius (km)', 
                                   'count': 'Number of Suppliers'})
            st.plotly_chart(fig, width='stretch')
        
        # Coverage analysis
        st.markdown("### Coverage Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not coverage_stats.empty:
                stats = coverage_stats.iloc[0]
                
                coverage_data = pd.DataFrame({
                    'Distance Range': ['Within 5km', '5-10km', 'Beyond 10km'],
                    'Number of Lights': [stats['within_5km'], 
                              stats['within_10km'] - stats['within_5km'],
                              stats['beyond_10km']]
                })
                
                fig = px.bar(coverage_data, x='Distance Range', y='Number of Lights',
                            title="Lights by Distance to Nearest Supplier",
                            color='Distance Range',
                            color_discrete_map={
                                'Within 5km': '#2ecc71',
                                '5-10km': '#f39c12',
                                'Beyond 10km': '#e74c3c'
                            })
                st.plotly_chart(fig, width='stretch')
        
        with col2:
            # Neighborhood to supplier distances
            neighborhood_dist = get_neighborhood_supplier_distance()
            if not neighborhood_dist.empty:
                fig = px.bar(neighborhood_dist, 
                            x='neighborhood', 
                            y='distance_km',
                            title="Distance from Neighborhood to Nearest Supplier",
                            labels={'distance_km': 'Distance (km)', 'neighborhood': 'Neighborhood'},
                            hover_data=['nearest_supplier', 'specialization', 'lights_in_neighborhood'],
                            color='distance_km',
                            color_continuous_scale='RdYlGn_r')
                fig.update_xaxes(tickangle=-45)
                st.plotly_chart(fig, width='stretch')
        
        # Table showing neighborhood coverage details
        st.markdown("### Neighborhood-Supplier Coverage Details")
        neighborhood_dist = get_neighborhood_supplier_distance()
        if not neighborhood_dist.empty:
            st.dataframe(
                neighborhood_dist.style.background_gradient(subset=['distance_km'], cmap='RdYlGn_r')
                                      .format({'distance_km': '{:.2f} km'}),
                width='stretch'
            )

elif page == "🎮 Live Demo Controls":
    st.title("🎮 Live Demo Controls")
    st.markdown("Interactive controls for demonstrating real-time updates")
    
    st.warning("⚠️ These actions modify the database. Use for demo purposes only!")
    
    # Current stats
    with st.spinner("Loading current status..."):
        all_lights = get_all_lights()
    
    col1, col2, col3, col4 = st.columns(4)
    
    if not all_lights.empty:
        total = len(all_lights)
        operational = len(all_lights[all_lights['status'] == 'operational'])
        faulty = len(all_lights[all_lights['status'] == 'faulty'])
        maintenance = len(all_lights[all_lights['status'] == 'maintenance_required'])
        
        col1.metric("Total Lights", f"{total:,}")
        col2.metric("Operational", f"{operational:,}")
        col3.metric("Faulty", f"{faulty:,}")
        col4.metric("Maintenance Required", f"{maintenance:,}")
    
    st.markdown("---")
    
    # Control 1: Simulate random failure
    st.markdown("### 🔴 Simulate Light Failure")
    st.markdown("Randomly select an operational light and set it to faulty status")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button("Simulate Random Failure", type="primary", width='stretch'):
            success, message = simulate_light_failure()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        st.info("This will update one random operational light to faulty status and refresh the dashboard")
    
    st.markdown("---")
    
    # Control 2: Trigger scheduled maintenance
    st.markdown("### 🟡 Trigger Scheduled Maintenance")
    st.markdown("Set multiple operational lights to require maintenance")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        count = st.number_input("Number of lights", min_value=1, max_value=20, value=5)
        
        if st.button("Trigger Maintenance", type="secondary", width='stretch'):
            success, message = trigger_scheduled_maintenance(count)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        st.info(f"This will set {count} random operational lights to maintenance_required status")
    
    st.markdown("---")
    
    # Control 3: Refresh data
    st.markdown("### 🔄 Refresh Dashboard")
    st.markdown("Clear cache and reload all data from database")
    
    if st.button("Refresh All Data", width='content'):
        st.cache_data.clear()
        st.success("Cache cleared! Dashboard will refresh.")
        st.rerun()
    
    st.markdown("---")
    
    # Control 4: Auto-refresh toggle
    st.markdown("### ⏱️ Auto-Refresh")
    
    auto_refresh = st.checkbox("Enable auto-refresh (every 30 seconds)")
    
    if auto_refresh:
        import time
        st.info("Auto-refresh enabled. Page will reload every 30 seconds.")
        time.sleep(30)
        st.rerun()
    
    st.markdown("---")
    
    # Demo script hints
    st.markdown("### 📝 Demo Script Hints")
    
    with st.expander("🎤 Presenter Notes"):
        st.markdown("""
        **Demo Flow Suggestions:**
        
        1. **Start with Neighborhood Overview** 
           - Show the complete map with all layers
           - Explain the color coding and spatial distribution
           
        2. **Navigate to Faulty Lights Analysis**
           - Show current faulty lights with nearest suppliers
           - Demonstrate filtering by neighborhood
           
        3. **Show Predictive Maintenance**
           - Explain the prediction algorithm
           - Show timeline of upcoming failures
           - Discuss seasonal patterns
           
        4. **Demonstrate Live Updates** (this page)
           - Click "Simulate Random Failure"
           - Go back to Faulty Lights page - show new red marker
           - Go to Neighborhood Overview - show updated metrics
           
        5. **Supplier Coverage**
           - Show supplier locations and service areas
           - Discuss coverage gaps
           
        **Key Talking Points:**
        - Real-time PostGIS queries (no caching delays)
        - Enrichment data improves predictions
        - Spatial operations (ST_Within, ST_Distance)
        - Production-ready architecture
        """)
    
    with st.expander("🔍 Quick Validation"):
        st.markdown("""
        **Verify Demo is Working:**
        
        - ✅ All metrics show non-zero values
        - ✅ Maps load with markers visible
        - ✅ Tables display data
        - ✅ Simulate failure updates the database
        - ✅ Refresh shows updated counts
        
        **Troubleshooting:**
        - If no data shows: Check if `data/load_data.sql` was run
        - If maps are empty: Verify PostgreSQL container is running
        - If refresh fails: Check database connection in config.py
        """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Street Lights Maintenance Dashboard | PostGIS + Apache NiFi Demo | "
    f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"
    "</div>",
    unsafe_allow_html=True
)

