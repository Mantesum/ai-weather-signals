# Security

Bind API, PostgreSQL and LLM to loopback until an authenticated reverse proxy is configured. Use a dedicated non-superuser database role and strong distinct passwords. Keep `.env`, Telegram sessions, dumps and GGUF files outside Git. Rotate `AUTHOR_HASH_SALT` only with an explicit migration plan because it changes author independence identity.

Untrusted provider text is data, never a prompt instruction: the system prompt limits output, llama.cpp constrains JSON, and Pydantic validates again. URLs are not fetched during evidence serving. Production should add outbound allow-lists, request-body limits, API authentication/rate limiting, dependency scanning and source-specific deletion consumers.

Before release run tests, lint, secret scanning, `git status --ignored`, and inspect `git ls-files`. Never publish real fixtures, `.env`, dumps, logs, sessions or model weights.
