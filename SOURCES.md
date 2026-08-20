# Sources and compliance

Operators own the allow-list in `config/sources.yaml`. `weather-signals sources add|enable|disable|list|check` performs small auditable edits; live state remains in PostgreSQL.

## MVP adapters

- Bluesky Jetstream: efficient global JSON stream with collection filters and a resumable microsecond cursor. Keep delete/account events in a future always-on deletion consumer before long retention.
- Mastodon: selected instance + bounded, deduplicated hashtag REST timelines. `options.hashtags` accepts multiple language-specific tags while `options.limit` caps the combined batch. Public preview may be disabled. Respect `X-RateLimit-*` headers and instance policy; a token is an environment variable.
- RSS/Atom: preferred for official agencies and media feeds. Configure only feeds whose terms permit the chosen storage; `store_text: false` keeps hashes and provenance without full text.
- Telegram: optional `telethon` extra and user authorization. Only explicitly named public channels; never broad scraping. Session files live under `data/private` and are ignored.
- X: official API v2 Recent Search with App-only Bearer authentication. The adapter combines multilingual weather terms in one bounded query, requests at most `options.max_results` posts, and resumes with `since_id`. Keep the source disabled until `X_BEARER_TOKEN` is configured and a Developer Console spending limit is set; Post reads are pay-per-use.
- Google News RSS: multiple regional and publisher-restricted queries merged into bounded logical sources. The deployment uses 108 queries in 21 groups with equal one-hour intervals. Coverage includes Africa, North America, Latin America and the Caribbean, Europe, the Middle East and North Africa, South Asia, East Asia, Central Asia and the Caucasus, Southeast Asia, and Oceania/Pacific. A China-specific group monitors Chinese weather terms across `weather.com.cn`, Xinhua, China News, People's Daily, CGTN and China Daily. Local-language terms are used alongside English, feed HTML is stripped, and every returned batch is capped. This is a useful discovery layer but not a documented Google API or an official confirmation source.
- GDELT DOC 2.0: optional multilingual news discovery with one bounded request per cycle. The public endpoint currently rate-limits this deployment address, so the source remains disabled until a successful pilot.
- NASA EONET v3: open structured natural-event metadata for severe storms, floods, drought, dust/haze, snow and ice. EONET is tagged official but still passes through temporal and geographic validation.
- GDACS: official cyclone and flood RSS feeds only; the generic earthquake/volcano feed is deliberately excluded from this weather service.
- Meteoalarm: selected maintained country Atom feeds merged into one bounded European warning source. Legacy RSS feeds are not used.
- China media: current CGTN China and World RSS feeds are merged into one bounded source. The technically reachable China Daily and legacy English Xinhua feeds are deliberately excluded because their published entries are stale.
- Additional aggregators: Yahoo News RSS and five bounded Bing News RSS searches provide independent discovery. MSN has no dependable public weather RSS, so its weather reporting is monitored through bounded, domain-restricted discovery.
- NWS: the official nationwide active-alert Atom feed is bounded to 40 items per cycle and treated as a high-trust source. BBC remains a lower-trust discovery source. Reuters retired its old Environment RSS URL; the replacement source uses bounded Reuters-domain-only discovery and is not represented as an official Reuters feed.
- Reddit: optional OAuth search adapter, disabled by default. It must not be enabled without a valid token and a review of current Reddit API terms.

RSS licenses vary by publisher. Permalinks do not imply republication rights. X and Reddit are optional credentialed adapters rather than required sources. Backoff based on HTTP status/rate headers is the next production hardening item.

Only a source definition explicitly tagged `official` may produce an `official_report` signal. Broad social timelines must never carry that tag.

Official references: [Bluesky Jetstream](https://docs.bsky.app/blog/jetstream), [Mastodon timelines](https://docs.joinmastodon.org/methods/timelines/) and [rate limits](https://docs.joinmastodon.org/api/rate-limits/), [NWS API](https://www.weather.gov/documentation/services-web-api), [GDELT DOC](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/), [NASA EONET](https://eonet.gsfc.nasa.gov/docs/v3), [GDACS feeds](https://data.gdacs.org/feed_reference.aspx), [Meteoalarm feeds](https://feeds.meteoalarm.org/), [Telegram API Terms](https://core.telegram.org/api/terms-of-use) and [application ID](https://core.telegram.org/api/obtaining_api_id). Record source terms, contact, permitted retention and deletion procedure during onboarding.
