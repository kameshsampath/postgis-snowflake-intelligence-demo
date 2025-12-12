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
Map utility functions for Streamlit Dashboard
Creates Folium maps with various layers
"""

import folium
from folium import plugins
import json
from config import MAP_CONFIG, STATUS_COLORS, URGENCY_COLORS


def create_base_map(center=None, zoom=None):
    """
    Create base Folium map
    """
    center = center or MAP_CONFIG["center"]
    zoom = zoom or MAP_CONFIG["zoom"]
    
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=MAP_CONFIG["tiles"]
    )
    
    return m


def add_neighborhoods_layer(map_obj, neighborhoods_df):
    """
    Add neighborhood polygons to map
    """
    if neighborhoods_df.empty:
        return map_obj
    
    for _, row in neighborhoods_df.iterrows():
        try:
            geojson = json.loads(row['boundary_geojson'])
            
            folium.GeoJson(
                geojson,
                name=row['name'],
                style_function=lambda x: {
                    'fillColor': '#3498db',
                    'color': '#2c3e50',
                    'weight': 2,
                    'fillOpacity': 0.1
                },
                tooltip=folium.Tooltip(
                    f"<b>{row['name']}</b><br>"
                    f"Population: {row['population']:,}",
                    sticky=True
                )
            ).add_to(map_obj)
        except Exception as e:
            # Skip invalid geometries
            continue
    
    return map_obj


def add_lights_layer(map_obj, lights_df, show_status_legend=True):
    """
    Add street lights markers to map (color-coded by status)
    """
    if lights_df.empty:
        return map_obj
    
    # Create marker cluster
    marker_cluster = plugins.MarkerCluster(
        name="Street Lights",
        options={
            'maxClusterRadius': 50,
            'disableClusteringAtZoom': 15
        }
    )
    
    for _, light in lights_df.iterrows():
        # Determine color based on status
        color = STATUS_COLORS.get(light['status'], '#95a5a6')
        
        # Create popup content
        popup_html = f"""
        <div style="font-family: Arial; width: 200px;">
            <h4 style="margin: 0;">{light['light_id']}</h4>
            <hr style="margin: 5px 0;">
            <b>Status:</b> {light['status']}<br>
            <b>Neighborhood:</b> {light.get('neighborhood_name', 'N/A')}<br>
            <b>Wattage:</b> {light.get('wattage', 'N/A')}W<br>
            <b>Age:</b> {light.get('age_months', 0)} months<br>
        """
        
        if light.get('failure_risk_score'):
            popup_html += f"<b>Risk Score:</b> {light['failure_risk_score']:.2f}<br>"
        
        if light.get('predicted_failure_date'):
            popup_html += f"<b>Predicted Failure:</b> {light['predicted_failure_date']}<br>"
        
        popup_html += "</div>"
        
        # Create marker
        folium.CircleMarker(
            location=[light['latitude'], light['longitude']],
            radius=6,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{light['light_id']} - {light['status']}",
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=2
        ).add_to(marker_cluster)
    
    marker_cluster.add_to(map_obj)
    
    return map_obj


def add_suppliers_layer(map_obj, suppliers_df):
    """
    Add supplier markers with service radius circles
    """
    if suppliers_df.empty:
        return map_obj
    
    for _, supplier in suppliers_df.iterrows():
        # Supplier marker
        folium.Marker(
            location=[supplier['latitude'], supplier['longitude']],
            popup=f"""
            <div style="font-family: Arial; width: 200px;">
                <h4 style="margin: 0;">{supplier['name']}</h4>
                <hr style="margin: 5px 0;">
                <b>Specialization:</b> {supplier['specialization']}<br>
                <b>Service Radius:</b> {supplier['service_radius_km']} km<br>
                <b>Avg Response:</b> {supplier['avg_response_hours']} hours<br>
                <b>Contact:</b> {supplier['contact_phone']}<br>
            </div>
            """,
            tooltip=supplier['name'],
            icon=folium.Icon(color='blue', icon='wrench', prefix='fa')
        ).add_to(map_obj)
        
        # Service radius circle
        folium.Circle(
            location=[supplier['latitude'], supplier['longitude']],
            radius=supplier['service_radius_km'] * 1000,  # Convert km to meters
            color='blue',
            fill=True,
            fillOpacity=0.05,
            weight=1,
            dash_array='5, 5'
        ).add_to(map_obj)
    
    return map_obj


def add_predicted_failures_layer(map_obj, predictions_df):
    """
    Add markers for lights predicted to fail soon
    Color-coded by urgency
    """
    if predictions_df.empty:
        return map_obj
    
    for _, light in predictions_df.iterrows():
        urgency = light.get('maintenance_urgency', 'LOW')
        color = URGENCY_COLORS.get(urgency, '#95a5a6')
        
        popup_html = f"""
        <div style="font-family: Arial; width: 220px;">
            <h4 style="margin: 0; color: {color};">{light['light_id']}</h4>
            <hr style="margin: 5px 0;">
            <b>Current Status:</b> {light['status']}<br>
            <b>Neighborhood:</b> {light['neighborhood_name']}<br>
            <b>Predicted Failure:</b> {light['predicted_failure_date']}<br>
            <b>Risk Score:</b> {light['failure_risk_score']:.2f}<br>
            <b>Urgency:</b> <span style="color: {color}; font-weight: bold;">{urgency}</span><br>
            <b>Season:</b> {light['season']}<br>
        </div>
        """
        
        folium.CircleMarker(
            location=[light['latitude'], light['longitude']],
            radius=8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{light['light_id']} - {urgency}",
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.8,
            weight=3
        ).add_to(map_obj)
    
    return map_obj


def create_legend_html(items):
    """
    Create HTML legend for map
    items: list of (label, color) tuples or (label, color, marker_type) tuples
    marker_type can be 'circle' (default), 'marker', or 'line'
    """
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 240px; 
                background-color: white; z-index:9999; 
                border:2px solid grey; border-radius: 5px;
                padding: 10px; font-size: 14px;">
        <h4 style="margin: 0 0 10px 0;">Legend</h4>
    '''
    
    for item in items:
        if len(item) == 3:
            label, color, marker_type = item
        else:
            label, color = item
            marker_type = 'circle'
        
        if marker_type == 'marker':
            # Show as a wrench/tool icon for suppliers
            legend_html += f'''
            <p style="margin: 5px 0; display: flex; align-items: center;">
                <span style="color: {color}; font-size: 18px; width: 20px; text-align: center;">
                    🔧
                </span>
                <span style="margin-left: 5px;">{label}</span>
            </p>
            '''
        elif marker_type == 'line':
            # Show as a dashed line for connections
            legend_html += f'''
            <p style="margin: 5px 0; display: flex; align-items: center;">
                <span style="width: 20px; height: 3px; 
                             background: repeating-linear-gradient(
                                 to right,
                                 {color} 0px,
                                 {color} 6px,
                                 transparent 6px,
                                 transparent 10px
                             );
                             display: inline-block;">
                </span>
                <span style="margin-left: 5px; font-size: 12px;">{label}</span>
            </p>
            '''
        else:
            # Show as a circle (for lights)
            legend_html += f'''
            <p style="margin: 5px 0;">
                <span style="background-color: {color}; 
                             width: 20px; height: 20px; 
                             display: inline-block; 
                             border-radius: 50%; 
                             border: 1px solid #333;">
                </span> {label}
            </p>
            '''
    
    legend_html += '</div>'
    
    return legend_html


def add_neighborhood_supplier_lines(map_obj, neighborhood_supplier_df, neighborhoods_df, suppliers_df):
    """
    Add lines connecting neighborhoods to their nearest suppliers with distance labels
    """
    if neighborhood_supplier_df.empty or neighborhoods_df.empty or suppliers_df.empty:
        return map_obj
    
    # Create a feature group for connection lines so they're on top
    connections_group = folium.FeatureGroup(name='Supplier Connections')
    
    for _, row in neighborhood_supplier_df.iterrows():
        # Find neighborhood center
        neighborhood = neighborhoods_df[neighborhoods_df['name'] == row['neighborhood']]
        if neighborhood.empty:
            continue
        
        try:
            geojson = json.loads(neighborhood.iloc[0]['boundary_geojson'])
            # Get centroid from the GeoJSON
            if geojson['type'] == 'Polygon':
                coords = geojson['coordinates'][0]
            elif geojson['type'] == 'MultiPolygon':
                coords = geojson['coordinates'][0][0]
            else:
                continue
            
            # Calculate centroid (simple average of coordinates)
            # GeoJSON uses [lon, lat] order
            lats = [coord[1] for coord in coords]
            lons = [coord[0] for coord in coords]
            nh_lat = sum(lats) / len(lats)
            nh_lon = sum(lons) / len(lons)
        except Exception as e:
            print(f"Error processing neighborhood {row.get('neighborhood', 'unknown')}: {e}")
            continue
        
        # Find supplier location
        supplier = suppliers_df[suppliers_df['name'] == row['nearest_supplier']]
        if supplier.empty:
            continue
        
        supplier_lat = supplier.iloc[0]['latitude']
        supplier_lon = supplier.iloc[0]['longitude']
        
        # Draw line with more visibility
        folium.PolyLine(
            locations=[[nh_lat, nh_lon], [supplier_lat, supplier_lon]],
            color='#e74c3c',  # Red color for better visibility
            weight=3,
            opacity=0.8,
            dash_array='10, 5',
            popup=f"{row['neighborhood']} → {row['nearest_supplier']}: {row['distance_km']:.2f} km"
        ).add_to(connections_group)
        
        # Add distance label at midpoint
        mid_lat = (nh_lat + supplier_lat) / 2
        mid_lon = (nh_lon + supplier_lon) / 2
        
        folium.Marker(
            location=[mid_lat, mid_lon],
            icon=folium.DivIcon(html=f'''
                <div style="
                    background-color: white;
                    border: 2px solid #e74c3c;
                    border-radius: 5px;
                    padding: 4px 8px;
                    font-size: 12px;
                    font-weight: bold;
                    color: #e74c3c;
                    white-space: nowrap;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.4);
                ">
                    {row['distance_km']:.1f} km
                </div>
            '''),
            popup=f"{row['neighborhood']} ↔ {row['nearest_supplier']}"
        ).add_to(connections_group)
    
    # Add the feature group to the map
    connections_group.add_to(map_obj)
    
    return map_obj


def add_fullscreen_control(map_obj):
    """Add fullscreen button to map"""
    plugins.Fullscreen(
        position='topleft',
        title='Fullscreen',
        title_cancel='Exit fullscreen',
        force_separate_button=True
    ).add_to(map_obj)
    
    return map_obj


