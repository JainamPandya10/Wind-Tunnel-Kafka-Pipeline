from __future__ import annotations

import json
import time
import logging

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable

from common.config import config

logger = logging.getLogger(__name__)


def make_producer(retries: int = 10, delay_seconds: float = 3.0) -> KafkaProducer:
    """
    Kafka may still be starting up when a dependent service boots (even with
    a Docker healthcheck there's a small race window), so retry the initial
    connection a few times instead of crashing immediately.
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return KafkaProducer(
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
        except NoBrokersAvailable as e:
            last_error = e
            logger.warning("Kafka not ready yet (attempt %d/%d), retrying...", attempt, retries)
            time.sleep(delay_seconds)
    raise ConnectionError(f"Could not connect to Kafka after {retries} attempts") from last_error


def make_consumer(topic: str, group_id: str, retries: int = 10, delay_seconds: float = 3.0) -> KafkaConsumer:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return KafkaConsumer(
                topic,
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
        except NoBrokersAvailable as e:
            last_error = e
            logger.warning("Kafka not ready yet (attempt %d/%d), retrying...", attempt, retries)
            time.sleep(delay_seconds)
    raise ConnectionError(f"Could not connect to Kafka after {retries} attempts") from last_error


def publish(producer: KafkaProducer, topic: str, key: str, value: dict) -> None:
    producer.send(topic, key=key, value=value)
    producer.flush()
