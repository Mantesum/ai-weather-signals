# Privacy

Collect only intentionally public messages from an operator-controlled allow-list. Do not ingest private chats, closed groups, precise private addresses or unnecessary profile data. Author IDs are HMAC-SHA256 values; display names and profiles are not stored. Media is not downloaded. Evidence excerpts are short and may be disabled with `store_text: false`.

Default raw-text retention is 30 days; a scheduled retention implementation and provider deletion/tombstone consumers are required before broad production collection. A deletion request should remove text and attachments, set `deleted_at`, and either remove the signal or keep only sufficiently aggregated non-identifying statistics according to source terms. Document the legal basis, controller contact, retention and source terms for each deployment jurisdiction.
