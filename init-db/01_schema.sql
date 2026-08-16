-- ============================================================
-- Wind tunnel telemetry schema
-- ============================================================

CREATE TABLE IF NOT EXISTS test_runs (
    run_id          TEXT PRIMARY KEY,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    description     TEXT
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    id              BIGSERIAL PRIMARY KEY,
    run_id          TEXT NOT NULL,
    sensor_id       TEXT NOT NULL,
    sensor_type     TEXT NOT NULL,          -- 'airspeed' | 'pressure' | 'temperature'
    value           DOUBLE PRECISION NOT NULL,
    unit            TEXT NOT NULL,
    recorded_at     TIMESTAMPTZ NOT NULL,
    inserted_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_readings_run_id
    ON sensor_readings (run_id);

CREATE INDEX IF NOT EXISTS idx_readings_sensor_type_time
    ON sensor_readings (sensor_type, recorded_at);

CREATE TABLE IF NOT EXISTS alerts (
    id              BIGSERIAL PRIMARY KEY,
    run_id          TEXT NOT NULL,
    sensor_id       TEXT NOT NULL,
    sensor_type     TEXT NOT NULL,
    value           DOUBLE PRECISION NOT NULL,
    reason          TEXT NOT NULL,           -- e.g. 'out_of_range' | 'statistical_outlier'
    severity        TEXT NOT NULL,           -- 'warning' | 'critical'
    recorded_at     TIMESTAMPTZ NOT NULL,
    inserted_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alerts_run_id
    ON alerts (run_id);
