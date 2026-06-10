# PostGIS vs Snowflake Postgres (pg_lake)

| Aspect | Traditional PostGIS | This Demo (pg_lake) |
|--------|-------------------|---------------------|
| Storage | Heap tables | Iceberg tables |
| Spatial columns | GEOMETRY/GEOGRAPHY types | lat/lng FLOAT columns |
| Spatial queries | ST_Within, ST_DWithin, KNN (<->) | ST_MAKEPOINT(lng, lat) on read |
| Indexes | GIST spatial indexes | B-tree on lat/lng |
| Sync to warehouse | CDC (Debezium/OpenFlow) | Native CLD (zero-pipeline) |
| Analytics layer | External tools (Metabase, etc.) | Semantic View + Agent |
| Text search | ILIKE / pg_trgm / full-text | Cortex Search (semantic) |
| ML/Forecasting | External (Python, R) | FORECAST built-in |
| Setup complexity | Docker + PostGIS extension + CDC config | Single `CREATE POSTGRES INSTANCE` |
| Data model | Normalized + views | Iceberg tables + CLD views |

## Why pg_lake?

Traditional PostGIS workflows require:
1. Running a PostgreSQL server with PostGIS extension
2. Setting up CDC (WAL, publications, Debezium/OpenFlow connectors)
3. Managing schema sync between PG and Snowflake
4. Handling WKB/WKT serialization for spatial data

With pg_lake (Snowflake Postgres):
1. Tables are stored as Iceberg natively
2. CLD reads Iceberg metadata directly — no sync pipeline
3. Spatial data stored as simple floats, reconstructed with ST_MAKEPOINT
4. Full Snowflake AI/ML stack available immediately

## Trade-offs

| | PostGIS | pg_lake |
|--|---------|---------|
| Spatial indexing | GIST (fast for complex geometries) | No spatial index (B-tree on coordinates) |
| Geometry types | Full support (polygon, linestring, etc.) | Point-only via lat/lng floats |
| Real-time queries | Sub-millisecond spatial | Depends on Snowflake warehouse |
| Ecosystem | Mature (QGIS, GeoServer, etc.) | Snowflake-native only |
| Best for | Complex spatial operations | Analytics + AI on location data |
