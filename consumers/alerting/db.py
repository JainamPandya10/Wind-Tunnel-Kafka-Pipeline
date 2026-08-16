from __future__ import annotations

import psycopg2

from common.config import config
from common.models import Alert


def get_connection():
    return psycopg2.connect(config.DATABASE_URL)


def insert_alert(conn, alert: Alert) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO alerts (run_id, sensor_id, sensor_type, value, reason, severity, recorded_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            (
                alert.run_id,
                alert.sensor_id,
                alert.sensor_type,
                alert.value,
                alert.reason,
                alert.severity,
                alert.recorded_at,
            ),
        )
    conn.commit()
