from __future__ import annotations

import json

import pandas as pd
from influxdb_client import InfluxDBClient
from kafka import KafkaProducer

from .config import InfluxConfig, KafkaConfig


class KafkaIngestionPublisher:
    def __init__(self, cfg: KafkaConfig):
        self.cfg = cfg
        self.producer = KafkaProducer(
            bootstrap_servers=self.cfg.bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
        )

    def publish(self, df: pd.DataFrame) -> int:
        for row in df.itertuples(index=False):
            message = {
                "time": row.time.isoformat(),
                "sensor_id": row.sensor_id,
                "signal_type": row.signal_type,
                "value": float(row.value),
                "is_injected_anomaly": bool(row.is_injected_anomaly),
            }
            self.producer.send(self.cfg.topic, value=message)
        self.producer.flush()
        return len(df)


class InfluxQueryRepository:
    def __init__(self, cfg: InfluxConfig):
        self.cfg = cfg

    def run_flux(self, flux: str) -> pd.DataFrame:
        with InfluxDBClient(url=self.cfg.url, token=self.cfg.token, org=self.cfg.org) as client:
            tables = client.query_api().query_data_frame(flux)
            if isinstance(tables, list):
                if not tables:
                    return pd.DataFrame()
                return pd.concat(tables, ignore_index=True)
            return tables

    def latest_values(self, limit: int = 10) -> pd.DataFrame:
        flux = f'''
from(bucket: "{self.cfg.bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "metrics" and r._field == "value")
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {limit})
  |> keep(columns: ["_time", "sensor_id", "signal_type", "_value"])
'''
        df = self.run_flux(flux)
        if df.empty:
            return df
        return df.rename(columns={"_time": "time", "_value": "value"})

    def mean_by_window(self, every: str = "15m") -> pd.DataFrame:
        flux = f'''
from(bucket: "{self.cfg.bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "metrics" and r._field == "value")
  |> aggregateWindow(every: {every}, fn: mean, createEmpty: false)
  |> keep(columns: ["_time", "sensor_id", "signal_type", "_value"])
'''
        df = self.run_flux(flux)
        if df.empty:
            return df
        return df.rename(columns={"_time": "time", "_value": "mean_value"})

    def anomalies_only(self, limit: int = 20) -> pd.DataFrame:
        flux = f'''
from(bucket: "{self.cfg.bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "metrics" and r._field == "is_injected_anomaly")
  |> filter(fn: (r) => r._value == true)
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: {limit})
  |> keep(columns: ["_time", "sensor_id", "signal_type", "_value"])
'''
        df = self.run_flux(flux)
        if df.empty:
            return df
        return df.rename(columns={"_time": "time", "_value": "is_injected_anomaly"})
