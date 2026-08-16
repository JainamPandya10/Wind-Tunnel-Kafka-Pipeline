from producer.simulator import (
    generate_normal_reading,
    generate_anomalous_reading,
    generate_reading,
    SENSOR_SPECS,
)


def test_normal_reading_is_within_spec_range():
    for sensor_type, spec in SENSOR_SPECS.items():
        reading = generate_normal_reading(sensor_type, run_id="test-run")
        low, high = spec["normal_range"]
        assert low <= reading.value <= high
        assert reading.sensor_type == sensor_type
        assert reading.unit == spec["unit"]
        assert reading.run_id == "test-run"


def test_anomalous_reading_is_outside_spec_range():
    for sensor_type, spec in SENSOR_SPECS.items():
        reading = generate_anomalous_reading(sensor_type, run_id="test-run")
        low, high = spec["normal_range"]
        assert reading.value < low or reading.value > high


def test_generate_reading_respects_zero_anomaly_probability():
    # With probability 0, every reading generated should land in the normal range
    for sensor_type, spec in SENSOR_SPECS.items():
        low, high = spec["normal_range"]
        for _ in range(50):
            reading = generate_reading(sensor_type, run_id="test-run", anomaly_probability=0.0)
            assert low <= reading.value <= high


def test_generate_reading_respects_full_anomaly_probability():
    # With probability 1, every reading generated should be out of range
    for sensor_type, spec in SENSOR_SPECS.items():
        low, high = spec["normal_range"]
        for _ in range(50):
            reading = generate_reading(sensor_type, run_id="test-run", anomaly_probability=1.0)
            assert reading.value < low or reading.value > high


def test_reading_has_iso_timestamp():
    reading = generate_normal_reading("airspeed", run_id="test-run")
    # Should not raise -- confirms recorded_at is a valid ISO-8601 string
    from datetime import datetime
    datetime.fromisoformat(reading.recorded_at)
