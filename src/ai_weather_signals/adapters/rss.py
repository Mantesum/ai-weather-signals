from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import feedparser

from ..schemas import NormalizedMessage
from .base import PUBLIC_FEED_HEADERS, Adapter, AdapterResult, strip_html


class RSSAdapter(Adapter):
    def fetch(self, cursor: str | None = None) -> AdapterResult:
        response = self.client.get(self.source.target, headers=PUBLIC_FEED_HEADERS)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        messages: list[NormalizedMessage] = []
        newest = cursor
        limit = max(1, min(int(str(self.source.options.get("limit", 100))), 200))
        for entry in feed.entries[:limit]:
            external_id = str(entry.get("id") or entry.get("link") or "")
            if not external_id or external_id == cursor:
                break
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
            messages.append(
                NormalizedMessage(
                    source_name=self.source.name,
                    external_id=external_id,
                    permalink=entry.get("link"),
                    author_external_id=entry.get("author"),
                    text=text,
                    language=self.source.language,
                    published_at=published_at,
                )
            )
            newest = newest or external_id
        return AdapterResult(messages=messages, cursor=newest)
