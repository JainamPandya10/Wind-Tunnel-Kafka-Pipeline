"""
Anomaly-detection consumer.

Subscribes to the sensor-readings topic (independently from the storage
consumer -- its own consumer group, so it sees every message too), runs
each reading through AnomalyDetector, and publishes anything flagged to
the alerts topic for the alert-consumer to pick up.

This is the clearest example in the project of Kafka actually decoupling
services: this process doesn't know or care who (if anyone) is listening
to the alerts topic downstream.

Run standalone with:
    python -m consumers.anomaly.main
"""

from __future__ import annotations

import logging

from common.config import config
from common.kafka_utils import make_consumer, make_producer, publish
from common.models import SensorReading
from consumers.anomaly.detector import AnomalyDetector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [anomaly-consumer] %(message)s")
logger = logging.getLogger(__name__)


def run():
    consumer = make_consumer(config.TOPIC_READINGS, group_id="anomaly-consumer-group")
    producer = make_producer()
    detector = AnomalyDetector()

    logger.info("Anomaly consumer listening on '%s'", config.TOPIC_READINGS)

    try:
        for message in consumer:
            reading = SensorReading.from_dict(message.value)
            alert = detector.check(reading)

            if alert is not None:
                publish(producer, config.TOPIC_ALERTS, key=alert.sensor_id, value=alert.to_dict())
                logger.warning(
                    "ALERT [%s/%s] %s=%.2f (run=%s)",
                    alert.severity, alert.reason, alert.sensor_type, alert.value, alert.run_id,
                )
    except KeyboardInterrupt:
        logger.info("Shutting down anomaly consumer.")
    finally:
        producer.close()
        consumer.close()


if __name__ == "__main__":
    run()
