# TSMS Tutorial – Step 1: TICK Stack + Kafka + InfluxDB (Apptainer-only)

This repository is now **Apptainer-only** (no Docker/Compose) and focuses on Step 1 of the TSMS tutorial:

- generate synthetic time-series data with **TimeSynth**;
- publish records to **Kafka**;
- ingest data through **Telegraf**;
- store/query data in **InfluxDB 2.x**;
- visualize via **Chronograf**;
- include **Kapacitor** for alerting/task pipeline experiments.

At this stage, **TimeScaleDB and ClickHouse are intentionally removed**.

---

## Architecture

`TimeSynth (Python) -> Kafka topic -> Telegraf (kafka_consumer) -> InfluxDB`

Services run as **Apptainer instances**:

- Kafka (KRaft mode, no ZooKeeper)
- InfluxDB
- Telegraf
- Chronograf
- Kapacitor

---

## 1) Prerequisites

- Apptainer installed on the remote server.
- Python 3.10+.
- Network access from the server to pull container images from Docker Hub.

Check Apptainer:

```bash
apptainer --version
```

---

## 2) Start the stack (Apptainer, Kafka KRaft)

From repository root:

```bash
./apptainer/start_stack.sh
```

Check running instances:

```bash
./apptainer/status_stack.sh
```

Stop the stack:

```bash
./apptainer/stop_stack.sh
```

Default endpoints:

- InfluxDB: `http://localhost:8086`
- Chronograf UI: `http://localhost:8888`
- Kapacitor API: `http://localhost:9092`
- Kafka bootstrap: `localhost:9092`

Kafka is configured in **KRaft** mode in `apptainer/start_stack.sh`, so no ZooKeeper service is required.

---

## 3) Python setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

---

## 4) Ingestion: publish synthetic data to Kafka

```bash
PYTHONPATH=src python -m tsms_tutorial.main ingest --points 2000 --seed 42
```

Telegraf consumes topic `tsms-metrics` and writes metrics into InfluxDB bucket `tutorial`.

---

## 5) Run sample queries on InfluxDB

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

## 6) Example Flux queries for demos

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

## 7) Configuration and persistence notes

- Apptainer data is persisted under `.apptainer-data/` (created automatically by `start_stack.sh`).
- Telegraf and Kapacitor config files are mounted from:
  - `telegraf/telegraf.conf`
  - `kapacitor/kapacitor.conf`
- Python app runtime settings come from `.env`:
  - `INFLUX_*`
  - `KAFKA_*`

---

## Project structure

- `apptainer/start_stack.sh`: start all services as Apptainer instances.
- `apptainer/stop_stack.sh`: stop all running instances.
- `apptainer/status_stack.sh`: print instance status.
- `src/tsms_tutorial/generator.py`: synthetic time-series generator (TimeSynth).
- `src/tsms_tutorial/clients.py`: Kafka publisher + InfluxDB query repository.
- `src/tsms_tutorial/main.py`: CLI for `ingest` and `query`.
- `telegraf/telegraf.conf`: Kafka input and InfluxDB output for Telegraf.
- `kapacitor/kapacitor.conf`: baseline Kapacitor configuration.
