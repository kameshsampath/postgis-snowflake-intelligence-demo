-- Copyright 2025 Kamesh Sampath
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- =====================================================
-- Semantic View: Streetlights Intelligence
-- =====================================================
-- Creates a Semantic View over CLD tables for use with:
--   - Snowflake Intelligence (natural language queries)
--   - Cortex Agent (structured SQL generation)
--
-- IMPORTANT: CLD surfaces tables with quoted lowercase identifiers.
-- All table/column references use "schema"."table"."column" notation.
--
-- Variables to replace:
--   ${PREFIX} = your demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
-- =====================================================

USE WAREHOUSE ${PREFIX}_STREETLIGHTS_WH;

CREATE OR REPLACE SEMANTIC VIEW ${PREFIX}_STREETLIGHTS_CLD."streetlights".streetlights_semantic_view
  COMMENT = 'Semantic view for streetlight infrastructure intelligence queries'
AS

  -- ===================================================
  -- Table: street_lights (core fact table)
  -- ===================================================
  TABLE ${PREFIX}_STREETLIGHTS_CLD."streetlights"."street_lights"
    PRIMARY KEY ("light_id")
    SYNONYMS ('lamps', 'light poles', 'lighting fixtures', 'lights', 'luminaires', 'street lamps')
    COMMENT 'Core operational data for all street lights including location, status, and power consumption.'

    COLUMN "light_id"
      SYNONYMS ('asset_id', 'fixture_id', 'lamp_id', 'pole_id')
      COMMENT 'Unique identifier for each street light in format SL-XXXX.'
      SAMPLE VALUES ('SL-0001', 'SL-0500', 'SL-2500')

    COLUMN "latitude"
      SYNONYMS ('lat', 'y_coordinate')
      COMMENT 'Latitude in WGS84 (SRID 4326).'

    COLUMN "longitude"
      SYNONYMS ('lng', 'lon', 'x_coordinate')
      COMMENT 'Longitude in WGS84 (SRID 4326).'

    COMPUTED COLUMN location
      COMMENT 'Geographic point reconstructed from lat/lng for spatial queries.'
      AS ST_MAKEPOINT("longitude", "latitude")

    COLUMN "status"
      SYNONYMS ('condition', 'light_status', 'operational_status', 'state')
      COMMENT 'Current operational status: operational, faulty, or maintenance_required.'
      SAMPLE VALUES ('operational', 'faulty', 'maintenance_required')

    COLUMN "wattage"
      SYNONYMS ('energy_usage', 'power', 'power_consumption', 'watts')
      COMMENT 'Power consumption in watts. LED: 100W, sodium vapor: up to 250W.'
      SAMPLE VALUES ('100', '150', '200', '250')

    COLUMN "installation_date"
      SYNONYMS ('commissioned_date', 'install_date', 'setup_date')
      COMMENT 'Date when the street light was installed. Used for age calculations.'

    COLUMN "last_maintenance"
      SYNONYMS ('last_inspection', 'last_repair', 'last_service')
      COMMENT 'Timestamp of most recent maintenance performed.'

    COLUMN "neighborhood_id"
      SYNONYMS ('area_id', 'district_id', 'zone_id')
      COMMENT 'Foreign key to neighborhoods table for geographic grouping.'
      SAMPLE VALUES ('NH-001', 'NH-025', 'NH-050')

  -- ===================================================
  -- Table: maintenance_requests
  -- ===================================================
  TABLE ${PREFIX}_STREETLIGHTS_CLD."streetlights"."maintenance_requests"
    PRIMARY KEY ("request_id")
    SYNONYMS ('complaints', 'issues', 'maintenance_tickets', 'repairs', 'service_requests', 'work_orders')
    COMMENT 'Historical and active maintenance requests tracking issues, response times, and resolution.'

    COLUMN "request_id"
      SYNONYMS ('case_id', 'incident_id', 'ticket_id', 'work_order_id')
      COMMENT 'Unique identifier in format REQ-XXXX.'
      SAMPLE VALUES ('REQ-0001', 'REQ-0250', 'REQ-0500')

    COLUMN "light_id"
      SYNONYMS ('asset_id', 'fixture_id', 'lamp_id')
      COMMENT 'Foreign key to the street light requiring maintenance.'

    COLUMN "reported_at"
      SYNONYMS ('created_at', 'opened_at', 'report_date')
      COMMENT 'Timestamp when the issue was reported. Start of SLA clock.'

    COLUMN "resolved_at"
      SYNONYMS ('closed_at', 'completed_at', 'fixed_at')
      COMMENT 'Timestamp when resolved. NULL means still open.'

    COLUMN "issue_type"
      SYNONYMS ('defect_type', 'failure_type', 'problem_category', 'problem_type')
      COMMENT 'Category: bulb_failure, wiring, pole_damage, sensor_malfunction, timer_issue, vandalism, storm_damage.'
      SAMPLE VALUES ('bulb_failure', 'wiring', 'pole_damage', 'sensor_malfunction', 'timer_issue')

    COLUMN "description"
      COMMENT 'Free-text description of the issue from field staff or residents.'

  -- ===================================================
  -- Table: neighborhoods
  -- ===================================================
  TABLE ${PREFIX}_STREETLIGHTS_CLD."streetlights"."neighborhoods"
    PRIMARY KEY ("neighborhood_id")
    SYNONYMS ('areas', 'districts', 'localities', 'regions', 'wards', 'zones')
    COMMENT 'Geographic neighborhoods with boundaries and population data for spatial aggregation.'

    COLUMN "neighborhood_id"
      SYNONYMS ('area_id', 'district_id', 'locality_id', 'zone_id')
      COMMENT 'Unique identifier in format NH-XXX.'
      SAMPLE VALUES ('NH-001', 'NH-025', 'NH-050')

    COLUMN "name"
      SYNONYMS ('area_name', 'district_name', 'neighborhood_name')
      COMMENT 'Human-readable neighborhood name.'

    COLUMN "population"
      SYNONYMS ('inhabitants', 'people', 'residents')
      COMMENT 'Estimated population for per-capita calculations.'
      SAMPLE VALUES ('50000', '125000', '200000')

  -- ===================================================
  -- Table: suppliers
  -- ===================================================
  TABLE ${PREFIX}_STREETLIGHTS_CLD."streetlights"."suppliers"
    PRIMARY KEY ("supplier_id")
    SYNONYMS ('contractors', 'maintenance_companies', 'service_providers', 'vendors')
    COMMENT 'Light equipment suppliers with coverage areas, response times, and specializations.'

    COLUMN "supplier_id"
      SYNONYMS ('company_id', 'contractor_id', 'vendor_id')
      COMMENT 'Unique identifier in format SUP-XXX.'
      SAMPLE VALUES ('SUP-001', 'SUP-010', 'SUP-020')

    COLUMN "name"
      SYNONYMS ('company_name', 'supplier_name', 'vendor_name')
      COMMENT 'Supplier company name.'

    COLUMN "latitude"
      COMMENT 'Supplier office latitude in WGS84.'

    COLUMN "longitude"
      COMMENT 'Supplier office longitude in WGS84.'

    COMPUTED COLUMN supplier_location
      COMMENT 'Geographic point for supplier office, reconstructed from lat/lng.'
      AS ST_MAKEPOINT("longitude", "latitude")

    COLUMN "contact_phone"
      SYNONYMS ('contact', 'phone', 'telephone')
      COMMENT 'Contact phone number for dispatch.'

    COLUMN "service_radius_km"
      SYNONYMS ('coverage_distance', 'coverage_radius', 'service_area')
      COMMENT 'Maximum service distance in kilometers.'
      SAMPLE VALUES ('8', '10', '12')

    COLUMN "avg_response_hours"
      SYNONYMS ('response_time', 'sla_hours', 'turnaround_time')
      COMMENT 'Average response time in hours. Lower is better.'
      SAMPLE VALUES ('3', '4', '6')

    COLUMN "specialization"
      SYNONYMS ('equipment_type', 'expertise', 'specialty')
      COMMENT 'Equipment specialization: LED, Sodium Vapor, or All.'
      SAMPLE VALUES ('LED', 'Sodium Vapor', 'All')

  -- ===================================================
  -- Table: weather_enrichment
  -- ===================================================
  TABLE ${PREFIX}_STREETLIGHTS_CLD."streetlights"."weather_enrichment"
    PRIMARY KEY ("light_id", "season")
    SYNONYMS ('climate_data', 'seasonal_data', 'weather_data', 'weather_factors')
    COMMENT 'Seasonal weather patterns and failure risk predictions per light.'

    COLUMN "light_id"
      COMMENT 'Foreign key to street light.'

    COLUMN "season"
      SYNONYMS ('seasonal_period', 'time_of_year', 'weather_season')
      COMMENT 'Season: spring, summer, fall, or winter.'
      SAMPLE VALUES ('spring', 'summer', 'fall', 'winter')

    COLUMN "avg_temperature_c"
      SYNONYMS ('average_temperature', 'avg_temp', 'temperature')
      COMMENT 'Average temperature in Celsius for the season.'
      SAMPLE VALUES ('22.80', '28.50', '35.20')

    COLUMN "rainfall_mm"
      SYNONYMS ('average_rainfall', 'precipitation', 'rain')
      COMMENT 'Average rainfall in millimeters for the season.'
      SAMPLE VALUES ('10.50', '25.30', '185.75')

    COLUMN "failure_risk_score"
      SYNONYMS ('failure_likelihood', 'failure_probability', 'risk_level', 'risk_score')
      COMMENT 'Predicted failure probability 0.0 to 1.0. Higher in wet/hot seasons.'
      SAMPLE VALUES ('0.35', '0.62', '0.78')

    COLUMN "predicted_failure_date"
      SYNONYMS ('expected_failure', 'failure_prediction', 'predicted_outage')
      COMMENT 'ML-predicted failure date based on weather and historical patterns.'

  -- ===================================================
  -- Table: demographics
  -- ===================================================
  TABLE ${PREFIX}_STREETLIGHTS_CLD."streetlights"."demographics"
    PRIMARY KEY ("neighborhood_id")
    SYNONYMS ('area_demographics', 'census_data', 'population_data')
    COMMENT 'Neighborhood demographics for priority-based maintenance scheduling.'

    COLUMN "neighborhood_id"
      SYNONYMS ('area_id', 'district_id', 'zone_id')
      COMMENT 'Foreign key to neighborhoods table.'

    COLUMN "population_density"
      SYNONYMS ('density', 'people_per_sqkm', 'residents_per_area')
      COMMENT 'People per square kilometer. Urban >10000, suburban 5000-10000, rural <5000.'
      SAMPLE VALUES ('5200', '9800', '12500')

    COLUMN "urban_classification"
      SYNONYMS ('area_type', 'development_level', 'urbanization', 'zone_type')
      COMMENT 'Development level: urban, suburban, or rural.'
      SAMPLE VALUES ('urban', 'suburban', 'rural')

  -- ===================================================
  -- Table: power_grid_zones
  -- ===================================================
  TABLE ${PREFIX}_STREETLIGHTS_CLD."streetlights"."power_grid_zones"
    PRIMARY KEY ("light_id")
    SYNONYMS ('electrical_data', 'grid_data', 'power_grid', 'power_supply')
    COMMENT 'Electrical grid zone data for correlating light failures with grid issues.'

    COLUMN "light_id"
      COMMENT 'Foreign key to street light.'

    COLUMN "grid_zone"
      SYNONYMS ('electrical_zone', 'grid_area', 'power_zone', 'supply_zone')
      COMMENT 'Power grid zone identifier (e.g., ZONE-A, ZONE-B).'
      SAMPLE VALUES ('ZONE-A', 'ZONE-B', 'ZONE-C')

    COLUMN "avg_load_percent"
      SYNONYMS ('capacity_usage', 'grid_load', 'load_percentage', 'power_load')
      COMMENT 'Average grid load percentage. Above 80% indicates potential stress.'
      SAMPLE VALUES ('65.40', '78.50', '82.30')

    COLUMN "outage_history_count"
      SYNONYMS ('blackouts', 'outage_count', 'outages', 'power_outages')
      COMMENT 'Historical power outage count. Higher = less reliable supply.'
      SAMPLE VALUES ('1', '3', '5')

  -- ===================================================
  -- Relationships
  -- ===================================================
  RELATIONSHIPS
    ${PREFIX}_STREETLIGHTS_CLD."streetlights"."street_lights"("neighborhood_id")
      REFERENCES ${PREFIX}_STREETLIGHTS_CLD."streetlights"."neighborhoods"("neighborhood_id")
    ,
    ${PREFIX}_STREETLIGHTS_CLD."streetlights"."maintenance_requests"("light_id")
      REFERENCES ${PREFIX}_STREETLIGHTS_CLD."streetlights"."street_lights"("light_id")
    ,
    ${PREFIX}_STREETLIGHTS_CLD."streetlights"."weather_enrichment"("light_id")
      REFERENCES ${PREFIX}_STREETLIGHTS_CLD."streetlights"."street_lights"("light_id")
    ,
    ${PREFIX}_STREETLIGHTS_CLD."streetlights"."demographics"("neighborhood_id")
      REFERENCES ${PREFIX}_STREETLIGHTS_CLD."streetlights"."neighborhoods"("neighborhood_id")
    ,
    ${PREFIX}_STREETLIGHTS_CLD."streetlights"."power_grid_zones"("light_id")
      REFERENCES ${PREFIX}_STREETLIGHTS_CLD."streetlights"."street_lights"("light_id")
;
