# Changelog

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
