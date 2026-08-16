from common.models import SensorReading
from consumers.anomaly.detector import AnomalyDetector, MIN_SAMPLES_FOR_ZSCORE


def make_reading(sensor_type="airspeed", value=50.0, run_id="run-1"):
    return SensorReading(
        run_id=run_id,
        sensor_id="AS-01",
        sensor_type=sensor_type,
        value=value,
        unit="m/s",
        recorded_at="2026-01-01T00:00:00+00:00",
    )


def test_value_within_normal_range_raises_no_alert():
    detector = AnomalyDetector()
    reading = make_reading(value=50.0)  # well within airspeed's hard limits
    assert detector.check(reading) is None


def test_value_beyond_hard_limit_raises_critical_alert():
    detector = AnomalyDetector()
    reading = make_reading(sensor_type="airspeed", value=999.0)  # way beyond hard limit of 160
    alert = detector.check(reading)

    assert alert is not None
    assert alert.severity == "critical"
    assert alert.reason == "out_of_range"
    assert alert.sensor_type == "airspeed"


def test_value_below_hard_limit_raises_critical_alert():
    detector = AnomalyDetector()
    reading = make_reading(sensor_type="pressure", value=-50.0)  # below hard limit of 60
    alert = detector.check(reading)

    assert alert is not None
    assert alert.severity == "critical"


def test_statistical_outlier_detected_after_stable_baseline():
    detector = AnomalyDetector()

    # Feed a stable baseline with small realistic jitter (a perfectly
    # constant baseline has zero variance, which would make the z-score
    # undefined -- real sensors always have some noise).
    baseline_values = [49.8, 50.1, 49.9, 50.2, 50.0, 49.7, 50.3, 50.0, 49.9, 50.1]
    for value in baseline_values:
        result = detector.check(make_reading(value=value))
        assert result is None

    # A sudden spike, still within hard limits but far from the baseline mean
    spike = make_reading(value=100.0)
    alert = detector.check(spike)

    assert alert is not None
    assert alert.reason == "statistical_outlier"
    assert alert.severity == "warning"


def test_no_statistical_check_before_minimum_samples():
    detector = AnomalyDetector()
    # Only feed a couple of readings -- not enough history for z-score yet
    detector.check(make_reading(value=10.0))
    result = detector.check(make_reading(value=90.0))  # would be an outlier if history existed
    assert result is None  # hard limits not breached, and not enough samples for stats


def test_sensor_types_have_independent_history():
    detector = AnomalyDetector()
    for _ in range(MIN_SAMPLES_FOR_ZSCORE + 2):
        detector.check(make_reading(sensor_type="airspeed", value=50.0))

    # A pressure reading shouldn't be judged against airspeed's history
    reading = make_reading(sensor_type="pressure", value=100.0)  # normal for pressure
    assert detector.check(reading) is None


def test_flagged_reading_does_not_pollute_rolling_baseline():
    detector = AnomalyDetector()
    baseline_values = [49.8, 50.1, 49.9, 50.2, 50.0, 49.7, 50.3, 50.0, 49.9, 50.1]
    for value in baseline_values:
        detector.check(make_reading(value=value))

    # This spike should get flagged...
    spike_alert = detector.check(make_reading(value=100.0))
    assert spike_alert is not None

    # ...and should NOT have been added to the window, so the next normal
    # reading is still judged against the original stable baseline, not
    # against a window contaminated by the spike.
    result = detector.check(make_reading(value=50.0))
    assert result is None
