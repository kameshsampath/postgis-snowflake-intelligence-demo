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
-- Actual CLD table schema (7 tables):
--   street_lights:      id, pole_id, latitude, longitude, neighborhood,
--                       install_date, wattage, light_type, status
--   maintenance_records: id, light_id, date, type, description, cost, technician
--   energy_consumption: id, light_id, date, hour, kwh, voltage, power_factor
--   light_sensors:      id, light_id, timestamp, lux, motion_detected, temperature
--   demographics:       neighborhood, population, median_income, commercial_pct
--   power_grid_zones:   zone_id, zone_name, capacity_kw, current_load_kw, latitude, longitude
--   weather_enrichment: date, season, temperature, humidity, wind_speed, precipitation
--
-- IMPORTANT: CLD preserves PostgreSQL casing — all identifiers are quoted lowercase.
--
-- Variables to replace:
--   <% PREFIX %> = demo_resource_prefix in UPPERCASE (e.g., KAMESHS)
-- =====================================================

USE WAREHOUSE <% PREFIX %>_STREETLIGHTS_WH;

-- Semantic view lives in the regular DB (CLD is read-only; tables are still referenced from CLD)
CREATE OR REPLACE SEMANTIC VIEW <% PREFIX %>_STREETLIGHTS.PUBLIC.streetlights_semantic_view

  TABLES (

    street_lights AS <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."street_lights"
      PRIMARY KEY (id)
      WITH SYNONYMS ('lamps', 'light fixtures', 'light poles', 'lights', 'luminaires', 'street lamps')
      COMMENT = 'Core operational data for all street lights: location, status, wattage, and type.',

    maintenance_records AS <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."maintenance_records"
      PRIMARY KEY (id)
      WITH SYNONYMS ('maintenance_history', 'repairs', 'service_records', 'work_orders')
      COMMENT = 'Historical maintenance performed on street lights including cost and technician.',

    energy_consumption AS <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."energy_consumption"
      PRIMARY KEY (id)
      WITH SYNONYMS ('energy_data', 'energy_usage', 'kwh_readings', 'power_usage')
      COMMENT = 'Hourly energy consumption readings per street light.',

    light_sensors AS <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."light_sensors"
      PRIMARY KEY (id)
      WITH SYNONYMS ('iot_sensors', 'sensor_data', 'sensor_readings')
      COMMENT = 'IoT sensor readings: ambient light (lux), motion, and temperature per light.',

    demographics AS <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."demographics"
      PRIMARY KEY (neighborhood)
      WITH SYNONYMS ('area_demographics', 'census_data', 'neighborhood_data', 'population_data')
      COMMENT = 'Neighborhood-level demographics: population, median income, and commercial share.',

    power_grid_zones AS <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."power_grid_zones"
      PRIMARY KEY (zone_id)
      WITH SYNONYMS ('electrical_zones', 'grid_data', 'grid_zones', 'power_supply')
      COMMENT = 'Electrical grid zones with capacity and current load.',

    weather AS <% PREFIX %>_STREETLIGHTS_CLD."streetlights"."weather_enrichment"
      PRIMARY KEY (date)
      WITH SYNONYMS ('climate_data', 'daily_weather', 'weather_data', 'weather_factors')
      COMMENT = 'Daily weather data including temperature, humidity, wind, and precipitation.'

  )

  RELATIONSHIPS (

    -- maintenance_records → street_lights
    maintenance_to_lights AS
      maintenance_records (light_id) REFERENCES street_lights (id),

    -- energy_consumption → street_lights
    energy_to_lights AS
      energy_consumption (light_id) REFERENCES street_lights (id),

    -- light_sensors → street_lights
    sensors_to_lights AS
      light_sensors (light_id) REFERENCES street_lights (id),

    -- street_lights → demographics (neighborhood name join)
    lights_to_demographics AS
      street_lights (neighborhood) REFERENCES demographics (neighborhood),

    -- energy_consumption → weather (date join for weather enrichment)
    energy_to_weather AS
      energy_consumption (date) REFERENCES weather (date)

  )

  FACTS (

    -- street_lights: numeric and spatial measures
    street_lights.light_id        AS "id"
      COMMENT = 'Street light identifier. Use for counting lights.',

    street_lights.wattage         AS "wattage"
      WITH SYNONYMS ('energy_usage', 'power', 'power_consumption', 'watts')
      COMMENT = 'Power consumption in watts.',

    street_lights.location        AS ST_MAKEPOINT("longitude", "latitude")
      WITH SYNONYMS ('coordinates', 'geo_location', 'geo_point', 'position')
      COMMENT = 'Geographic point reconstructed from lat/lng for spatial queries.',

    -- maintenance_records: cost measures
    maintenance_records.record_id AS "id"
      COMMENT = 'Maintenance record identifier. Use for counting maintenance events.',

    maintenance_records.cost      AS "cost"
      WITH SYNONYMS ('maintenance_cost', 'repair_cost', 'service_cost')
      COMMENT = 'Cost of the maintenance event in local currency.',

    -- energy_consumption: electrical measures
    energy_consumption.reading_id AS "id"
      COMMENT = 'Energy reading identifier. Use for counting readings.',

    energy_consumption.kwh        AS "kwh"
      WITH SYNONYMS ('energy', 'energy_consumed', 'kilowatt_hours', 'power_used')
      COMMENT = 'Energy consumed in kilowatt-hours for the hour.',

    energy_consumption.voltage    AS "voltage"
      WITH SYNONYMS ('supply_voltage', 'v', 'volts')
      COMMENT = 'Voltage reading in volts.',

    energy_consumption.power_factor AS "power_factor"
      WITH SYNONYMS ('efficiency', 'pf')
      COMMENT = 'Power factor (0–1). Values below 0.9 indicate inefficiency.',

    -- light_sensors: sensor measurements
    light_sensors.sensor_id       AS "id"
      COMMENT = 'Sensor reading identifier. Use for counting sensor events.',

    light_sensors.lux             AS "lux"
      WITH SYNONYMS ('ambient_light', 'brightness', 'illuminance', 'light_level')
      COMMENT = 'Ambient light level in lux. High values indicate daylight.',

    light_sensors.sensor_temperature AS "temperature"
      WITH SYNONYMS ('ambient_temp', 'sensor_temp')
      COMMENT = 'Ambient temperature reading from the sensor in Celsius.',

    -- demographics: area metrics
    demographics.population       AS "population"
      WITH SYNONYMS ('inhabitants', 'people', 'residents')
      COMMENT = 'Neighborhood population.',

    demographics.median_income    AS "median_income"
      WITH SYNONYMS ('avg_income', 'income', 'income_level')
      COMMENT = 'Median household income in the neighborhood.',

    demographics.commercial_pct   AS "commercial_pct"
      WITH SYNONYMS ('commercial_share', 'commercial_zone_pct')
      COMMENT = 'Percentage of area classified as commercial.',

    -- power_grid_zones: capacity and load
    power_grid_zones.capacity_kw  AS "capacity_kw"
      WITH SYNONYMS ('grid_capacity', 'max_capacity', 'total_capacity')
      COMMENT = 'Total grid capacity in kilowatts.',

    power_grid_zones.current_load_kw AS "current_load_kw"
      WITH SYNONYMS ('current_demand', 'grid_load', 'load_kw')
      COMMENT = 'Current grid load in kilowatts.',

    power_grid_zones.zone_location AS ST_MAKEPOINT("longitude", "latitude")
      WITH SYNONYMS ('grid_location', 'substation_location', 'zone_coordinates')
      COMMENT = 'Geographic point of the grid zone substation.',

    -- weather: meteorological measures
    weather.temperature           AS "temperature"
      WITH SYNONYMS ('air_temp', 'daily_temp', 'outdoor_temp')
      COMMENT = 'Daily temperature in Celsius.',

    weather.humidity              AS "humidity"
      WITH SYNONYMS ('moisture', 'relative_humidity', 'rh')
      COMMENT = 'Relative humidity percentage.',

    weather.wind_speed            AS "wind_speed"
      WITH SYNONYMS ('wind', 'wind_velocity')
      COMMENT = 'Wind speed in km/h.',

    weather.precipitation         AS "precipitation"
      WITH SYNONYMS ('rainfall', 'rain_mm')
      COMMENT = 'Daily precipitation in millimeters.'

  )

  DIMENSIONS (

    -- street_lights: categorical and time attributes
    street_lights.status          AS "status"
      WITH SYNONYMS ('condition', 'light_status', 'operational_status', 'state')
      COMMENT = 'Operational status: operational, faulty, or maintenance_required.',

    street_lights.light_type      AS "light_type"
      WITH SYNONYMS ('bulb_type', 'fixture_type', 'lamp_type', 'technology')
      COMMENT = 'Lighting technology: LED, Sodium Vapor, etc.',

    street_lights.neighborhood    AS "neighborhood"
      WITH SYNONYMS ('area', 'district', 'locality', 'zone')
      COMMENT = 'Neighborhood where the street light is located.',

    street_lights.install_date    AS "install_date"
      WITH SYNONYMS ('commissioned_date', 'installation_date', 'setup_date')
      COMMENT = 'Date when the street light was installed.',

    -- maintenance_records: event attributes
    maintenance_records.maintenance_date AS "date"
      WITH SYNONYMS ('repair_date', 'service_date', 'work_date')
      COMMENT = 'Date the maintenance was performed.',

    maintenance_records.maintenance_type AS "type"
      WITH SYNONYMS ('repair_type', 'service_type', 'work_type')
      COMMENT = 'Type of maintenance performed.',

    maintenance_records.technician AS "technician"
      WITH SYNONYMS ('engineer', 'repair_person', 'service_tech', 'worker')
      COMMENT = 'Name or ID of the technician who performed the work.',

    -- energy_consumption: time and hour breakdown
    energy_consumption.reading_date AS "date"
      WITH SYNONYMS ('consumption_date', 'energy_date')
      COMMENT = 'Date of the energy reading.',

    energy_consumption.hour       AS "hour"
      WITH SYNONYMS ('hour_of_day', 'time_of_day', 'time_slot')
      COMMENT = 'Hour of the day (0–23) for the reading.',

    -- light_sensors: time attributes
    light_sensors.reading_timestamp AS "timestamp"
      WITH SYNONYMS ('reading_time', 'sensor_time')
      COMMENT = 'Timestamp of the sensor reading.',

    light_sensors.motion_detected AS "motion_detected"
      WITH SYNONYMS ('activity', 'motion', 'pedestrian_activity')
      COMMENT = 'Whether motion was detected at the time of the reading.',

    -- power_grid_zones: zone identifiers
    power_grid_zones.zone_name    AS "zone_name"
      WITH SYNONYMS ('grid_area', 'grid_name', 'power_zone', 'supply_zone')
      COMMENT = 'Human-readable name for the power grid zone.',

    -- weather: time and seasonal dimensions
    weather.weather_date          AS "date"
      WITH SYNONYMS ('forecast_date', 'measurement_date', 'observation_date')
      COMMENT = 'Date of the weather observation.',

    weather.season                AS "season"
      WITH SYNONYMS ('quarter_season', 'seasonal_period', 'time_of_year')
      COMMENT = 'Season: spring, summer, fall, or winter.'

  )

  METRICS (

    -- Street light counts and health
    street_lights.total_lights AS COUNT(street_lights.light_id)
      WITH SYNONYMS ('light_count', 'number_of_lights', 'total_lamps')
      COMMENT = 'Total number of street lights.',

    street_lights.faulty_lights AS COUNT_IF(street_lights.status = 'faulty')
      WITH SYNONYMS ('broken_lights', 'defective_lights', 'fault_count', 'non_operational')
      COMMENT = 'Count of street lights with faulty status.',

    street_lights.maintenance_required AS COUNT_IF(street_lights.status = 'maintenance_required')
      WITH SYNONYMS ('lights_needing_service', 'pending_maintenance')
      COMMENT = 'Count of street lights requiring maintenance.',

    street_lights.operational_lights AS COUNT_IF(street_lights.status = 'operational')
      WITH SYNONYMS ('active_lights', 'working_lights')
      COMMENT = 'Count of operational street lights.',

    street_lights.avg_wattage AS AVG(street_lights.wattage)
      WITH SYNONYMS ('average_power', 'mean_wattage')
      COMMENT = 'Average power consumption in watts across all street lights.',

    -- Maintenance metrics
    maintenance_records.total_maintenance AS COUNT(maintenance_records.record_id)
      WITH SYNONYMS ('maintenance_count', 'repair_count', 'service_events')
      COMMENT = 'Total number of maintenance events.',

    maintenance_records.total_maintenance_cost AS SUM(maintenance_records.cost)
      WITH SYNONYMS ('total_repair_cost', 'total_spend')
      COMMENT = 'Total cost of all maintenance events.',

    maintenance_records.avg_maintenance_cost AS AVG(maintenance_records.cost)
      WITH SYNONYMS ('average_cost', 'average_repair_cost', 'mean_cost')
      COMMENT = 'Average cost per maintenance event.',

    -- Energy metrics
    energy_consumption.total_kwh AS SUM(energy_consumption.kwh)
      WITH SYNONYMS ('total_energy', 'total_energy_consumed', 'total_power_used')
      COMMENT = 'Total energy consumed in kilowatt-hours.',

    energy_consumption.avg_kwh AS AVG(energy_consumption.kwh)
      WITH SYNONYMS ('average_energy', 'average_kwh', 'mean_energy')
      COMMENT = 'Average hourly energy consumption per reading.',

    energy_consumption.avg_power_factor AS AVG(energy_consumption.power_factor)
      WITH SYNONYMS ('average_efficiency', 'average_pf', 'mean_power_factor')
      COMMENT = 'Average power factor — values below 0.9 indicate inefficiency.',

    -- Sensor metrics
    light_sensors.avg_lux AS AVG(light_sensors.lux)
      WITH SYNONYMS ('average_brightness', 'average_light_level', 'mean_lux')
      COMMENT = 'Average ambient light level in lux.',

    -- Weather metrics
    weather.avg_temperature AS AVG(weather.temperature)
      WITH SYNONYMS ('average_temp', 'mean_temperature')
      COMMENT = 'Average daily temperature in Celsius.',

    weather.avg_precipitation AS AVG(weather.precipitation)
      WITH SYNONYMS ('average_rainfall', 'mean_precipitation')
      COMMENT = 'Average daily precipitation in millimeters.'

  )

  COMMENT = 'Semantic view for streetlight infrastructure intelligence — enables natural language queries via Cortex Analyst and Intelligence Agent.'
;
