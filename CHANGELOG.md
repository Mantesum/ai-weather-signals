# Changelog

## Unreleased

- Add fresh CGTN China/World RSS, Yahoo News RSS and bounded multilingual Bing News RSS discovery.
- Add China-focused discovery across `weather.com.cn`, Xinhua, China News, People's Daily, CGTN and China Daily.
- Add bounded MSN weather discovery and replace the retired Reuters Environment RSS URL with fresh,
  Reuters-domain-only climate and severe-weather discovery.
- Add fresh direct China News Service and Sixth Tone RSS feeds plus a bounded native adapter for
  CCTV's current China and society JSONP news lists.

## 0.4.0 - 2026-08-20

- Expand bounded Google News RSS discovery from 46 to 97 queries across Southeast Asia, Africa,
  North America, Latin America and the Caribbean, Europe, the Middle East, South Asia, East Asia,
  Central Asia and the Caucasus, and Oceania/Pacific.
- Balance all regional Google News groups on a one-hour interval and remove the former Southeast Asia
  priority/frequency bias.
- Expand fallback geocoding from 88 to 187 worldwide city anchors and add weather vocabulary for
  African, South Asian, East Asian, Middle Eastern, Central Asian and Eastern European languages.
- Add GDELT DOC, NASA EONET and merged RSS/Atom adapters; enable GDACS cyclone/flood, EONET and selected Meteoalarm feeds.
- Add Southeast Asian city anchors and weather terms in Indonesian/Malay, Vietnamese, Thai, Filipino, Burmese, Khmer and Lao.
- Add optional Reddit, X Recent Search and additional RSS sources while keeping credentialed or rate-limited sources disabled by default.
- Strip feed HTML, use explicit public-feed headers and cap large RSS batches.
- Make Ollama context length configurable and select the 4B/4,096-token high-volume profile.
- Clarify and normalize `time_precision` output from small local models; bump the extraction prompt to v2.
- Harden Windows Task Scheduler startup for Ollama, PostgreSQL readiness and process cleanup.
- Replace obsolete state-by-state NWS feeds with the official nationwide active-alert Atom feed and
  disable the retired Reuters environment RSS endpoint.
- Keep GDELT and X disabled until their external access requirements are satisfied.

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
