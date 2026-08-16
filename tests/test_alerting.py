from unittest.mock import MagicMock

from common.models import Alert
from consumers.alerting.notifier import format_alert_message
from consumers.alerting.db import insert_alert


def make_alert(severity="critical", reason="out_of_range"):
    return Alert(
        run_id="run-1",
        sensor_id="AS-01",
        sensor_type="airspeed",
        value=999.0,
        reason=reason,
        severity=severity,
        recorded_at="2026-01-01T00:00:00+00:00",
    )


def test_format_alert_message_includes_key_fields():
    alert = make_alert()
    message = format_alert_message(alert)

    assert "AS-01" in message
    assert "airspeed" in message
    assert "999.0" in message
    assert "CRITICAL" in message
    assert alert.run_id in message


def test_format_alert_message_uses_different_icon_for_warning():
    critical_message = format_alert_message(make_alert(severity="critical"))
    warning_message = format_alert_message(make_alert(severity="warning"))
    assert critical_message != warning_message


def test_insert_alert_executes_insert_and_commits():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    alert = make_alert()

    insert_alert(conn, alert)

    cursor.execute.assert_called_once()
    sql_used, params = cursor.execute.call_args[0]
    assert "INSERT INTO alerts" in sql_used
    assert params == (
        alert.run_id,
        alert.sensor_id,
        alert.sensor_type,
        alert.value,
        alert.reason,
        alert.severity,
        alert.recorded_at,
    )
    conn.commit.assert_called_once()
