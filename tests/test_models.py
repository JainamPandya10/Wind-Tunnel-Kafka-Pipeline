from common.models import SensorReading, Alert


def test_sensor_reading_round_trip_through_dict():
    original = SensorReading(
        run_id="run-1",
        sensor_id="AS-01",
        sensor_type="airspeed",
        value=42.5,
        unit="m/s",
        recorded_at="2026-01-01T00:00:00+00:00",
    )
    rebuilt = SensorReading.from_dict(original.to_dict())
    assert rebuilt == original


def test_alert_round_trip_through_dict():
    original = Alert(
        run_id="run-1",
        sensor_id="AS-01",
        sensor_type="airspeed",
        value=999.0,
        reason="out_of_range",
        severity="critical",
        recorded_at="2026-01-01T00:00:00+00:00",
    )
    rebuilt = Alert.from_dict(original.to_dict())
    assert rebuilt == original


def test_sensor_reading_value_is_coerced_to_float():
    # Simulates what happens after JSON deserialization, where numbers
    # might arrive as int if the value happened to be a whole number
    d = {
        "run_id": "run-1",
        "sensor_id": "AS-01",
        "sensor_type": "airspeed",
        "value": 50,   # int, not float
        "unit": "m/s",
        "recorded_at": "2026-01-01T00:00:00+00:00",
    }
    reading = SensorReading.from_dict(d)
    assert isinstance(reading.value, float)
    assert reading.value == 50.0
