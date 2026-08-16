from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone


@dataclass
class SensorReading:
    run_id: str
    sensor_id: str
    sensor_type: str   # 'airspeed' | 'pressure' | 'temperature'
    value: float
    unit: str
    recorded_at: str   # ISO-8601 string (keeps JSON serialization simple/unambiguous)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "SensorReading":
        return SensorReading(
            run_id=d["run_id"],
            sensor_id=d["sensor_id"],
            sensor_type=d["sensor_type"],
            value=float(d["value"]),
            unit=d["unit"],
            recorded_at=d["recorded_at"],
        )


@dataclass
class Alert:
    run_id: str
    sensor_id: str
    sensor_type: str
    value: float
    reason: str        # 'out_of_range' | 'statistical_outlier'
    severity: str       # 'warning' | 'critical'
    recorded_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Alert":
        return Alert(
            run_id=d["run_id"],
            sensor_id=d["sensor_id"],
            sensor_type=d["sensor_type"],
            value=float(d["value"]),
            reason=d["reason"],
            severity=d["severity"],
            recorded_at=d["recorded_at"],
        )
