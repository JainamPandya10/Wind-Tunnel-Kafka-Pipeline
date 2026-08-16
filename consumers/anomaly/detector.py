from __future__ import annotations

import statistics
from collections import deque
from typing import Optional

from common.models import SensorReading, Alert

# Hard operating limits per sensor type. Anything outside these is an
# immediate 'critical' alert regardless of recent history -- these are
# physical/safety bounds, not statistical ones.
HARD_LIMITS = {
    "airspeed": (-5.0, 160.0),
    "pressure": (60.0, 140.0),
    "temperature": (-15.0, 70.0),
}

ROLLING_WINDOW_SIZE = 20
Z_SCORE_THRESHOLD = 3.0
MIN_SAMPLES_FOR_ZSCORE = 8


class AnomalyDetector:
    """
    Stateful per-sensor-type rolling window, used to catch statistical
    outliers that are still within hard limits but far from recent
    behaviour (e.g. a sudden spike or a sensor that's stuck/drifting).

    Kept as a plain class with no I/O so tests can feed it a sequence of
    readings and assert on exactly which ones raise an alert.
    """

    def __init__(self, window_size: int = ROLLING_WINDOW_SIZE):
        self.window_size = window_size
        self._history: dict[str, deque] = {}

    def _window_for(self, sensor_type: str) -> deque:
        if sensor_type not in self._history:
            self._history[sensor_type] = deque(maxlen=self.window_size)
        return self._history[sensor_type]

    def check(self, reading: SensorReading) -> Optional[Alert]:
        alert = self._check_hard_limits(reading)
        if alert is None:
            alert = self._check_statistical_outlier(reading)

        # Update rolling history regardless of outcome, but only with
        # "sane" values -- an already-flagged spike shouldn't poison the
        # baseline that future statistical checks compare against.
        if alert is None:
            self._window_for(reading.sensor_type).append(reading.value)

        return alert

    def _check_hard_limits(self, reading: SensorReading) -> Optional[Alert]:
        low, high = HARD_LIMITS[reading.sensor_type]
        if reading.value < low or reading.value > high:
            return Alert(
                run_id=reading.run_id,
                sensor_id=reading.sensor_id,
                sensor_type=reading.sensor_type,
                value=reading.value,
                reason="out_of_range",
                severity="critical",
                recorded_at=reading.recorded_at,
            )
        return None

    def _check_statistical_outlier(self, reading: SensorReading) -> Optional[Alert]:
        window = self._window_for(reading.sensor_type)
        if len(window) < MIN_SAMPLES_FOR_ZSCORE:
            return None  # not enough history yet to judge

        mean = statistics.mean(window)
        stdev = statistics.pstdev(window)
        if stdev == 0:
            return None  # no variance to compute a meaningful z-score against

        z_score = abs(reading.value - mean) / stdev
        if z_score >= Z_SCORE_THRESHOLD:
            return Alert(
                run_id=reading.run_id,
                sensor_id=reading.sensor_id,
                sensor_type=reading.sensor_type,
                value=reading.value,
                reason="statistical_outlier",
                severity="warning",
                recorded_at=reading.recorded_at,
            )
        return None
