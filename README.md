# TSMS Tutorial – Step 1: TICK Stack + Kafka + InfluxDB

This repository focuses on **Step 1** of the TSMS tutorial with a practical TICK stack setup:

- generate synthetic time-series data with **TimeSynth**;
- publish records to **Kafka**;
- ingest data through **Telegraf**;
- store/query data in **InfluxDB 2.x**;
- visualize via **Chronograf**;
- include **Kapacitor** service for alerting/task pipeline experiments.

At this stage, **TimeScaleDB and ClickHouse are intentionally removed** from the workflow.

---

## Architecture

`TimeSynth (Python) -> Kafka topic -> Telegraf (kafka_consumer) -> InfluxDB`

TICK-related services included in Docker Compose:

- Telegraf
- InfluxDB
- Chronograf
- Kapacitor

Supporting services:

- Kafka
- Zookeeper

---

## 1) Start the stack

```bash
docker compose up -d
```

Useful endpoints:

- InfluxDB: `http://localhost:8086`
- Chronograf UI: `http://localhost:8888`
- Kapacitor API (host mapped): `http://localhost:9093`
- Kafka bootstrap (host): `localhost:29092`

---

## 2) Python setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

---

## 3) Ingestion: publish synthetic data to Kafka

```bash
PYTHONPATH=src python -m tsms_tutorial.main ingest --points 2000 --seed 42
```

Telegraf consumes topic `tsms-metrics` and writes metrics into InfluxDB bucket `tutorial`.

---

## 4) Run sample queries on InfluxDB

### Latest points

```bash
PYTHONPATH=src python -m tsms_tutorial.main query --example latest --limit 10
```

### Mean by window

```bash
PYTHONPATH=src python -m tsms_tutorial.main query --example mean-window --window 15m --limit 10
```

### Injected anomalies only

```bash
PYTHONPATH=src python -m tsms_tutorial.main query --example anomalies --limit 20
```

---

## 5) Example Flux queries for demos

### Latest values

```flux
from(bucket: "tutorial")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "metrics" and r._field == "value")
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 10)
```

### 15-minute moving mean

```flux
from(bucket: "tutorial")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "metrics" and r._field == "value")
  |> aggregateWindow(every: 15m, fn: mean, createEmpty: false)
```

### Injected anomalies

```flux
from(bucket: "tutorial")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "metrics" and r._field == "is_injected_anomaly")
  |> filter(fn: (r) => r._value == true)
  |> sort(columns: ["_time"], desc: true)
```

---

## 6) Chronograf and Kapacitor in this step

- Chronograf is included as UI service to inspect and organize dashboards.
- Kapacitor is included and reachable from Chronograf (`http://kapacitor:9092` inside the Docker network).
- A baseline Kapacitor config is provided in `kapacitor/kapacitor.conf` for step-by-step extension in the next tutorial stage.

---

## Project structure

- `src/tsms_tutorial/generator.py`: synthetic time-series generator (TimeSynth).
- `src/tsms_tutorial/clients.py`: Kafka publisher + InfluxDB query repository.
- `src/tsms_tutorial/main.py`: CLI for `ingest` and `query`.
- `telegraf/telegraf.conf`: Kafka input and InfluxDB output for Telegraf.
- `kapacitor/kapacitor.conf`: baseline Kapacitor configuration.

---

## 7) Running on remote servers with Apptainer

If your remote server uses **Apptainer** instead of Docker, the **Python code does not need to change**.
Only the container orchestration layer changes.

### What changes vs Docker Compose

- Keep Python code and CLI commands unchanged (`ingest`, `query`).
- Replace `docker compose up -d` with Apptainer workflows (one service per container/instance).
- Keep the same exposed endpoints used by `.env`:
  - InfluxDB: `http://localhost:8086`
  - Kafka bootstrap from host: `localhost:29092`

### Practical Apptainer approach

1. Pull OCI images as SIF files (InfluxDB, Telegraf, Kafka, Zookeeper, Chronograf, Kapacitor).
2. Start each service as an Apptainer instance (or via your scheduler/HPC wrapper).
3. Bind configuration files:
   - `telegraf/telegraf.conf` -> `/etc/telegraf/telegraf.conf`
   - `kapacitor/kapacitor.conf` -> `/etc/kapacitor/kapacitor.conf`
4. Bind persistent directories for InfluxDB/Kapacitor data.
5. Ensure network reachability among services (same host network or explicit port mapping strategy).

> Note: in HPC environments, Kafka + Zookeeper may be managed externally. In that case,
> set `KAFKA_BOOTSTRAP_SERVERS` in `.env` to your managed broker address and keep Telegraf
> pointed to that broker.

### Conclusion

- **Application logic:** unchanged.
- **Deployment/runtime:** switch from Compose to Apptainer instances.
