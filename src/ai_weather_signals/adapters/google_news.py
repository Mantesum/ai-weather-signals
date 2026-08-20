import hashlib
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from ..schemas import NormalizedMessage
from .base import PUBLIC_FEED_HEADERS, Adapter, AdapterResult, strip_html


def _published_at(entry: dict[str, object]) -> datetime:
    value = entry.get("published") or entry.get("updated")
    try:
        parsed = parsedate_to_datetime(str(value)) if value else datetime.now(UTC)
    except (TypeError, ValueError, OverflowError):
        parsed = datetime.now(UTC)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


class GoogleNewsAdapter(Adapter):
    """Several bounded Google News RSS searches represented as one source."""

    def fetch(self, cursor: str | None = None) -> AdapterResult:
        configured = self.source.options.get("queries", [])
        queries = configured if isinstance(configured, list) else [str(configured)]
        queries = [str(query).strip() for query in queries if str(query).strip()]
        if not queries:
            raise ValueError("Google News source requires options.queries")

        total_limit = max(1, min(int(str(self.source.options.get("total_limit", 20))), 100))
        per_query_limit = max(1, min(int(str(self.source.options.get("per_query_limit", 10))), 25))
        delay = max(0.0, min(float(str(self.source.options.get("delay_seconds", 0.2))), 2.0))
        params_base = {
            "hl": str(self.source.options.get("hl", "en-US")),
            "gl": str(self.source.options.get("gl", "US")),
            "ceid": str(self.source.options.get("ceid", "US:en")),
        }
        by_id: dict[str, NormalizedMessage] = {}
        successful_requests = 0
        last_error: httpx.HTTPError | None = None
        for index, query in enumerate(queries):
            try:
                response = self.client.get(
                    self.source.target,
                    params={**params_base, "q": query},
                    headers=PUBLIC_FEED_HEADERS,
                )
                response.raise_for_status()
                successful_requests += 1
            except httpx.HTTPError as error:
                last_error = error
                continue
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:per_query_limit]:
                identity = str(entry.get("id") or entry.get("link") or "").strip()
                if not identity:
                    continue
                external_id = hashlib.sha256(identity.encode()).hexdigest()
                text = strip_html(
                    "\n".join(filter(None, [entry.get("title", ""), entry.get("summary", "")]))
                )
                by_id[external_id] = NormalizedMessage(
                    source_name=self.source.name,
                    external_id=external_id,
                    permalink=entry.get("link"),
                    author_external_id=entry.get("source", {}).get("title") or entry.get("author"),
                    text=text,
                    language=self.source.language,
                    published_at=_published_at(entry),
                    raw={"provider": "google_news_rss", "query": query},
                )
            if delay and index < len(queries) - 1:
                time.sleep(delay)

        if successful_requests == 0 and last_error is not None:
            raise last_error
        messages = sorted(by_id.values(), key=lambda item: item.published_at, reverse=True)[:total_limit]
        newest = messages[0].external_id if messages else cursor
        return AdapterResult(messages=messages, cursor=newest)
