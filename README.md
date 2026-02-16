# TSMS Tutorial (InfluxDB vs TimeScaleDB vs ClickHouse) with TimeSynth

This project provides a practical foundation for a **Time Series Management Systems (TSMS)** tutorial using:

- **InfluxDB 2.x**
- **TimeScaleDB (PostgreSQL extension)**
- **ClickHouse**

Data is generated with **TimeSynth** and then used for:

1. Ingestion into all three databases.
2. Retrieval queries.
3. Forecasting.
4. Anomaly detection.

## 1) Start local (free) databases

```bash
docker compose up -d
```

Available services:

- InfluxDB: `http://localhost:8086`
- TimeScaleDB: `localhost:5432`
- ClickHouse HTTP: `localhost:8123`

## 2) Python setup (also for remote servers)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Use with PyCharm + remote interpreter

- Open the remote repository in PyCharm.
- Configure a remote interpreter using the `.venv` created on the server.
- Run the CLI commands from the remote integrated terminal.

## 3) Run the tutorial workflow

### 3.1 Generate + ingest into all databases

```bash
PYTHONPATH=src python -m tsms_tutorial.main ingest --points 2000
```

### 3.2 Query the latest records

```bash
PYTHONPATH=src python -m tsms_tutorial.main query --limit 10
```

### 3.3 Forecasting + anomaly detection

```bash
PYTHONPATH=src python -m tsms_tutorial.main analyze --limit 1000 --horizon 30
```

## 4) Comparison queries (for the tutorial)

### InfluxDB (Flux)

```flux
from(bucket: "tutorial")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "metrics" and r._field == "value")
  |> aggregateWindow(every: 15m, fn: mean, createEmpty: false)
```

### TimeScaleDB (SQL)

```sql
SELECT time_bucket('15 minutes', time) AS bucket,
       AVG(value) AS avg_value
FROM metrics
GROUP BY bucket
ORDER BY bucket;
```

### ClickHouse (SQL)

```sql
SELECT toStartOfInterval(time, INTERVAL 15 MINUTE) AS bucket,
       avg(value) AS avg_value
FROM metrics
GROUP BY bucket
ORDER BY bucket;
```

## 5) Project structure

- `src/tsms_tutorial/generator.py`: synthetic series generation with injected anomalies.
- `src/tsms_tutorial/clients.py`: connectors and base operations for all three DBs.
- `src/tsms_tutorial/analytics.py`: forecasting and anomaly detection.
- `src/tsms_tutorial/main.py`: tutorial CLI.

## 6) Practical notes for remote servers

- If DBs run on the same remote server, keep `localhost` in `.env`.
- If DBs run on separate hosts, update host/port values in `.env`.
- For live demos, prepare 2–3 datasets with different seeds (`seed` in `generator.py`) to show robustness.
