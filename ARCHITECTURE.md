# Architecture

The service is one deployable Python package with two processes: a read-only FastAPI process and a polling worker. PostgreSQL is the durable queue and system of record. This keeps the MVP operable on one Windows PC and leaves clear seams (`Adapter`, `Classifier`, `LocalGeocoder`) for a future queue or separate workers.

Collectors normalize provider payloads into `NormalizedMessage`. A cheap vocabulary/place filter protects the LLM from the full stream. Only candidates reach an interchangeable classifier. The local backend receives a schema-constrained request, and Pydantic validates the response again. Failed stages are retained as retry/audit records. Exact source IDs make ingestion idempotent; normalized text hashes flag cross-source copies.

Aggregation searches a 3-hour/35-km window with the same phenomenon, then recomputes confidence from all linked signals. PostgreSQL latitude/longitude is sufficient for the pilot; PostGIS is a later optimization. No Redis, Celery, Kafka or Kubernetes is required.

Trust boundaries: internet payloads are untrusted; adapters never execute content. API evidence is anonymized and bounded. LLM listens on loopback. PostgreSQL is bound to loopback in Compose. Secrets live outside Git.
