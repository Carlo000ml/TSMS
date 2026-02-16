from __future__ import annotations

import argparse

from .analytics import build_forecast, detect_anomalies
from .clients import ClickHouseRepository, InfluxRepository, TimescaleRepository
from .config import ClickHouseConfig, InfluxConfig, TimescaleConfig
from .generator import generate_time_series


def cmd_generate_and_store(points: int) -> None:
    df = generate_time_series(n_points=points)

    InfluxRepository(InfluxConfig()).write(df)
    TimescaleRepository(TimescaleConfig()).write(df)
    ClickHouseRepository(ClickHouseConfig()).write(df)

    print(f"Inserted {len(df)} rows into InfluxDB, TimeScaleDB, and ClickHouse")


def cmd_query(limit: int) -> None:
    repos = {
        "InfluxDB": InfluxRepository(InfluxConfig()),
        "TimeScaleDB": TimescaleRepository(TimescaleConfig()),
        "ClickHouse": ClickHouseRepository(ClickHouseConfig()),
    }
    for name, repo in repos.items():
        print(f"\n=== {name} latest {limit} records ===")
        print(repo.query_last(limit=limit).head(limit))


def cmd_analyze(limit: int, horizon: int) -> None:
    source_df = ClickHouseRepository(ClickHouseConfig()).query_last(limit=limit)
    source_df = source_df.sort_values("time")

    forecast_df = build_forecast(source_df, horizon=horizon)
    anomaly_df = detect_anomalies(source_df)

    print("\n=== Forecast (first 10 rows) ===")
    print(forecast_df.head(10))

    anomalies = anomaly_df[anomaly_df["is_detected_anomaly"]]
    print(f"\nDetected anomalies: {len(anomalies)}")
    print(anomalies[["time", "value", "is_detected_anomaly"]].head(10))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TSMS tutorial with TimeSynth + 3 databases")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Generate a time series and write to all 3 databases")
    ingest.add_argument("--points", type=int, default=2000)

    query = sub.add_parser("query", help="Retrieve latest records from all 3 databases")
    query.add_argument("--limit", type=int, default=10)

    analyze = sub.add_parser("analyze", help="Run forecasting and anomaly detection")
    analyze.add_argument("--limit", type=int, default=1000)
    analyze.add_argument("--horizon", type=int, default=30)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "ingest":
        cmd_generate_and_store(points=args.points)
    elif args.command == "query":
        cmd_query(limit=args.limit)
    elif args.command == "analyze":
        cmd_analyze(limit=args.limit, horizon=args.horizon)


if __name__ == "__main__":
    main()
