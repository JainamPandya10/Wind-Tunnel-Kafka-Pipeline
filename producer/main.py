"""
Producer service.

Simulates a wind tunnel test run: continuously emits airspeed, pressure,
and temperature readings to Kafka, occasionally injecting an out-of-range
reading so the anomaly-consumer downstream has something to catch.

Run standalone (outside Docker) with:
    python -m producer.main
"""

from __future__ import annotations

import logging
import time
import uuid

from common.config import config
from common.kafka_utils import make_producer, publish
from producer.simulator import generate_reading, SENSOR_SPECS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [producer] %(message)s")
logger = logging.getLogger(__name__)


def run(run_id: str | None = None):
    run_id = run_id or f"run-{uuid.uuid4().hex[:8]}"
    producer = make_producer()
    interval = 1.0 / config.READINGS_PER_SECOND

    logger.info("Starting test run %s (%.1f readings/sec/sensor, anomaly prob=%.2f)",
                run_id, config.READINGS_PER_SECOND, config.ANOMALY_PROBABILITY)

    try:
        while True:
            for sensor_type in SENSOR_SPECS:
                reading = generate_reading(sensor_type, run_id, config.ANOMALY_PROBABILITY)
                publish(producer, config.TOPIC_READINGS, key=reading.sensor_id, value=reading.to_dict())
                logger.info("Published %s=%.2f%s", reading.sensor_type, reading.value, reading.unit)
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Shutting down producer.")
    finally:
        producer.close()


if __name__ == "__main__":
    run()
