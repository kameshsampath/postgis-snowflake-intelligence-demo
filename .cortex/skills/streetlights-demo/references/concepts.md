# Key Concepts

## pg_lake

PostgreSQL extension that enables tables to be stored in Apache Iceberg format instead
of traditional heap storage. When you `CREATE TABLE ... USING iceberg`, the data is
written as Parquet files with Iceberg metadata, making it directly readable by any
system that understands the Iceberg table format.

**Key property**: The PostgreSQL wire protocol (SQL, psql, ORMs) works as normal — the
storage engine is the only difference.

## Managed Storage

A Snowflake Postgres instance can use either:
- **Managed storage** — Snowflake manages the underlying object store (required for CLD)
- **Customer storage** — You provide your own S3/GCS/Azure bucket

This demo **requires managed storage** because CLD only works when Snowflake controls
the storage layer.

## CLD (Catalog-Linked Database)

A Snowflake database that reads Iceberg table metadata from a catalog source — in this
case, a Snowflake Postgres instance. CLD does NOT copy data. It reads the same Iceberg
files that PostgreSQL wrote.

**Key property**: Zero-latency sync. When PostgreSQL writes data, Snowflake sees it
via the shared Iceberg metadata (subject to ~30s propagation delay for metadata refresh).

## Catalog Integration

A Snowflake object that defines how to connect to an external catalog. For pg_lake:
```sql
CREATE CATALOG INTEGRATION my_catalog
  CATALOG_SOURCE = SNOWFLAKE_POSTGRES
  POSTGRES_INSTANCE_NAME = 'my_instance'
  ENABLED = TRUE;
```

## Semantic View

A SQL-native semantic layer in Snowflake. Replaces YAML-based semantic models (Cortex
Analyst) with a DDL object:
```sql
CREATE SEMANTIC VIEW my_view
  TABLES (...)
  DIMENSIONS (...)
  MEASURES (...)
  FILTERS (...);
```

Semantic Views enable natural language querying via Intelligence Agents and Cortex
Analyst without requiring YAML file management.

## Cortex Search

A managed full-text + semantic search service in Snowflake. Indexes a text column and
enables natural language retrieval with relevance ranking. Unlike PostgreSQL's ILIKE or
full-text search, Cortex Search understands semantic meaning (e.g., "safety hazard"
matches "exposed wire" and "sparking").

## Intelligence Agent

A Snowflake object that combines multiple data sources (Semantic Views, Cortex Search
services) into a single natural language interface. Users ask questions in plain
English; the agent routes to the appropriate source and returns formatted answers.

```sql
CREATE AGENT my_agent
  DATA_SOURCES = (semantic_view, cortex_search_service)
  ...;
```

## FORECAST (ML)

Snowflake's built-in time-series forecasting. Trains on historical data and predicts
future values with confidence intervals:
```sql
CREATE SNOWFLAKE.ML.FORECAST my_model(
  INPUT_DATA => ...,
  TIMESTAMP_COLNAME => 'ts',
  TARGET_COLNAME => 'value'
);
```

No external ML infrastructure needed — runs entirely within Snowflake.
