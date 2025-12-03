# Schema Reference

Complete data dictionary for the Street Lights Maintenance Demo.

> **DISCLAIMER**: All sample data is fictitious and created solely for demonstration purposes. Company names, contact information, and other identifiers do not represent real entities.

---

## Table of Contents

- [Overview](#overview)
- [PostgreSQL Tables](#postgresql-tables)
  - [Base Tables](#base-tables)
  - [Enrichment Tables](#enrichment-tables)
  - [Views](#postgresql-views)
- [Snowflake Objects](#snowflake-objects)
  - [CDC Tables](#cdc-tables)
  - [Analytics Views](#analytics-views)
  - [ML Objects](#ml-objects)
- [Coordinate System](#coordinate-system)
- [Common Query Patterns](#common-query-patterns)

---

## Overview

### Data Flow

```
PostgreSQL (Operational)          Snowflake (Analytics)
─────────────────────────────────────────────────────────
┌──────────────────────┐          ┌──────────────────────┐
│ Base Tables          │   CDC    │ Raw Tables           │
│ • street_lights      │ ──────▶  │ (Real-time sync)     │
│ • neighborhoods      │          │                      │
│ • maintenance_requests│          └──────────┬───────────┘
│ • suppliers          │                      │
└──────────────────────┘                      ▼
         │                        ┌──────────────────────┐
         │                        │ Analytics Views      │
┌──────────────────────┐          │ • ML Training Data   │
│ Enrichment Tables    │   CDC    │ • Forecasts          │
│ • weather_enrichment │ ──────▶  │ • Cortex Search      │
│ • demographics       │          └──────────────────────┘
│ • power_grid         │
└──────────────────────┘
```

### Data Volumes

| Entity | Count | Description |
|--------|-------|-------------|
| Street Lights | 5,000 | Distributed across Bengaluru |
| Neighborhoods | 50 | With polygon boundaries |
| Suppliers | 25 | Equipment service providers |
| Maintenance Requests | 1,500 | Historical records for ML training |
| Weather Enrichment | 15,000 | 3 seasons × 5,000 lights |
| Demographics | 50 | One per neighborhood |
| Power Grid | 5,000 | One per light |

---

## PostgreSQL Tables

All tables are in the `streetlights` schema.

### Base Tables

#### `street_lights`

**Purpose**: Core operational data for all street lights in the city.

| Column | Type | Constraints | Description | Example |
|--------|------|-------------|-------------|---------|
| `light_id` | TEXT | PRIMARY KEY | Unique identifier | `SL-0001` |
| `location` | GEOMETRY(Point, 4326) | NOT NULL | GPS coordinates (WGS84) | `POINT(77.5946 12.9716)` |
| `status` | TEXT | NOT NULL | Operational status | `operational`, `faulty`, `maintenance_required` |
| `wattage` | INTEGER | | Power consumption (watts) | `150` |
| `installation_date` | DATE | | Installation date | `2018-03-15` |
| `last_maintenance` | TIMESTAMP | | Last maintenance time | `2024-01-20 14:30:00` |
| `neighborhood_id` | TEXT | FK → neighborhoods | Reference to neighborhood | `NH-042` |

**Indexes**:

- `idx_lights_location GIST(location)` - Spatial index for proximity queries
- `idx_lights_status` - Filter by status
- `idx_lights_neighborhood` - Join optimization

**Status Values**:

| Status | Description | Typical % |
|--------|-------------|-----------|
| `operational` | Working normally | 85% |
| `maintenance_required` | Needs scheduled service | 10% |
| `faulty` | Not functioning | 5% |

---

#### `neighborhoods`

**Purpose**: Geographic boundaries and metadata for city neighborhoods.

| Column | Type | Constraints | Description | Example |
|--------|------|-------------|-------------|---------|
| `neighborhood_id` | TEXT | PRIMARY KEY | Unique identifier | `NH-001` |
| `name` | TEXT | NOT NULL | Neighborhood name | `Koramangala` |
| `boundary` | GEOMETRY(Polygon, 4326) | NOT NULL | Geographic boundary | `POLYGON((77.60 12.93, ...))` |
| `population` | INTEGER | | Estimated population | `125000` |

**Indexes**:

- `idx_neighborhoods_boundary GIST(boundary)` - Point-in-polygon queries

---

#### `maintenance_requests`

**Purpose**: Historical and active maintenance work orders.

| Column | Type | Constraints | Description | Example |
|--------|------|-------------|-------------|---------|
| `request_id` | TEXT | PRIMARY KEY | Unique identifier | `MR-0001` |
| `light_id` | TEXT | FK → street_lights | Light requiring service | `SL-1234` |
| `reported_at` | TIMESTAMP | NOT NULL | Issue report time | `2024-01-15 08:30:00` |
| `resolved_at` | TIMESTAMP | | Resolution time (NULL if open) | `2024-01-18 14:20:00` |
| `issue_type` | TEXT | | Type of issue | See below |

**Issue Types**:

| Type | Description |
|------|-------------|
| `bulb_failure` | Bulb burned out or broken |
| `wiring` | Electrical wiring issues |
| `pole_damage` | Physical damage to pole |
| `sensor_malfunction` | Light sensor not working |
| `flickering` | Intermittent operation |

---

#### `suppliers`

**Purpose**: Equipment suppliers with service coverage areas.

| Column | Type | Constraints | Description | Example |
|--------|------|-------------|-------------|---------|
| `supplier_id` | TEXT | PRIMARY KEY | Unique identifier | `SUP-001` |
| `name` | TEXT | NOT NULL | Company name (fictitious) | `Acme Lights & Co.` |
| `location` | GEOMETRY(Point, 4326) | NOT NULL | Office location | `POINT(77.5800 12.9600)` |
| `contact_phone` | TEXT | | Phone number | `+91-80-12345678` |
| `service_radius_km` | INTEGER | | Coverage radius (km) | `10` |
| `avg_response_hours` | INTEGER | | Average response time | `4` |
| `specialization` | TEXT | | Equipment type | `LED`, `Sodium Vapor`, `All` |

**Indexes**:

- `idx_suppliers_location GIST(location)` - Nearest supplier queries

---

### Enrichment Tables

#### `weather_enrichment`

**Purpose**: Seasonal weather patterns affecting light failure rates.

| Column | Type | Constraints | Description | Example |
|--------|------|-------------|-------------|---------|
| `light_id` | TEXT | FK → street_lights | Reference to light | `SL-0001` |
| `season` | TEXT | NOT NULL | Season identifier | `monsoon`, `summer`, `winter` |
| `avg_temperature_c` | NUMERIC(5,2) | | Average temperature | `32.50` |
| `rainfall_mm` | NUMERIC(6,2) | | Average rainfall | `185.75` |
| `failure_risk_score` | NUMERIC(3,2) | CHECK (0.0-1.0) | ML failure probability | `0.75` |
| `predicted_failure_date` | DATE | | Predicted failure date | `2024-06-15` |

**Season Definitions**:

| Season | Months | Risk Level | Typical Score |
|--------|--------|------------|---------------|
| Monsoon | June-September | High | 0.7-0.9 |
| Summer | March-May | Medium | 0.5-0.7 |
| Winter | December-February | Low | 0.2-0.4 |

---

#### `demographics_enrichment`

**Purpose**: Neighborhood characteristics for infrastructure planning.

| Column | Type | Constraints | Description | Example |
|--------|------|-------------|-------------|---------|
| `neighborhood_id` | TEXT | FK → neighborhoods | Reference | `NH-001` |
| `population_density` | INTEGER | | People per sq km | `12500` |
| `urban_classification` | TEXT | | Development level | `urban`, `suburban`, `rural` |

---

#### `power_grid_enrichment`

**Purpose**: Electrical grid data for each light.

| Column | Type | Constraints | Description | Example |
|--------|------|-------------|-------------|---------|
| `light_id` | TEXT | FK → street_lights | Reference to light | `SL-0001` |
| `grid_zone` | TEXT | | Power grid zone | `ZONE-A`, `ZONE-B` |
| `avg_load_percent` | NUMERIC(5,2) | | Average grid load | `78.50` |
| `outage_history_count` | INTEGER | | Historical outages | `3` |

---

### PostgreSQL Views

#### `street_lights_enriched`

**Purpose**: Combined view of lights with all enrichment data. Primary view for CDC to Snowflake.

**Key Columns**:

- All columns from `street_lights`
- `neighborhood_name`, `population` from `neighborhoods`
- `season`, `failure_risk_score`, `predicted_failure_date` from `weather_enrichment`
- `population_density`, `urban_classification` from `demographics_enrichment`
- `grid_zone`, `avg_load_percent`, `outage_history_count` from `power_grid_enrichment`
- `age_months` - Calculated light age
- `maintenance_urgency` - CRITICAL/HIGH/MEDIUM/LOW based on predicted failure

---

#### `maintenance_requests_enriched`

**Purpose**: Maintenance requests with spatial and enrichment context.

**Key Columns**:

- All columns from `maintenance_requests`
- `longitude`, `latitude` - Extracted coordinates
- `neighborhood_name` from `neighborhoods`
- `season`, `failure_risk_score` from `weather_enrichment`
- `resolution_hours` - Calculated time to resolve
- `status` - OPEN/CLOSED based on `resolved_at`

---

## Snowflake Objects

After CDC sync, data is available in Snowflake for analytics.

### CDC Tables

Tables synced from PostgreSQL (in lowercase schema `"streetlights"`):

| Snowflake Table | Source PostgreSQL Table |
|-----------------|------------------------|
| `"streetlights"."street_lights"` | `streetlights.street_lights` |
| `"streetlights"."neighborhoods"` | `streetlights.neighborhoods` |
| `"streetlights"."maintenance_requests"` | `streetlights.maintenance_requests` |
| `"streetlights"."suppliers"` | `streetlights.suppliers` |
| `"streetlights"."weather_enrichment"` | `streetlights.weather_enrichment` |
| `"streetlights"."demographics_enrichment"` | `streetlights.demographics_enrichment` |
| `"streetlights"."power_grid_enrichment"` | `streetlights.power_grid_enrichment` |

> **Note**: Use double quotes for lowercase schema/table names in Snowflake SQL.

---

### Analytics Views

Located in `ANALYTICS` schema:

#### `MAINTENANCE_SEARCHABLE`

**Purpose**: Cortex Search source with synthesized descriptions.

| Column | Description |
|--------|-------------|
| `REQUEST_ID` | Maintenance request ID |
| `LIGHT_ID` | Street light ID |
| `SEARCH_DESCRIPTION` | Natural language description for semantic search |
| `ISSUE_TYPE` | Type of maintenance issue |
| `NEIGHBORHOOD_NAME` | Location context |
| `REQUEST_STATUS` | OPEN or CLOSED |

---

#### `ML_BULB_FAILURE_TIMESERIES`

**Purpose**: Time-series training data for ML forecasting.

| Column | Description |
|--------|-------------|
| `FAILURE_DATE` | Date of failure event |
| `FAILURE_COUNT` | Number of failures that day |
| `SEASON` | Season (monsoon/summer/winter) |

---

#### `BULB_FAILURE_FORECAST_30D` / `BULB_FAILURE_FORECAST_90D`

**Purpose**: ML forecast results.

| Column | Description |
|--------|-------------|
| `FORECAST_DATE` | Predicted date |
| `PREDICTED_FAILURES` | Expected failure count |
| `LOWER_BOUND` | 95% confidence lower bound |
| `UPPER_BOUND` | 95% confidence upper bound |
| `SEASON` | Season for the date |

---

#### `BULB_REPLACEMENT_SCHEDULE`

**Purpose**: Operational planning view with staffing recommendations.

| Column | Description |
|--------|-------------|
| `FORECAST_DATE` | Date |
| `PREDICTED_FAILURES` | Expected failures |
| `PRIORITY` | HIGH/MEDIUM/LOW |
| `STAFFING_RECOMMENDATION` | Crew size needed |
| `BULBS_TO_STOCK` | Inventory recommendation |

---

### ML Objects

| Object | Type | Purpose |
|--------|------|---------|
| `BULB_FAILURE_FORECASTER` | SNOWFLAKE.ML.FORECAST | Time-series forecasting model |

**Model Methods**:

- `FORECAST(30)` / `FORECAST(90)` - Generate predictions
- `SHOW_EVALUATION_METRICS()` - View model performance

---

## Coordinate System

**SRID**: 4326 (WGS84 - World Geodetic System 1984)

- Standard GPS coordinate system
- Latitude/Longitude format
- Compatible with web mapping (Google Maps, Leaflet, Folium)

**Bengaluru Bounds**:

- Latitude: 12.8°N to 13.1°N
- Longitude: 77.5°E to 77.7°E

**WKT Format**: [Well-Known Text](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) representation

- Point: `POINT(77.5946 12.9716)` = (longitude, latitude)
- Polygon: `POLYGON((lon1 lat1, lon2 lat2, ...))`

**Geography vs Geometry**:

```sql
-- Geometry: Fast, approximate (degrees)
SELECT ST_Distance(a.location, b.location) FROM ...

-- Geography: Accurate meters (cast with ::geography)
SELECT ST_Distance(a.location::geography, b.location::geography) FROM ...
```

---

## Common Query Patterns

### PostgreSQL Queries

**Find lights in a neighborhood**:

```sql
SELECT l.* FROM streetlights.street_lights l
JOIN streetlights.neighborhoods n ON ST_Within(l.location, n.boundary)
WHERE n.name = 'Koramangala';
```

**Find nearest supplier to a faulty light**:

```sql
SELECT s.name, s.avg_response_hours,
       ST_Distance(s.location::geography, l.location::geography)/1000 AS distance_km
FROM streetlights.suppliers s
CROSS JOIN streetlights.street_lights l
WHERE l.light_id = 'SL-0001'
ORDER BY s.location <-> l.location
LIMIT 3;
```

**Find lights predicted to fail within 30 days**:

```sql
SELECT * FROM streetlights.street_lights_enriched
WHERE predicted_failure_date <= CURRENT_DATE + INTERVAL '30 days'
  AND predicted_failure_date IS NOT NULL
ORDER BY predicted_failure_date;
```

### Snowflake Queries

**Semantic search for maintenance issues**:

```sql
SELECT * FROM TABLE(
  ANALYTICS.MAINTENANCE_SEARCH!SEARCH(
    query => 'flickering light electrical problem',
    columns => ['SEARCH_DESCRIPTION'],
    limit => 10
  )
);
```

**Weekly forecast with budget**:

```sql
SELECT
    DATE_TRUNC('week', FORECAST_DATE)::DATE AS WEEK_START,
    SUM(PREDICTED_FAILURES) AS TOTAL_FAILURES,
    SUM(PREDICTED_FAILURES) * 1650 AS TOTAL_BUDGET_INR
FROM ANALYTICS.BULB_REPLACEMENT_SCHEDULE
GROUP BY DATE_TRUNC('week', FORECAST_DATE)
ORDER BY WEEK_START;
```

**Seasonal risk analysis**:

```sql
SELECT SEASON, 
       SUM(PREDICTED_FAILURES) AS total_failures,
       ROUND(AVG(PREDICTED_FAILURES), 1) AS avg_daily
FROM ANALYTICS.BULB_FAILURE_FORECAST_30D
GROUP BY SEASON
ORDER BY total_failures DESC;
```

---

## Related Documentation

- [QUICKSTART.md](QUICKSTART.md) - Setup guide
- [DEMO_SCRIPT.md](DEMO_SCRIPT.md) - Demo walkthrough
- [snowflake/SNOWFLAKE_INTELLIGENCE_QUESTIONS.md](snowflake/SNOWFLAKE_INTELLIGENCE_QUESTIONS.md) - Sample Cortex queries
