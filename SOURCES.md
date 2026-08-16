# Sources and compliance

Operators own the allow-list in `config/sources.yaml`. The repository ships no enabled collection. `weather-signals sources add|enable|disable|list|check` performs small auditable edits; live state remains in PostgreSQL.

## MVP adapters

- Bluesky Jetstream: efficient global JSON stream with collection filters and a resumable microsecond cursor. Keep delete/account events in a future always-on deletion consumer before long retention.
- Mastodon: selected instance + bounded, deduplicated hashtag REST timelines. `options.hashtags` accepts multiple language-specific tags while `options.limit` caps the combined batch. Public preview may be disabled. Respect `X-RateLimit-*` headers and instance policy; a token is an environment variable.
- RSS/Atom: preferred for official agencies and media feeds. Configure only feeds whose terms permit the chosen storage; `store_text: false` keeps hashes and provenance without full text.
- Telegram: optional `telethon` extra and user authorization. Only explicitly named public channels; never broad scraping. Session files live under `data/private` and are ignored.

RSS licenses vary by publisher. Permalinks do not imply republication rights. X/Twitter and Reddit are deliberately absent from the required MVP. Backoff based on HTTP status/rate headers is the next production hardening item.

Only a source definition explicitly tagged `official` may produce an `official_report` signal. Broad social timelines must never carry that tag.

Official references: [Bluesky Jetstream](https://docs.bsky.app/blog/jetstream), [Mastodon timelines](https://docs.joinmastodon.org/methods/timelines/) and [rate limits](https://docs.joinmastodon.org/api/rate-limits/), [Telegram API Terms](https://core.telegram.org/api/terms-of-use) and [application ID](https://core.telegram.org/api/obtaining_api_id). Record source terms, contact, permitted retention and deletion procedure during onboarding.
