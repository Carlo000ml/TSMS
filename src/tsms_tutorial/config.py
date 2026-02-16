from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class InfluxConfig:
    url: str = os.getenv("INFLUX_URL", "http://localhost:8086")
    token: str = os.getenv("INFLUX_TOKEN", "supersecrettoken")
    org: str = os.getenv("INFLUX_ORG", "tsms")
    bucket: str = os.getenv("INFLUX_BUCKET", "tutorial")


@dataclass(frozen=True)
class TimescaleConfig:
    host: str = os.getenv("TIMESCALE_HOST", "localhost")
    port: int = int(os.getenv("TIMESCALE_PORT", "5432"))
    dbname: str = os.getenv("TIMESCALE_DB", "tsms")
    user: str = os.getenv("TIMESCALE_USER", "tsms")
    password: str = os.getenv("TIMESCALE_PASSWORD", "tsms123")


@dataclass(frozen=True)
class ClickHouseConfig:
    host: str = os.getenv("CLICKHOUSE_HOST", "localhost")
    port: int = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    username: str = os.getenv("CLICKHOUSE_USER", "tsms")
    password: str = os.getenv("CLICKHOUSE_PASSWORD", "tsms123")
    database: str = os.getenv("CLICKHOUSE_DB", "tsms")
