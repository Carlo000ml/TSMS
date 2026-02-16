from __future__ import annotations

from typing import Iterable

import clickhouse_connect
import pandas as pd
import psycopg2
from influxdb_client import InfluxDBClient, Point

from .config import ClickHouseConfig, InfluxConfig, TimescaleConfig


class InfluxRepository:
    def __init__(self, cfg: InfluxConfig):
        self.cfg = cfg

    def write(self, df: pd.DataFrame) -> None:
        with InfluxDBClient(url=self.cfg.url, token=self.cfg.token, org=self.cfg.org) as client:
            write_api = client.write_api()
            points: Iterable[Point] = (
                Point("metrics")
                .tag("sensor_id", row.sensor_id)
                .tag("signal_type", row.signal_type)
                .field("value", float(row.value))
                .field("is_injected_anomaly", bool(row.is_injected_anomaly))
                .time(row.time)
                for row in df.itertuples()
            )
            write_api.write(bucket=self.cfg.bucket, record=list(points))

    def query_last(self, limit: int = 10) -> pd.DataFrame:
        flux = f'''
from(bucket: "{self.cfg.bucket}")
  |> range(start: -365d)
  |> filter(fn: (r) => r._measurement == "metrics" and r._field == "value")
  |> sort(columns:["_time"], desc: true)
  |> limit(n: {limit})
'''
        with InfluxDBClient(url=self.cfg.url, token=self.cfg.token, org=self.cfg.org) as client:
            tables = client.query_api().query_data_frame(flux)
            if isinstance(tables, list):
                df = pd.concat(tables, ignore_index=True)
            else:
                df = tables
        return df[["_time", "sensor_id", "_value"]].rename(
            columns={"_time": "time", "_value": "value"}
        )


class TimescaleRepository:
    def __init__(self, cfg: TimescaleConfig):
        self.cfg = cfg

    def _conn(self):
        return psycopg2.connect(
            host=self.cfg.host,
            port=self.cfg.port,
            dbname=self.cfg.dbname,
            user=self.cfg.user,
            password=self.cfg.password,
        )

    def write(self, df: pd.DataFrame) -> None:
        rows = list(df[["time", "sensor_id", "value", "signal_type"]].itertuples(index=False, name=None))
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO metrics (time, sensor_id, value, signal_type)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (time, sensor_id) DO UPDATE
                      SET value = EXCLUDED.value,
                          signal_type = EXCLUDED.signal_type
                    """,
                    rows,
                )

    def query_last(self, limit: int = 10) -> pd.DataFrame:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT time, sensor_id, value
                    FROM metrics
                    ORDER BY time DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        return pd.DataFrame(rows, columns=["time", "sensor_id", "value"])


class ClickHouseRepository:
    def __init__(self, cfg: ClickHouseConfig):
        self.cfg = cfg
        self.client = clickhouse_connect.get_client(
            host=cfg.host,
            port=cfg.port,
            username=cfg.username,
            password=cfg.password,
            database=cfg.database,
        )
        self._ensure_table()

    def _ensure_table(self) -> None:
        self.client.command(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                time DateTime64(3, 'UTC'),
                sensor_id String,
                signal_type String,
                value Float64,
                is_injected_anomaly UInt8
            )
            ENGINE = MergeTree
            ORDER BY (sensor_id, time)
            """
        )

    def write(self, df: pd.DataFrame) -> None:
        payload = df[["time", "sensor_id", "signal_type", "value", "is_injected_anomaly"]].copy()
        payload["is_injected_anomaly"] = payload["is_injected_anomaly"].astype(int)
        self.client.insert_df("metrics", payload)

    def query_last(self, limit: int = 10) -> pd.DataFrame:
        query = f"""
        SELECT time, sensor_id, value
        FROM metrics
        ORDER BY time DESC
        LIMIT {limit}
        """
        result = self.client.query_df(query)
        return result
