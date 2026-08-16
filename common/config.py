from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://wt_user:wt_password@localhost:5432/wind_tunnel"
    )

    READINGS_PER_SECOND = float(os.getenv("READINGS_PER_SECOND", 5))
    ANOMALY_PROBABILITY = float(os.getenv("ANOMALY_PROBABILITY", 0.05))

    TOPIC_READINGS = "wind-tunnel.sensor-readings"
    TOPIC_ALERTS = "wind-tunnel.alerts"


config = Config()
