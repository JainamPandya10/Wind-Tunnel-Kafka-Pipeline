# Wind Tunnel Telemetry Pipeline (Kafka + Postgres)

A simulated wind tunnel that emits streaming sensor readings (airspeed,
pressure, temperature) over Kafka to three independent microservices — one
persists the data, one detects anomalies, one delivers alerts. Everything
runs as separate processes connected only by Kafka topics, the way a real
event-driven microservice system is structured.

## Why this project

This project describes:

- **One producer, multiple independent consumers on the same stream.**
  The storage consumer and the anomaly consumer both read every message
  from `wind-tunnel.sensor-readings`, in their own consumer groups,
  without knowing about each other. That's the actual point of a message
  broker — services stay decoupled.
- **A second topic downstream of the first.** The anomaly consumer
  publishes to `wind-tunnel.alerts`; the alert consumer only cares about
  that topic and has no idea sensor readings even exist. This is a
  two-hop event pipeline, not just a single publish/subscribe pair.
- **Real business logic, not just message-passing plumbing.** The anomaly
  detector combines hard physical limits with a rolling z-score, which is
  a legitimate (if simple) approach to time-series anomaly detection.

## Architecture

```
                     ┌───────────────┐
                     │   producer     │  simulates airspeed / pressure /
                     │  (simulator)   │  temperature sensors
                     └───────┬────────┘
                             │ publish
                             ▼
              topic: wind-tunnel.sensor-readings
                             │
              ┌──────────────┼──────────────┐
              │  (each in its own consumer group -- both get every message)
              ▼                              ▼
   ┌────────────────────┐         ┌───────────────────────┐
   │  storage-consumer   │         │   anomaly-consumer     │
   │  writes every       │         │  hard-limit check +    │
   │  reading to Postgres│         │  rolling z-score        │
   └──────────────────────┘        └───────────┬─────────────┘
                                                │ publish (only if flagged)
                                                ▼
                                   topic: wind-tunnel.alerts
                                                │
                                                ▼
                                   ┌───────────────────────┐
                                   │   alert-consumer        │
                                   │  logs to console +      │
                                   │  Postgres alerts table  │
                                   └───────────────────────┘
```

## Setup

### 1. Start everything with Docker Compose

```bash
docker compose up --build
```

This starts, in order: Kafka (KRaft mode, no Zookeeper needed), Postgres
(schema auto-applied from `init-db/`), then the producer and all three
consumers. You'll see interleaved logs from all four services — watch for
lines like:

```
wt_producer          | Published airspeed=63.21m/s
wt_storage_consumer   | Stored airspeed=63.21m/s (run=run-a1b2c3d4)
wt_anomaly_consumer   | ALERT [critical/out_of_range] pressure=210.44 (run=run-a1b2c3d4)
wt_alert_consumer     | 🔴 [CRITICAL] pressure sensor PR-02 reported 210.44 ...
```

Stop everything with `docker compose down` (add `-v` to also wipe the
Postgres volume and start clean next time).

### 2. Inspect the data

```bash
docker exec -it wt_postgres psql -U wt_user -d wind_tunnel

wind_tunnel=# SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 10;
wind_tunnel=# SELECT * FROM alerts ORDER BY id DESC LIMIT 10;
wind_tunnel=# SELECT sensor_type, count(*), avg(value) FROM sensor_readings GROUP BY sensor_type;
```

### 3. Run the tests

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest -v
```

The tests need **no running Kafka or Postgres** — every test exercises
pure business logic (the simulator, the anomaly detector, message
formatting) or a mocked database connection. That's a deliberate design
choice: I/O (Kafka, Postgres) is kept in thin wrapper functions
(`common/kafka_utils.py`, `consumers/*/db.py`) so the logic underneath is
fast and easy to test in isolation.

## Project layout

```
wind-tunnel-kafka-pipeline/
├── docker-compose.yml         # Kafka + Postgres + all 4 services
├── Dockerfile.python          # shared image for producer/consumers
├── init-db/01_schema.sql      # test_runs, sensor_readings, alerts tables
├── common/
│   ├── config.py              # env var loading, topic names
│   ├── models.py              # SensorReading / Alert dataclasses
│   └── kafka_utils.py         # producer/consumer wrappers (retry on boot)
├── producer/
│   ├── simulator.py           # pure reading-generation logic
│   └── main.py                # publish loop
├── consumers/
│   ├── storage/
│   │   ├── db.py              # Postgres writes
│   │   └── main.py            # consume loop
│   ├── anomaly/
│   │   ├── detector.py        # hard limits + rolling z-score
│   │   └── main.py            # consume + publish alerts
│   └── alerting/
│       ├── notifier.py        # message formatting
│       ├── db.py               # Postgres writes
│       └── main.py             # consume loop
└── tests/                      # 20 unit tests, no live Kafka/Postgres needed
```

## How the anomaly detection works

Two independent checks, either of which can raise an alert:

1. **Hard physical limits** (`HARD_LIMITS` in `detector.py`) — e.g.
   airspeed outside -5 to 160 m/s is immediately `critical`, regardless of
   recent history. These represent values that would be physically
   implausible or dangerous.
2. **Rolling z-score** — each sensor type keeps its own rolling window
   (last 20 readings). Once there's enough history, a new reading more
   than 3 standard deviations from the recent mean is flagged as a
   `warning`-level statistical outlier — catching drift or sudden spikes
   that are still within hard limits but inconsistent with recent
   behavior.

A reading that gets flagged is **not** added to the rolling window, so a
single spike doesn't drag the baseline toward itself and mask the next
real anomaly.

## What this demonstrates (for CV / interview prep)

- Event-driven architecture: independent microservices connected only by
  Kafka topics, each in its own consumer group
- A two-hop pipeline (readings topic → derived alerts topic), not just a
  single producer/consumer pair
- Docker Compose orchestration of a multi-service system with health
  checks and startup dependencies
- Postgres schema design for time-series-ish data (indexes on
  `sensor_type + recorded_at` for the query patterns that actually matter)
- Testable architecture: I/O isolated from logic, 20 unit tests covering
  simulation, detection, serialization, and persistence — all runnable
  without any live infrastructure
- Defensive engineering: Kafka connection retries on startup to handle the
  container-startup race condition, graceful shutdown on `KeyboardInterrupt`

## Extending this project

- **RabbitMQ variant**: swap Kafka for RabbitMQ to show you understand
  both major message-broker paradigms (Kafka's log/partition model vs.
  RabbitMQ's queue/exchange model) — genuinely useful since the job
  posting mentions both as options.
- **Dead-letter handling**: what happens if `insert_reading` throws (DB
  briefly down)? Right now that exception propagates and the consumer
  dies. A more production-grade version would catch it, retry with
  backoff, and eventually route the message to a dead-letter topic.
- **Windowed aggregation service**: add a 4th consumer that computes
  1-minute rolling averages per sensor and writes them to a separate
  `sensor_aggregates` table — a good excuse to learn Kafka Streams or
  just do it with a Python sliding window like the anomaly detector does.
- **Grafana dashboard**: point Grafana at the Postgres tables for a live
  view of the simulated wind tunnel — good visual payoff for a demo.
