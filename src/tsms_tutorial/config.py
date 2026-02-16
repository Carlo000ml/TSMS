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
class KafkaConfig:
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic: str = os.getenv("KAFKA_TOPIC", "tsms-metrics")
