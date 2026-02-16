from __future__ import annotations

import numpy as np
import pandas as pd
import timesynth as ts


def generate_time_series(n_points: int = 2000, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic time series with trend, seasonality, noise, and anomalies."""
    np.random.seed(seed)

    time_sampler = ts.TimeSampler(stop_time=200)
    timeline = time_sampler.sample_regular_time(num_points=n_points)

    sinusoidal = ts.signals.Sinusoidal(frequency=0.12)
    autoregressive = ts.signals.AutoRegressive(ar_param=[0.7])
    gaussian_noise = ts.noise.GaussianNoise(std=0.15)

    sinusoid_ts = ts.TimeSeries(signal_generator=sinusoidal, noise_generator=gaussian_noise)
    ar_ts = ts.TimeSeries(signal_generator=autoregressive)

    seasonal, _, _ = sinusoid_ts.sample(timeline)
    trend = 0.005 * timeline
    autoreg, _, _ = ar_ts.sample(timeline)

    values = seasonal + trend + 0.2 * autoreg

    anomaly_idx = np.random.choice(np.arange(100, n_points - 100), size=15, replace=False)
    values[anomaly_idx] += np.random.uniform(2.0, 3.5, size=len(anomaly_idx))

    base_time = pd.Timestamp("2025-01-01T00:00:00Z")
    df = pd.DataFrame(
        {
            "time": [base_time + pd.Timedelta(seconds=float(x) * 60) for x in timeline],
            "sensor_id": "sensor-A",
            "signal_type": "synthetic",
            "value": values,
            "is_injected_anomaly": False,
        }
    )
    df.loc[anomaly_idx, "is_injected_anomaly"] = True
    return df
