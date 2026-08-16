"""
Alert consumer.

Subscribes to the alerts topic (published by the anomaly consumer) and
"delivers" each one -- here that means printing it and logging it to
Postgres, but in a real system this is exactly where you'd plug in
Slack/email/PagerDuty without touching the anomaly-detection code at all.
That swap-ability is the actual point of the message-broker pattern.

Run standalone with:
    python -m consumers.alerting.main
"""

from __future__ import annotations

import logging

from common.config import config
from common.kafka_utils import make_consumer
from common.models import Alert
from consumers.alerting.db import get_connection, insert_alert
from consumers.alerting.notifier import format_alert_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s [alert-consumer] %(message)s")
logger = logging.getLogger(__name__)


def run():
    consumer = make_consumer(config.TOPIC_ALERTS, group_id="alert-consumer-group")
    conn = get_connection()

    logger.info("Alert consumer listening on '%s'", config.TOPIC_ALERTS)

    try:
        for message in consumer:
            alert = Alert.from_dict(message.value)
            logger.info(format_alert_message(alert))
            insert_alert(conn, alert)
    except KeyboardInterrupt:
        logger.info("Shutting down alert consumer.")
    finally:
        conn.close()
        consumer.close()


if __name__ == "__main__":
    run()
