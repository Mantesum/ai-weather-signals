# Changelog

## 0.3.0 - 2026-08-16

- Persist accepted and rejected structured LLM decisions for audit.
- Allow `official_report` only for explicitly trusted sources tagged `official`.
- Recalculate active event confidence from one latest signal per independent author.
- Add a read-only classification audit API and decision metrics.
- Bound Ollama input/output, avoid retrying timeouts and keep the model warm.
- Collect and deduplicate multiple multilingual Mastodon hashtags in one bounded batch.
- Add five GeoNames-validated pilot locations and aliases.

## 0.2.0 - 2026-08-16

- Add native Ollama chat support with JSON Schema output and thinking disabled.
- Select `qwen3.5:9b` as the Windows deployment default while retaining the OpenAI-compatible provider.
- Add safe collection time budgets that preserve the cursor for partial runs.
- Enforce `LLM_ENABLED` whenever a live source is enabled.
- Synchronize disabled source state into PostgreSQL.
- Reduce false-positive English prefilter matches by enforcing word boundaries.
- Lower the default bounded Bluesky batch from 200 to 100 messages.

## 0.1.0 - 2026-08-15

- Initial public MVP.
