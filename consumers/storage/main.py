"""
Storage consumer.

Subscribes to the sensor-readings topic and writes every reading to
Postgres. This is the "aggregates/stores it" consumer -- a completely
independent process from the anomaly detector and alert consumer, even
though all three read the exact same Kafka topic (each in its own
consumer group, so each gets a full copy of the stream).

Run standalone with:
    python -m consumers.storage.main
"""

from __future__ import annotations

import logging

from common.config import config
from common.kafka_utils import make_consumer
from common.models import SensorReading
from consumers.storage.db import get_connection, ensure_run_exists, insert_reading

logging.basicConfig(level=logging.INFO, format="%(asctime)s [storage-consumer] %(message)s")
logger = logging.getLogger(__name__)


def run():
    consumer = make_consumer(config.TOPIC_READINGS, group_id="storage-consumer-group")
    conn = get_connection()
    seen_runs = set()

    logger.info("Storage consumer listening on '%s'", config.TOPIC_READINGS)

    try:
        for message in consumer:
            reading = SensorReading.from_dict(message.value)

            if reading.run_id not in seen_runs:
                ensure_run_exists(conn, reading.run_id)
                seen_runs.add(reading.run_id)

            insert_reading(conn, reading)
            logger.info("Stored %s=%.2f%s (run=%s)", reading.sensor_type, reading.value, reading.unit, reading.run_id)
    except KeyboardInterrupt:
        logger.info("Shutting down storage consumer.")
    finally:
        conn.close()
        consumer.close()


if __name__ == "__main__":
    run()
