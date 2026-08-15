# ADR 0001: MVP boundaries and runtimes

Status: accepted, 2026-08-15.

Use one Python package with synchronous SQLAlchemy, PostgreSQL, a polling worker, FastAPI and local llama.cpp. Avoid Redis/Celery/Kafka/Kubernetes until measured throughput requires them. Use YAML for desired source state and PostgreSQL for cursors/health. Use an isolated GeoNames-compatible catalogue rather than Django imports. Store no profile fields and do not download media. Confirmation requires corroboration or an official report. This minimizes Windows operational load while preserving replaceable adapters and classifiers.

Consequences: polling latency is minutes; Jetstream reconnects each cycle; horizontal scheduling needs a future lease/advisory lock; PostGIS may be needed at larger geographic scale; deletion consumers and authentication are required before broad public deployment.
