from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def build_forecast(df: pd.DataFrame, horizon: int = 30) -> pd.DataFrame:
    ordered = df.sort_values("time")
    series = ordered.set_index("time")["value"]
    model = ExponentialSmoothing(series, trend="add", seasonal=None)
    fit = model.fit(optimized=True)
    forecast = fit.forecast(horizon)
    return forecast.reset_index().rename(columns={0: "forecast"})


def detect_anomalies(df: pd.DataFrame, contamination: float = 0.01) -> pd.DataFrame:
    ordered = df.sort_values("time").copy()
    detector = IsolationForest(contamination=contamination, random_state=42)
    ordered["anomaly_score"] = detector.fit_predict(ordered[["value"]])
    ordered["is_detected_anomaly"] = ordered["anomaly_score"] == -1
    return ordered
