# Data model

- `sources`: versioned definition mirrored from YAML plus cursor, last success and error.
- `ingest_runs`: per-cycle counts, duration and outcome.
- `raw_messages`: unique `(source_id, external_id)`, permalink, HMAC author, optional text, text hash and timestamps.
- `attachments`: remote links and non-sensitive media metadata; media is not downloaded.
- `model_versions`: model name, prompt/schema versions and prompt SHA-256.
- `weather_signals`: validated extraction, evidence flags, confidence and copy marker.
- `geocode_results`: stable city ID, optional GeoNames ID, coordinates, method and precision.
- `weather_events` / `event_signals`: aggregate state and auditable many-to-many evidence.
- `processing_errors`: bounded diagnostic, stage, retryability and attempt.

All timestamps are timezone-aware UTC. Deletion handling can null `raw_messages.text`, mark `deleted_at`, remove attachments and retain only non-identifying aggregate statistics. PostgreSQL is the supported runtime store; SQLite exists only for isolated tests.
