CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS metrics (
    time        TIMESTAMPTZ       NOT NULL,
    sensor_id   TEXT              NOT NULL,
    value       DOUBLE PRECISION  NOT NULL,
    signal_type TEXT              NOT NULL,
    PRIMARY KEY (time, sensor_id)
);

SELECT create_hypertable('metrics', by_range('time'), if_not_exists => TRUE);
