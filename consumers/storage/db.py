from __future__ import annotations

import psycopg2

from common.config import config
from common.models import SensorReading


def get_connection():
    return psycopg2.connect(config.DATABASE_URL)


def ensure_run_exists(conn, run_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO test_runs (run_id)
            VALUES (%s)
            ON CONFLICT (run_id) DO NOTHING;
            """,
            (run_id,),
        )
    conn.commit()


def insert_reading(conn, reading: SensorReading) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sensor_readings (run_id, sensor_id, sensor_type, value, unit, recorded_at)
            VALUES (%s, %s, %s, %s, %s, %s);
            """,
            (
                reading.run_id,
                reading.sensor_id,
                reading.sensor_type,
                reading.value,
                reading.unit,
                reading.recorded_at,
            ),
        )
    conn.commit()
