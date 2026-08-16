from __future__ import annotations

from common.models import Alert


def format_alert_message(alert: Alert) -> str:
    """Pure formatting function -- easy to unit test without any I/O."""
    icon = "🔴" if alert.severity == "critical" else "🟡"
    return (
        f"{icon} [{alert.severity.upper()}] {alert.sensor_type} sensor {alert.sensor_id} "
        f"reported {alert.value} ({alert.reason}) during run {alert.run_id} at {alert.recorded_at}"
    )
