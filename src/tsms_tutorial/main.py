from __future__ import annotations

import argparse

from .clients import InfluxQueryRepository, KafkaIngestionPublisher
from .config import InfluxConfig, KafkaConfig
from .generator import generate_time_series


def cmd_ingest(points: int, seed: int) -> None:
    df = generate_time_series(n_points=points, seed=seed)
    published = KafkaIngestionPublisher(KafkaConfig()).publish(df)
    print(f"Published {published} records to Kafka topic '{KafkaConfig().topic}'.")
    print("Telegraf will consume the topic and write points to InfluxDB.")


def cmd_query(example: str, limit: int, window: str) -> None:
    repo = InfluxQueryRepository(InfluxConfig())

    if example == "latest":
        result = repo.latest_values(limit=limit)
    elif example == "mean-window":
        result = repo.mean_by_window(every=window)
    else:
        result = repo.anomalies_only(limit=limit)

    print(f"\n=== Query example: {example} ===")
    if result.empty:
        print("No data returned. Ensure ingestion has completed.")
    else:
        print(result.head(limit))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TSMS step 1: Kafka -> Telegraf -> InfluxDB ingestion and sample queries"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Generate synthetic data and publish it to Kafka")
    ingest.add_argument("--points", type=int, default=2000)
    ingest.add_argument("--seed", type=int, default=42)

    query = sub.add_parser("query", help="Run sample Flux queries on InfluxDB")
    query.add_argument(
        "--example",
        choices=["latest", "mean-window", "anomalies"],
        default="latest",
    )
    query.add_argument("--limit", type=int, default=10)
    query.add_argument("--window", type=str, default="15m")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "ingest":
        cmd_ingest(points=args.points, seed=args.seed)
    elif args.command == "query":
        cmd_query(example=args.example, limit=args.limit, window=args.window)


if __name__ == "__main__":
    main()
