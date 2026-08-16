from __future__ import annotations

import random
from common.models import SensorReading

# Each sensor's normal operating range, and its unit.
# These are the ranges the simulator samples from during normal operation.
SENSOR_SPECS = {
    "airspeed": {"unit": "m/s", "normal_range": (0.0, 120.0), "sensor_id": "AS-01"},
    "pressure": {"unit": "kPa", "normal_range": (80.0, 120.0), "sensor_id": "PR-02"},
    "temperature": {"unit": "C", "normal_range": (15.0, 45.0), "sensor_id": "TMP-03"},
}


def generate_normal_reading(sensor_type: str, run_id: str) -> SensorReading:
    spec = SENSOR_SPECS[sensor_type]
    low, high = spec["normal_range"]
    value = round(random.uniform(low, high), 2)
    return SensorReading(
        run_id=run_id,
        sensor_id=spec["sensor_id"],
        sensor_type=sensor_type,
        value=value,
        unit=spec["unit"],
        recorded_at=SensorReading.now_iso(),
    )


def generate_anomalous_reading(sensor_type: str, run_id: str) -> SensorReading:
    """Produces a reading well outside the normal range, to simulate a fault/spike."""
    spec = SENSOR_SPECS[sensor_type]
    low, high = spec["normal_range"]
    span = high - low
    # either far below the floor or far above the ceiling
    if random.random() < 0.5:
        value = round(low - random.uniform(0.5, 2.0) * span, 2)
    else:
        value = round(high + random.uniform(0.5, 2.0) * span, 2)
    return SensorReading(
        run_id=run_id,
        sensor_id=spec["sensor_id"],
        sensor_type=sensor_type,
        value=value,
        unit=spec["unit"],
        recorded_at=SensorReading.now_iso(),
    )


def generate_reading(sensor_type: str, run_id: str, anomaly_probability: float) -> SensorReading:
    if random.random() < anomaly_probability:
        return generate_anomalous_reading(sensor_type, run_id)
    return generate_normal_reading(sensor_type, run_id)
