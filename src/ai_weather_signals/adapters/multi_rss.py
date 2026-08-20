import hashlib
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from ..schemas import NormalizedMessage
from .base import PUBLIC_FEED_HEADERS, Adapter, AdapterResult, strip_html


class MultiRSSAdapter(Adapter):
    """Merge a bounded list of related RSS/Atom feeds into one logical source."""

    def fetch(self, cursor: str | None = None) -> AdapterResult:
        configured = self.source.options.get("feeds", [])
        feeds = configured if isinstance(configured, list) else [str(configured)]
        feeds = [str(url).strip() for url in feeds if str(url).strip()]
        if not feeds:
            raise ValueError("Multi-RSS source requires options.feeds")
        total_limit = max(1, min(int(str(self.source.options.get("total_limit", 50))), 200))
        per_feed_limit = max(1, min(int(str(self.source.options.get("per_feed_limit", 20))), 100))
        by_id: dict[str, NormalizedMessage] = {}
        successful_requests = 0
        last_error: httpx.HTTPError | None = None
        for feed_url in feeds:
            try:
                response = self.client.get(feed_url, headers=PUBLIC_FEED_HEADERS)
                response.raise_for_status()
                successful_requests += 1
            except httpx.HTTPError as error:
                last_error = error
                continue
            parsed_feed = feedparser.parse(response.content)
            for entry in parsed_feed.entries[:per_feed_limit]:
                identity = str(entry.get("id") or entry.get("link") or "").strip()
                if not identity:
                    continue
                external_id = hashlib.sha256(f"{feed_url}|{identity}".encode()).hexdigest()
                published = entry.get("published") or entry.get("updated")
                try:
                    published_at = parsedate_to_datetime(published) if published else datetime.now(UTC)
                except (TypeError, ValueError, OverflowError):
                    published_at = datetime.now(UTC)
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=UTC)
                text = strip_html(
                    "\n".join(filter(None, [entry.get("title", ""), entry.get("summary", "")]))
                )
                by_id[external_id] = NormalizedMessage(
                    source_name=self.source.name,
                    external_id=external_id,
                    permalink=entry.get("link"),
                    author_external_id=entry.get("author"),
                    text=text,
                    language=self.source.language,
                    published_at=published_at,
                    raw={"feed_url": feed_url},
                )
        if successful_requests == 0 and last_error is not None:
            raise last_error
        messages = sorted(by_id.values(), key=lambda item: item.published_at, reverse=True)[:total_limit]
        newest = messages[0].external_id if messages else cursor
        return AdapterResult(messages=messages, cursor=newest)
