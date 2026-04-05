# Gravitino Semantic Layer Quickstart

This project demonstrates a working semantic layer using [MetricFlow](https://github.com/dbt-labs/metricflow) and [dbt](https://www.getdbt.com/), with NYC yellow cab trip data as the test dataset. It is part of the broader [Apache Gravitino](https://gravitino.apache.org/) ADP (Agentic Data Protocol) demonstration environment.

The goal is to show that a semantic model defined in YAML can be compiled to valid, executable SQL — without hardcoding SQL logic anywhere. This is the foundation for serving governed metrics to LLMs via MCP.

## What This Demonstrates

```
OSI YAML → MetricFlow (compiler) → SQL → Trino (federated execution)
```

A semantic model declaratively defines metrics, dimensions, and relationships. MetricFlow compiles those definitions into optimized SQL at query time. The generated SQL is clean ANSI SQL compatible with Trino.

## Prerequisites

- Python 3.12+
- NYC yellow cab Parquet files available locally (2024 dataset used in examples)
- Git

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/markhoerth/gravitino-semantic-layer-quickstart.git
cd gravitino-semantic-layer-quickstart
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

You will need to run `source venv/bin/activate` each time you open a new terminal session.

### 3. Install dependencies

```bash
pip install dbt-core dbt-duckdb dbt-metricflow
```

### 4. Configure your Parquet data path

Edit `gravitino_semantic_layer/models/staging/stg_taxi_trips.sql` and update the path to point at your local NYC taxi Parquet files:

```sql
from read_parquet('/your/path/to/nyc_taxi_2024/*.parquet')
```

DuckDB reads the entire directory of Parquet files in one shot using the glob pattern.

### 5. Set the dbt profiles directory

MetricFlow requires this environment variable to locate your dbt profile:

```bash
export DBT_PROFILES_DIR=~/.dbt
```

You may want to add this to your shell profile (`.bashrc` or `.zshrc`) so it persists across sessions.

### 6. Build the dbt models

```bash
cd gravitino_semantic_layer
dbt run
```

This creates two objects in DuckDB:
- `stg_taxi_trips` — a view over your local Parquet files
- `metricflow_time_spine` — a date table required by MetricFlow for time-based aggregations

### 7. Validate the semantic model

```bash
mf validate-configs
```

All checks should pass with zero errors.

## Querying Metrics

MetricFlow compiles your YAML semantic model to SQL at query time. Use the `--explain` flag to see the generated SQL without executing it.

### Total trips by day

```bash
mf query --metrics total_trips --group-by metric_time__day --explain
```

### Average fare by vendor

```bash
mf query --metrics average_fare --group-by trip__vendor_id --explain
```

### List all available metrics

```bash
mf list metrics
```

### List all available dimensions

```bash
mf list dimensions --metrics total_trips
```

## Project Structure

```
gravitino_semantic_layer/
├── dbt_project.yml                          # dbt project config
├── models/
│   ├── staging/
│   │   ├── stg_taxi_trips.sql               # Source model over local Parquet files
│   │   ├── metricflow_time_spine.sql        # Required date spine for MetricFlow
│   │   └── metricflow_time_spine.yml        # Time spine YAML config
│   └── semantic_models/
│       └── taxi_trips.yml                   # Semantic model: metrics, measures, dimensions
```

## Semantic Model

The semantic model is defined in `models/semantic_models/taxi_trips.yml`. It currently defines:

**Measures**
- `trip_count` — count of trips (using `fare_amount` as the non-null expression)
- `avg_fare` — average fare amount

**Metrics**
- `total_trips` — total number of taxi trips
- `average_fare` — average fare per trip

**Dimensions**
- `pickup_datetime` — time dimension at day granularity
- `vendor_id` — categorical
- `payment_type` — categorical

## Relationship to Apache Gravitino

This quickstart is a standalone POC. The longer-term vision is:

1. Gravitino provides a UI for authoring semantic models against catalog objects, generating OSI-compliant YAML
2. MetricFlow compiles the YAML to SQL
3. Trino executes the SQL federally across data sources
4. LLMs access governed metrics via MCP — resolving natural language questions to trusted SQL rather than raw tables

This addresses the open design question of whether a semantic model is a standalone catalog object or metadata enriching an existing Iceberg view — a contribution Gravitino can bring to the OSI working group.

## Related Projects

- [gravitino-irc-quickstart](https://github.com/markhoerth/gravitino-irc-quickstart) — Gravitino Iceberg REST Catalog quickstart environment
- [Apache Gravitino](https://github.com/apache/gravitino)
- [MetricFlow](https://github.com/dbt-labs/metricflow)
- [Open Semantic Interchange (OSI)](https://github.com/open-semantic-interchange/OSI)
