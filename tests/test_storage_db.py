from unittest.mock import MagicMock

from common.models import SensorReading
from consumers.storage.db import ensure_run_exists, insert_reading


def make_reading():
    return SensorReading(
        run_id="run-1",
        sensor_id="AS-01",
        sensor_type="airspeed",
        value=42.5,
        unit="m/s",
        recorded_at="2026-01-01T00:00:00+00:00",
    )


def test_ensure_run_exists_executes_insert_and_commits():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value

    ensure_run_exists(conn, "run-1")

    cursor.execute.assert_called_once()
    sql_used = cursor.execute.call_args[0][0]
    assert "INSERT INTO test_runs" in sql_used
    assert "ON CONFLICT" in sql_used
    conn.commit.assert_called_once()


def test_insert_reading_executes_insert_with_correct_values():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    reading = make_reading()

    insert_reading(conn, reading)

    cursor.execute.assert_called_once()
    sql_used, params = cursor.execute.call_args[0]
    assert "INSERT INTO sensor_readings" in sql_used
    assert params == (
        reading.run_id,
        reading.sensor_id,
        reading.sensor_type,
        reading.value,
        reading.unit,
        reading.recorded_at,
    )
    conn.commit.assert_called_once()
